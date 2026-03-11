"""
CaptionCraft → Google Drive uploader.
POSTs generated captions to the n8n webhook which saves them to Drive.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Load .env from skill root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = "/webhook/captioncraft-save"
WEBHOOK_URL = N8N_BASE_URL + WEBHOOK_PATH


def upload(title: str, content: str) -> dict:
    """
    Send captions to the n8n webhook.
    Returns the response dict with success, filename, fileId, webViewLink.
    """
    if not N8N_BASE_URL:
        raise ValueError("N8N_BASE_URL not set in .env")

    payload = json.dumps({"title": title, "content": content}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Webhook returned {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach webhook: {e.reason}") from e


if __name__ == "__main__":
    # Usage: python upload_to_drive.py "Video Title" captions.txt
    # Or pipe content: echo "content" | python upload_to_drive.py "Video Title"
    if len(sys.argv) < 2:
        print("Usage: python upload_to_drive.py <title> [captions_file]")
        sys.exit(1)

    title = sys.argv[1]

    if len(sys.argv) >= 3:
        content = Path(sys.argv[2]).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print("Error: provide a captions file or pipe content via stdin.")
        sys.exit(1)

    print(f"Uploading '{title}' to Google Drive...")
    result = upload(title, content)

    # onReceived mode returns {"message": "Workflow was started"} — that's a success
    if result.get("success") or "started" in str(result.get("message", "")).lower():
        filename = result.get("filename", f"{title}_Captions_{__import__('datetime').date.today()}.txt")
        print(f"Uploaded to Google Drive folder successfully.")
        print(f"Filename: {filename}")
        if result.get("webViewLink"):
            print(f"View: {result['webViewLink']}")
    else:
        print(f"Unexpected response: {result}")
