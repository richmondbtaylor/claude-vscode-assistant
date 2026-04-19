"""
Playwright script to send a LinkedIn DM.
Called by server.py when an approval comes in from Slack via n8n.

Usage (direct):
    python send_dm.py --url "https://www.linkedin.com/messaging/thread/XXXXX" --message "Hey Marcus..."
"""

import json
import os
import sys
import argparse
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "linkedin-dm-assistant.env")

COOKIES_FILE = os.getenv("LINKEDIN_COOKIES_FILE", "./linkedin_cookies.json")


def load_cookies(context):
    if not os.path.exists(COOKIES_FILE):
        raise FileNotFoundError(
            f"Cookie file not found: {COOKIES_FILE}\n"
            "Run save_cookies.py first to capture your LinkedIn session."
        )
    with open(COOKIES_FILE) as f:
        cookies = json.load(f)
    context.add_cookies(cookies)


def send_linkedin_dm(conversation_url: str, message: str) -> dict:
    """
    Navigate to a LinkedIn conversation and send a message.
    Returns {"success": True} or {"success": False, "error": "..."}
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        try:
            load_cookies(context)
            page = context.new_page()

            # Navigate to the conversation
            print(f"Navigating to: {conversation_url}")
            page.goto(conversation_url, wait_until="domcontentloaded", timeout=30000)

            # Check we're still logged in
            if "linkedin.com/login" in page.url or "linkedin.com/uas/login" in page.url:
                return {
                    "success": False,
                    "error": "Session expired. Run save_cookies.py again to refresh your LinkedIn session.",
                }

            # Wait for the message input to appear
            # LinkedIn's message composer is a contenteditable div
            msg_input_selector = "div.msg-form__contenteditable"
            try:
                page.wait_for_selector(msg_input_selector, timeout=15000)
            except PlaywrightTimeoutError:
                # Try alternate selector for newer LinkedIn UI
                msg_input_selector = "[data-placeholder='Write a message…']"
                page.wait_for_selector(msg_input_selector, timeout=10000)

            msg_input = page.locator(msg_input_selector).first

            # Click to focus and type
            msg_input.click()
            time.sleep(0.5)

            # Type the message (use fill for reliability, then keyboard for newlines)
            msg_input.fill(message)
            time.sleep(0.3)

            # Send with Enter — LinkedIn uses Enter to send (Shift+Enter for newline)
            send_button_selector = "button.msg-form__send-button"
            try:
                send_btn = page.locator(send_button_selector).first
                send_btn.wait_for(state="visible", timeout=5000)
                send_btn.click()
            except Exception:
                # Fallback: press Enter
                msg_input.press("Enter")

            time.sleep(1)  # Brief pause to let the send register

            print("Message sent successfully.")
            return {"success": True}

        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except PlaywrightTimeoutError as e:
            return {"success": False, "error": f"Timeout waiting for LinkedIn UI: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a LinkedIn DM via Playwright")
    parser.add_argument("--url", required=True, help="LinkedIn conversation URL")
    parser.add_argument("--message", required=True, help="Message to send")
    args = parser.parse_args()

    result = send_linkedin_dm(args.url, args.message)
    if result["success"]:
        print("Done.")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
