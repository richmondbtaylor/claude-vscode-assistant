"""
Run this once to save your LinkedIn session cookies.
It opens a real browser window — log in manually, then press Enter.

Usage:
    python save_cookies.py
"""

import json
import os
from playwright.sync_api import sync_playwright
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "linkedin-dm-assistant.env")

COOKIES_FILE = os.getenv("LINKEDIN_COOKIES_FILE", "./linkedin_cookies.json")


def save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Opening LinkedIn...")
        page.goto("https://www.linkedin.com/login")

        print("\n>>> Log in to LinkedIn in the browser window that just opened.")
        print(">>> Once you're fully logged in and see your feed, come back here and press Enter.\n")
        input("Press Enter when logged in...")

        cookies = context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"\nCookies saved to {COOKIES_FILE}")
        print("You won't need to do this again unless your session expires.")

        browser.close()


if __name__ == "__main__":
    save_cookies()
