"""Intercept LinkedIn feed API responses to find activity IDs"""
import os, time, re
from playwright.sync_api import sync_playwright

user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_profile')

captured = []

def handle_response(response):
    url = response.url
    # Only look at LinkedIn's own API calls
    if 'linkedin.com' not in url:
        return
    # Skip static assets
    if any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.woff', '.svg', '.ico']):
        return
    try:
        body = response.body()
        text = body.decode('utf-8', errors='ignore')
        activity_ids = re.findall(r'urn:li:activity:(\d{15,})', text)
        if activity_ids:
            captured.append({
                'url': url[:120],
                'size': len(body),
                'activity_ids': list(dict.fromkeys(activity_ids))[:10],
                'snippet': text[text.find('urn:li:activity:'):text.find('urn:li:activity:')+100] if 'urn:li:activity:' in text else ''
            })
            print(f"[API] {url[:80]} -> {len(activity_ids)} activity IDs", flush=True)
    except Exception as e:
        pass

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=['--start-maximized'],
        viewport={'width': 1920, 'height': 1080},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.on('response', handle_response)

    print("Loading feed...", flush=True)
    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
    time.sleep(12)
    print("Scrolling...", flush=True)
    for i in range(5):
        page.evaluate('window.scrollBy(0, window.innerHeight * 0.8)')
        time.sleep(3)
        print(f"  Scroll {i+1} done", flush=True)

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total API responses with activity IDs: {len(captured)}")
    all_ids = []
    for r in captured:
        print(f"\n  URL: {r['url']}")
        print(f"  Size: {r['size']} bytes")
        print(f"  Activity IDs: {r['activity_ids']}")
        all_ids.extend(r['activity_ids'])

    unique_ids = list(dict.fromkeys(all_ids))
    print(f"\n=== ALL UNIQUE ACTIVITY IDs ({len(unique_ids)}) ===")
    for aid in unique_ids:
        print(f"  https://www.linkedin.com/feed/update/urn:li:activity:{aid}/")

    context.close()
