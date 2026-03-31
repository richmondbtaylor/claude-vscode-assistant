"""Diagnose what's actually in the LinkedIn feed DOM"""
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
    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
    time.sleep(8)
    page.evaluate('window.scrollBy(0, 600)')
    time.sleep(3)

    result = page.evaluate('''() => {
        const checks = {
            'data-id*=activity': document.querySelectorAll('[data-id*="urn:li:activity"]').length,
            'data-urn*=activity': document.querySelectorAll('[data-urn*="activity"]').length,
            'occludable-update': document.querySelectorAll('[class*="occludable-update"]').length,
            'feed-shared-update-v2': document.querySelectorAll('[class*="feed-shared-update-v2"]').length,
            'ember-view li': document.querySelectorAll('.scaffold-finite-scroll__content li').length,
            'artdeco-list__item': document.querySelectorAll('.artdeco-list__item').length,
            'feed-outlet': document.querySelectorAll('[class*="feed-outlet"]').length,
        };

        // Find any element with urn:li:activity in any attribute
        const allEls = document.querySelectorAll('[data-occludable-entity-urn], [data-entity-urn], [data-update-v2]');
        checks['occludable-entity-urn'] = allEls.length;

        // Sample the first such element
        const sample = allEls[0];
        if (sample) {
            checks['sample_attrs'] = Array.from(sample.attributes).map(a => a.name + '=' + a.value.substring(0, 60)).join(', ');
            checks['sample_tag'] = sample.tagName;
            checks['sample_class'] = sample.className.substring(0, 100);
        }

        // Check for any li elements in main content
        const mainLis = document.querySelectorAll('main li, [role="main"] li');
        checks['main_li_count'] = mainLis.length;
        if (mainLis[0]) {
            checks['first_li_class'] = mainLis[0].className.substring(0, 100);
            checks['first_li_data'] = Array.from(mainLis[0].attributes).map(a => a.name + '=' + a.value.substring(0,40)).join(', ');
        }

        return checks;
    }''')

    for k, v in result.items():
        print(f"{k}: {v}")

    page.screenshot(path=os.path.join(os.path.dirname(__file__), 'feed_diag.png'))
    print("\nScreenshot saved to feed_diag.png")
    context.close()
