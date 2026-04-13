#!/usr/bin/env python3
"""
LinkedIn Comment Bot — First-time setup wizard.
Run this once before starting main.py.
"""

import os
import sys
import time
from pathlib import Path

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "linkedin_profile")


def write_env(**kwargs):
    """Write or update key=value pairs in .env."""
    existing = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
    existing.update({k: v for k, v in kwargs.items() if v})
    with open(ENV_FILE, "w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    print(f".env saved to {ENV_FILE}")


def configure():
    print("\n=== LinkedIn Comment Bot — Setup ===\n")

    profile_url = input(
        "Your LinkedIn profile URL\n"
        "(e.g. https://www.linkedin.com/in/richmond-taylor/): "
    ).strip()
    if not profile_url:
        profile_url = "https://www.linkedin.com/in/richmond-taylor/"

    my_name = input(
        "\nYour first name (used to skip your own comments, e.g. Rich): "
    ).strip()
    if not my_name:
        my_name = "Richmond"

    api_key = input(
        "\nAnthropic API key (leave blank to use claude CLI instead): "
    ).strip()

    sheet_id = input(
        "\nGoogle Sheet ID for logging (leave blank to skip Sheets): "
    ).strip()

    write_env(
        LINKEDIN_PROFILE_URL=profile_url,
        MY_NAME=my_name,
        ANTHROPIC_API_KEY=api_key,
        GOOGLE_SHEET_ID=sheet_id,
        GOOGLE_OAUTH_CREDENTIALS="./credentials.json",
        MAX_POSTS_TO_CHECK="5",
        MAX_REPLIES_PER_RUN="10",
    )


def login_linkedin():
    print("\n=== LinkedIn Login ===")
    print("Opening browser. Log in to LinkedIn, then wait for confirmation.\n")

    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE_DIR, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")

        print("Waiting for login (up to 3 minutes)...")
        for _ in range(36):
            time.sleep(5)
            url = page.url
            if "feed" in url or "mynetwork" in url:
                print("Logged in! Session saved to linkedin_profile/")
                context.close()
                return

        print("Timeout — if you completed login, the session may still be saved.")
        context.close()


def main():
    configure()

    do_login = input("\nOpen browser to log in to LinkedIn now? (y/n): ").strip().lower()
    if do_login == "y":
        login_linkedin()

    print("\n=== Setup complete ===")
    print("Start the bot:  python main.py")
    print("Test one run:   python main.py --now")


if __name__ == "__main__":
    main()
