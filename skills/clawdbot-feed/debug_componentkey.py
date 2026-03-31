"""Find all componentkey patterns in LinkedIn feed"""
import os, time
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
    page.evaluate('window.scrollBy(0, 600)')
    time.sleep(4)

    result = page.evaluate('''() => {
        const out = {};

        // Get ALL elements with componentkey
        const ckEls = document.querySelectorAll('[componentkey]');
        out.ckCount = ckEls.length;

        // Get unique componentkey patterns
        const ckVals = Array.from(ckEls).map(el => el.getAttribute('componentkey'));
        const uniquePrefixes = {};
        for (const v of ckVals) {
            const prefix = v.split('_')[0];
            uniquePrefixes[prefix] = (uniquePrefixes[prefix] || 0) + 1;
        }
        out.ckPrefixes = uniquePrefixes;

        // Get full samples
        out.ckSamples = ckVals.slice(0, 20);

        // Activity-specific componentkeys
        const activityKeys = ckVals.filter(v => v.includes('urn:li:activity'));
        out.activityCount = activityKeys.length;
        out.activitySamples = activityKeys.slice(0, 10);

        // For each unique activity ID, find the containing element and extract content
        const activityIds = new Set();
        for (const v of activityKeys) {
            const m = v.match(/urn:li:activity:(\d+)/);
            if (m) activityIds.add(m[1]);
        }
        out.uniqueActivityIds = Array.from(activityIds);

        // Now try to get content for the first activity
        if (activityIds.size > 0) {
            const firstId = Array.from(activityIds)[0];
            // Find elements with this activity ID
            const relatedEls = document.querySelectorAll('[componentkey*="' + firstId + '"]');
            out.firstActivityElCount = relatedEls.length;
            out.firstActivityElTags = Array.from(relatedEls).map(el => ({
                tag: el.tagName,
                ck: el.getAttribute('componentkey'),
                class: el.className.substring(0, 60),
                text: el.innerText.substring(0, 100),
            }));
        }

        // Also check for other data attributes used
        const allAttrs = new Set();
        for (const el of document.querySelectorAll('*')) {
            for (const attr of el.attributes) {
                if (!['class', 'style', 'href', 'src', 'id', 'type', 'aria-label',
                       'aria-hidden', 'tabindex', 'role', 'placeholder', 'title',
                       'alt', 'width', 'height', 'target', 'rel', 'name',
                       'value', 'disabled', 'checked'].includes(attr.name)) {
                    allAttrs.add(attr.name);
                }
            }
        }
        out.customAttrs = Array.from(allAttrs).slice(0, 30);

        return out;
    }''')

    print(f"Total componentkey elements: {result['ckCount']}")
    print(f"\ncomponentkey prefixes:")
    for k, v in sorted(result['ckPrefixes'].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\ncomponentkey samples (first 20):")
    for s in result['ckSamples']:
        print(f"  {s}")
    print(f"\nActivity-specific keys: {result['activityCount']}")
    print(f"Unique activity IDs: {result['uniqueActivityIds']}")
    print(f"\nFirst activity element samples:")
    for el in result.get('firstActivityElTags', [])[:10]:
        print(f"  {el}")
    print(f"\nCustom attributes found: {result['customAttrs']}")

    context.close()
