"""Debug script to understand what messages look like in LinkedIn DM threads."""
import json, os, time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
COOKIES_FILE = os.getenv("LINKEDIN_COOKIES_FILE", "./linkedin_cookies.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    with open(COOKIES_FILE) as f:
        context.add_cookies(json.load(f))
    page = context.new_page()
    page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector(".msg-conversation-listitem__link", timeout=15000)
    time.sleep(2)

    items = page.query_selector_all(".msg-conversation-listitem__link")
    print(f"Total conversation items: {len(items)}")

    for i, item in enumerate(items[:5]):
        name_el = item.query_selector(".msg-conversation-listitem__participant-names")
        name = name_el.inner_text().strip() if name_el else "Unknown"

        # Get time element
        time_el = item.query_selector("time")
        time_text = ""
        time_dt = ""
        if time_el:
            time_text = time_el.inner_text()
            time_dt = time_el.get_attribute("datetime") or ""

        item.click()
        time.sleep(1.5)

        # Inspect message elements
        msg_bodies = page.query_selector_all(".msg-s-event-listitem__body")
        outgoing_groups = page.query_selector_all(".msg-s-message-group--outgoing")
        all_groups = page.query_selector_all(".msg-s-message-group")

        print(f"\n--- Conv {i}: {name} | time_text={repr(time_text)} | datetime={repr(time_dt)} ---")
        print(f"  msg-bodies: {len(msg_bodies)}, all-groups: {len(all_groups)}, outgoing-groups: {len(outgoing_groups)}")

        if msg_bodies:
            last = msg_bodies[-1]
            text = last.inner_text().strip()[:100]
            is_out = last.evaluate("el => el.closest('.msg-s-message-group--outgoing') !== null")
            print(f"  Last msg text: {repr(text)}")
            print(f"  is_outgoing: {is_out}")

        # Check for unread badge
        unread = item.query_selector(".notification-badge")
        print(f"  unread badge: {unread is not None}")

    browser.close()
