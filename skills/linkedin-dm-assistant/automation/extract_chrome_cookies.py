"""
Extracts LinkedIn session cookies from your existing Chrome browser
and saves them to linkedin_cookies.json for use by Playwright.

Chrome must be closed when running this script.
"""

import json
import os
import shutil
import sqlite3
import base64
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = os.getenv("LINKEDIN_COOKIES_FILE", "./linkedin_cookies.json")


def get_encryption_key():
    import json as _json
    local_state_path = Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data/Local State"
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = _json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # Remove DPAPI prefix
    encrypted_key = encrypted_key[5:]
    import win32crypt
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key


def decrypt_cookie_value(key, encrypted_value):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        # v10 prefix = AES-256-GCM
        if encrypted_value[:3] == b"v10":
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:]
            cipher = AESGCM(key)
            return cipher.decrypt(iv, payload, None).decode("utf-8")
    except Exception:
        pass
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8")
    except Exception:
        return ""


def extract_linkedin_cookies():
    key = get_encryption_key()

    chrome_cookies_path = (
        Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data/Default/Network/Cookies"
    )

    if not chrome_cookies_path.exists():
        # Try without Network subfolder (older Chrome)
        chrome_cookies_path = (
            Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data/Default/Cookies"
        )

    if not chrome_cookies_path.exists():
        raise FileNotFoundError("Chrome cookies database not found. Make sure Chrome is installed.")

    # Copy to temp file so Chrome's lock doesn't block us
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    shutil.copy2(chrome_cookies_path, tmp_path)

    try:
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly, samesite "
            "FROM cookies WHERE host_key LIKE '%linkedin.com%'"
        )
        rows = cursor.fetchall()
        conn.close()
    finally:
        os.unlink(tmp_path)

    playwright_cookies = []
    for host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly, samesite in rows:
        value = decrypt_cookie_value(key, encrypted_value)
        if not value:
            continue

        # Convert Chrome's microsecond timestamp to Unix seconds
        expires = 0
        if expires_utc:
            # Chrome epoch starts Jan 1, 1601; Unix epoch starts Jan 1, 1970
            # Difference is 11644473600 seconds
            expires = (expires_utc / 1_000_000) - 11644473600

        samesite_map = {-1: "None", 0: "None", 1: "Lax", 2: "Strict"}
        samesite_str = samesite_map.get(samesite, "None")

        playwright_cookies.append({
            "name": name,
            "value": value,
            "domain": host_key,
            "path": path,
            "expires": int(expires),
            "httpOnly": bool(is_httponly),
            "secure": bool(is_secure),
            "sameSite": samesite_str,
        })

    return playwright_cookies


if __name__ == "__main__":
    print("Extracting LinkedIn cookies from Chrome...")
    try:
        cookies = extract_linkedin_cookies()
        if not cookies:
            print("No LinkedIn cookies found. Make sure you're logged into LinkedIn in Chrome.")
        else:
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"Saved {len(cookies)} cookies to {COOKIES_FILE}")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Chrome is CLOSED before running this script.")
