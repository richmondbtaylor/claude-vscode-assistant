"""Check li elements and iframes in LinkedIn feed"""
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
    page.evaluate('window.scrollBy(0, 800)')
    time.sleep(5)

    result = page.evaluate('''() => {
        const out = {};

        // Check for iframes
        const iframes = document.querySelectorAll('iframe');
        out.iframeCount = iframes.length;
        out.iframeSrcs = Array.from(iframes).map(f => f.src || f.getAttribute('src')).slice(0, 5);

        // Dump all li text content
        const mainEl = document.querySelector('main') || document.body;
        const lis = mainEl.querySelectorAll('li');
        out.liTexts = Array.from(lis).slice(0, 10).map(li => ({
            class: li.className.substring(0, 80),
            text: li.innerText.substring(0, 150),
            dataAttrs: Array.from(li.attributes)
                .filter(a => a.name.startsWith('data-'))
                .map(a => a.name + '=' + a.value.substring(0, 50))
                .join('; '),
            links: Array.from(li.querySelectorAll('a[href]')).map(a => a.href).slice(0, 3),
        }));

        // Check page title and URL to confirm we're on feed
        out.url = window.location.href;
        out.title = document.title;

        // Get all elements with any 'urn' in any attribute value
        const allEls = document.querySelectorAll('*');
        const urnEls = [];
        for (const el of allEls) {
            for (const attr of el.attributes) {
                if (attr.value.includes('urn:li')) {
                    urnEls.push({tag: el.tagName, attr: attr.name, val: attr.value.substring(0, 100)});
                    break;
                }
            }
            if (urnEls.length >= 10) break;
        }
        out.urnElements = urnEls;

        // Get total element count
        out.totalElements = allEls.length;

        // Get body text summary (first 500 chars)
        out.bodyTextStart = document.body.innerText.substring(0, 500);

        return out;
    }''')

    print(f"URL: {result['url']}")
    print(f"Title: {result['title']}")
    print(f"Total elements: {result['totalElements']}")
    print(f"\nIframes: {result['iframeCount']} - {result['iframeSrcs']}")
    print(f"\nLi elements (first 10):")
    for i, li in enumerate(result['liTexts']):
        print(f"  [{i}] class={li['class']}")
        print(f"       data={li['dataAttrs']}")
        print(f"       links={li['links']}")
        print(f"       text={repr(li['text'][:100])}")
    print(f"\nURN elements: {result['urnElements']}")
    print(f"\nBody text start: {repr(result['bodyTextStart'])}")

    # Also take a screenshot
    page.screenshot(path=os.path.join(os.path.dirname(__file__), 'feed_debug.png'))
    print("\nScreenshot saved to feed_debug.png")

    context.close()
