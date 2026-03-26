"""
Receipt filer for Claude Code.
Usage: python file_receipt.py <image_path> <date> <vendor> <amount> <tab> [payment_method] [notes]

Called by Claude after reading a receipt image. Claude extracts the data,
then calls this script to upload to Drive and log to Sheets.
"""
import sys
import os
import mimetypes
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
DRIVE_ROOT_FOLDER = "Bishop AI finances"
CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)
TOKEN_PATH = os.path.expanduser(r"~\.config\gspread\authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

def get_credentials():
    """Load OAuth credentials, refreshing if needed."""
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def find_or_create_folder(drive_service, name, parent_id=None):
    """Find a folder by name (optionally under a parent), or create it."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    # Create it
    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = drive_service.files().create(body=metadata, fields="id").execute()
    return folder["id"]

def upload_file(drive_service, file_path, file_name, folder_id):
    """Upload a file to a specific Drive folder."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    uploaded = drive_service.files().create(
        body=metadata, media_body=media, fields="id, webViewLink"
    ).execute()
    return uploaded.get("webViewLink", "")

def infer_tab(vendor, tab_hint=None):
    if tab_hint and tab_hint in ["Bishop AI", "Prompt Anything", "Personal"]:
        return tab_hint
    vendor_lower = vendor.lower()
    personal_keywords = ["grocery", "kroger", "walmart", "target", "costco", "clothing",
                         "hair", "salon", "gym", "fitness", "pharmacy", "cvs", "walgreens"]
    prompt_keywords = ["prompt anything", "promptanything"]
    for kw in prompt_keywords:
        if kw in vendor_lower:
            return "Prompt Anything"
    for kw in personal_keywords:
        if kw in vendor_lower:
            return "Personal"
    return "Bishop AI"

def main():
    if len(sys.argv) < 6:
        print("Usage: python file_receipt.py <image_path> <date> <vendor> <amount> <tab> [payment_method] [notes]")
        sys.exit(1)

    image_path  = sys.argv[1]
    date        = sys.argv[2]   # YYYY-MM-DD
    vendor      = sys.argv[3]
    amount      = sys.argv[4]   # numeric, no $
    tab         = sys.argv[5]   # Bishop AI / Prompt Anything / Personal
    payment     = sys.argv[6] if len(sys.argv) > 6 else "Unknown"
    notes       = sys.argv[7] if len(sys.argv) > 7 else ""

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    # Build filename
    ext = os.path.splitext(image_path)[1]
    safe_vendor = vendor.replace(" ", "_")
    file_name = f"{safe_vendor}_{amount}{ext}"

    print(f"Filing receipt: {file_name} → {tab} tab")

    # Auth
    creds = get_credentials()
    drive_service = build("drive", "v3", credentials=creds)
    gc = gspread.oauth(credentials_filename=CREDS_PATH)

    # Find Bishop AI finances root folder
    root_id = find_or_create_folder(drive_service, DRIVE_ROOT_FOLDER)
    print(f"Root folder: {DRIVE_ROOT_FOLDER} (id: {root_id})")

    # Find/create date subfolder
    date_folder_id = find_or_create_folder(drive_service, date, parent_id=root_id)
    print(f"Date folder: {date}")

    # Upload file
    drive_link = upload_file(drive_service, image_path, file_name, date_folder_id)
    print(f"Uploaded: {file_name}")
    print(f"Drive link: {drive_link}")

    # Log to sheet
    spreadsheet = gc.open_by_key(SHEET_ID)
    ws = spreadsheet.worksheet(tab)
    ws.append_row([date, vendor, amount, "", payment, drive_link, notes])

    # Infer and fill category (column D = index 4, 1-based)
    from fill_categories import infer_category
    category = infer_category(vendor)
    last_row = len(ws.get_all_values())
    ws.update_cell(last_row, 4, category)

    print(f"Logged to sheet: {tab} tab, row {last_row}")
    print(f"Category: {category}")
    print(f"\n✓ Done!")
    print(f"  File: {file_name}")
    print(f"  Folder: {DRIVE_ROOT_FOLDER} / {date}")
    print(f"  Tab: {tab}")
    print(f"  Category: {category}")
    print(f"  Drive: {drive_link}")

if __name__ == "__main__":
    main()
