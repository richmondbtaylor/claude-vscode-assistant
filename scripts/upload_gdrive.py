"""
Upload a file to Google Drive.
Usage: python upload_gdrive.py <local_file_path> [folder_id]

If folder_id is omitted, uploads to the default Bishop AI Drive folder.
"""
import sys
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

CREDENTIALS_PATH = Path("C:/Users/richm/bishop-research-agent/client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json")
TOKEN_PATH = Path(__file__).parent / "gdrive_token.pickle"

# Default destination folder ID — Bishop AI Drive
DEFAULT_FOLDER_ID = "1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ"


def get_service():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return build("drive", "v3", credentials=creds)


def upload_file(local_path, folder_id=None):
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"ERROR: File not found: {local_path}")
        sys.exit(1)

    folder_id = folder_id or DEFAULT_FOLDER_ID

    MIME_TYPES = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska", ".webm": "video/webm",
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    # Convert .pptx to Google Slides on upload
    CONVERT_TO_GOOGLE = {
        ".pptx": "application/vnd.google-apps.presentation",
    }
    mime_type = MIME_TYPES.get(local_path.suffix.lower(), "application/octet-stream")
    google_mime = CONVERT_TO_GOOGLE.get(local_path.suffix.lower())

    service = get_service()
    file_meta = {"name": local_path.stem, "parents": [folder_id]}
    if google_mime:
        file_meta["mimeType"] = google_mime
    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

    result = service.files().create(body=file_meta, media_body=media, fields="id, webViewLink").execute()
    print(f"Uploaded to Google Drive: {result.get('webViewLink')}")
    return result.get("webViewLink")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_gdrive.py <file_path> [folder_id]")
        sys.exit(1)
    folder = sys.argv[2] if len(sys.argv) > 2 else None
    upload_file(sys.argv[1], folder)
