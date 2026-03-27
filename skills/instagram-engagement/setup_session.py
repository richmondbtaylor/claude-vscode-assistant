"""
setup_session.py — One-time manual login to save Instagram session cookies.

Run this once per account. It opens a real (visible) browser window, lets you
log in normally, then saves the session so the headless bot can reuse it.

Usage:
    venv/Scripts/python setup_session.py --account main_account
"""

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
from config import get_credentials

SESSION_DIR = Path(__file__).parent / ".browser_sessions"
SESSION_DIR.mkdir(exist_ok=True)
IG_BASE = "https://www.instagram.com"


def setup_session(account_name: str):
    creds = get_credentials(account_name)
    session_file = SESSION_DIR / f"{account_name}_session.json"

    print(f"\nSetting up session for account: {account_name}")
    print(f"Username: {creds['username']}")
    print("-" * 50)
    print("A browser window will open. Log in to Instagram normally.")
    print("Complete any 2FA or verification prompts.")
    print("Once you see your Instagram feed, come back here and press Enter.")
    print("-" * 50)
    input("Press Enter to open the browser...")

    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        args=["--start-maximized"],
    )
    context = browser.new_context(
        viewport=None,  # use maximized window size
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()
    page.goto(f"{IG_BASE}/accounts/login/", wait_until="domcontentloaded")

    print("\nBrowser opened. Please log in to Instagram now.")
    print("When you're on your Instagram home feed, press Enter here to save the session.")
    input()

    # Save cookies and storage state
    context.storage_state(path=str(session_file))
    print(f"\nSession saved to: {session_file}")
    print("You can now run the bot in headless mode.")

    browser.close()
    pw.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up Instagram session cookies")
    parser.add_argument("--account", required=True, help="Account key (e.g. main_account)")
    args = parser.parse_args()
    setup_session(args.account)
