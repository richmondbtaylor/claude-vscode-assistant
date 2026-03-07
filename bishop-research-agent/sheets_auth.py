"""
sheets_auth.py — Google Sheets authentication helper.

Usage in notifier.py (replace the existing gspread.oauth() call):

    from sheets_auth import get_sheets_client
    client = get_sheets_client()
    sheet = client.open_by_key(SHEET_ID).worksheet("Leads")

Behavior:
  - In GitHub Actions (GOOGLE_SERVICE_ACCOUNT_JSON env var is set):
      Uses service account auth — no browser, no token file.
  - Locally (env var absent):
      Falls back to gspread OAuth (browser flow), reading credentials from
      ~/.config/gspread/credentials.json as before. No changes to local setup needed.
"""

import json
import os

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_sheets_client() -> gspread.Client:
    """
    Return an authenticated gspread Client.

    Raises:
        ValueError: If GOOGLE_SERVICE_ACCOUNT_JSON is set but is not valid JSON.
        RuntimeError: If the service account JSON is missing required fields.
    """
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if sa_json:
        return _service_account_client(sa_json)

    # Local dev: interactive OAuth via ~/.config/gspread/credentials.json
    return gspread.oauth(scopes=SCOPES)


def _service_account_client(sa_json: str) -> gspread.Client:
    try:
        sa_info = json.loads(sa_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is set but is not valid JSON. "
            "The GitHub Secret must contain the raw JSON content of the service "
            "account key file — do not base64-encode it."
        ) from exc

    required = {"type", "project_id", "private_key", "client_email"}
    missing = required - sa_info.keys()
    if missing:
        raise RuntimeError(
            f"Service account JSON is missing required fields: {missing}. "
            "Download a fresh key from Google Cloud Console > IAM & Admin > Service Accounts."
        )

    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)
