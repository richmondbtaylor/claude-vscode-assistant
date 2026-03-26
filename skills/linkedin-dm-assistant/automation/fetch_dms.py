"""
Fetches LinkedIn DM threads that need a reply.
Finds conversations where:
  - The last message was NOT sent by you
  - The last message is less than 24 hours old

Returns a list of dicts with sender name, thread URL, and messages.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = os.getenv("LINKEDIN_COOKIES_FILE", "./linkedin_cookies.json")


def load_cookies(context):
    if not os.path.exists(COOKIES_FILE):
        raise FileNotFoundError(f"Cookie file not found: {COOKIES_FILE}. Run save_cookies.py first.")
    with open(COOKIES_FILE) as f:
        cookies = json.load(f)
    context.add_cookies(cookies)


def parse_linkedin_time(time_str: str) -> datetime | None:
    """
    LinkedIn shows times like: '2h', '45m', 'Just now', '1:34 PM', 'Yesterday', 'Mon', etc.
    Returns a datetime or None if we can't parse it.
    """
    import re
    now = datetime.now()
    time_str = time_str.strip().lower()

    if not time_str or time_str in ("just now", "now"):
        return now

    if time_str.endswith("m"):
        try:
            mins = int(time_str[:-1])
            return now - timedelta(minutes=mins)
        except ValueError:
            pass

    if time_str.endswith("h"):
        try:
            hours = int(time_str[:-1])
            return now - timedelta(hours=hours)
        except ValueError:
            pass

    if time_str == "yesterday":
        return now - timedelta(hours=25)

    # Handle "1:34 pm" or "11:30 am" — clock time means it's from today
    if re.match(r"^\d{1,2}:\d{2}\s*(am|pm)$", time_str):
        return now - timedelta(minutes=30)  # Treat as recent (within 24h)

    # Day names (Mon, Tue, etc.) or date strings = older than 1 day
    return now - timedelta(hours=48)


def fetch_pending_dms() -> list[dict]:
    """
    Returns a list of DM threads that need a reply, each with:
      - sender_name
      - thread_url
      - messages: list of {sender, text, is_me}
      - last_message_time
    """
    results = []

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

            print("Navigating to LinkedIn messaging...")
            page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=30000)

            if "linkedin.com/login" in page.url or "linkedin.com/uas/login" in page.url:
                print("ERROR: Session expired. Run save_cookies.py again.")
                return []

            # Wait for conversation list
            try:
                page.wait_for_selector(".msg-conversation-listitem__link", timeout=15000)
            except PlaywrightTimeoutError:
                print("Could not find conversation list. LinkedIn UI may have changed.")
                return []

            time.sleep(2)  # Let conversations fully render

            # Get all conversation items
            conv_items = page.query_selector_all(".msg-conversation-listitem__link")
            print(f"Found {len(conv_items)} conversations")

            cutoff = datetime.now() - timedelta(hours=24)

            for item in conv_items:
                try:
                    # Get time of last message
                    time_el = item.query_selector("time")
                    time_str = time_el.get_attribute("datetime") or time_el.inner_text() if time_el else ""

                    # Try datetime attribute first (ISO format)
                    msg_time = None
                    if time_el:
                        dt_attr = time_el.get_attribute("datetime")
                        if dt_attr:
                            try:
                                msg_time = datetime.fromisoformat(dt_attr.replace("Z", "+00:00")).replace(tzinfo=None)
                            except Exception:
                                pass
                        if not msg_time:
                            msg_time = parse_linkedin_time(time_el.inner_text())

                    if msg_time and msg_time < cutoff:
                        continue  # Too old

                    # Get sender name
                    name_el = item.query_selector(".msg-conversation-listitem__participant-names")
                    sender_name = name_el.inner_text().strip() if name_el else "Unknown"

                    # Quick pre-check: if snippet starts with "You:" the last message is mine
                    snippet_el = item.query_selector(".msg-conversation-listitem__message-snippet")
                    snippet = snippet_el.inner_text().strip() if snippet_el else ""
                    if snippet.lower().startswith("you:"):
                        print(f"  Skipping {sender_name} — last message is mine")
                        continue

                    # Get the thread URL
                    href = item.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://www.linkedin.com" + href

                    print(f"Checking: {sender_name} ({time_str})")

                    # Click into the conversation to read it
                    item.click()
                    time.sleep(1.5)

                    # Get current URL (thread URL)
                    thread_url = page.url

                    # Wait for messages to load
                    try:
                        page.wait_for_selector(".msg-s-message-list", timeout=8000)
                    except PlaywrightTimeoutError:
                        continue

                    # Get all messages in the thread
                    msg_els = page.query_selector_all(".msg-s-event-listitem__body")
                    messages = []
                    for msg_el in msg_els:
                        # Outgoing messages live inside a list item with --outgoing modifier
                        is_me = msg_el.evaluate(
                            "el => el.closest('[class*=\"--outgoing\"]') !== null"
                        )
                        text = msg_el.inner_text().strip()
                        if text:
                            messages.append({"is_me": is_me, "text": text})

                    if not messages:
                        continue

                    # Check if the last message was sent by me — if so, skip
                    last_msg = messages[-1]
                    if last_msg["is_me"]:
                        print(f"  -> Last message is mine, skipping")
                        continue

                    print(f"  -> Needs reply!")

                    results.append({
                        "sender_name": sender_name,
                        "thread_url": thread_url,
                        "messages": messages,
                        "last_message_time": msg_time.isoformat() if msg_time else "",
                    })

                except Exception as e:
                    print(f"  Error processing conversation: {e}")
                    continue

        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            browser.close()

    return results


if __name__ == "__main__":
    threads = fetch_pending_dms()
    print(f"\n{'='*50}")
    print(f"Found {len(threads)} threads needing a reply:")
    for t in threads:
        print(f"\n  Sender: {t['sender_name']}")
        print(f"  URL: {t['thread_url']}")
        print(f"  Messages: {len(t['messages'])}")
        print(f"  Last message: {t['messages'][-1]['text'][:80]}...")
    print(json.dumps(threads, indent=2))
