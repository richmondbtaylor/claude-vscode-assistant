"""Search full page HTML for activity IDs and post content"""
import os, time, re
from playwright.sync_api import sync_playwright

user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_profile')

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=['--start-maximized'],
        viewport={'width': 1920, 'height': 1080},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
    time.sleep(10)
    page.evaluate('window.scrollBy(0, 1000)')
    time.sleep(5)
    page.evaluate('window.scrollBy(0, 1000)')
    time.sleep(3)

    # Get the full page HTML
    html = page.content()
    print(f"Total HTML length: {len(html)}")

    # Find all unique activity IDs
    activity_ids = list(dict.fromkeys(re.findall(r'urn:li:activity:(\d+)', html)))
    print(f"\nUnique activity IDs found: {len(activity_ids)}")
    for aid in activity_ids[:20]:
        print(f"  {aid} -> https://www.linkedin.com/feed/update/urn:li:activity:{aid}/")

    # Also check for ugcPost URNs
    ugc_ids = list(dict.fromkeys(re.findall(r'urn:li:ugcPost:(\d+)', html)))
    print(f"\nUnique ugcPost IDs found: {len(ugc_ids)}")
    for uid in ugc_ids[:10]:
        print(f"  {uid}")

    # Check for share URNs
    share_ids = list(dict.fromkeys(re.findall(r'urn:li:share:(\d+)', html)))
    print(f"\nUnique share IDs found: {len(share_ids)}")
    for sid in share_ids[:10]:
        print(f"  {sid}")

    # Look for the context around first activity ID
    if activity_ids:
        first_id = activity_ids[0]
        idx = html.find(f'urn:li:activity:{first_id}')
        if idx >= 0:
            snippet = html[max(0, idx-100):idx+200]
            print(f"\nContext around first ID ({first_id}):")
            print(f"  {repr(snippet)}")

    # Try to get global JS data
    try:
        js_data = page.evaluate('''() => {
            const keys = Object.keys(window).filter(k =>
                k.includes('data') || k.includes('Data') || k.includes('state') || k.includes('State') || k.includes('cache') || k.includes('Cache')
            );
            return {
                keys: keys.slice(0, 20),
                hasLinkedInData: typeof window.lintrk !== 'undefined',
            };
        }''')
        print(f"\nGlobal JS data keys: {js_data['keys']}")
    except Exception as e:
        print(f"JS data error: {e}")

    context.close()
