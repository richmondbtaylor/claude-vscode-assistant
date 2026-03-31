"""Debug what links are actually on the LinkedIn feed page"""
import os, time, json
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
    time.sleep(3)

    result = page.evaluate('''() => {
        // Get all unique href patterns
        const allLinks = Array.from(document.querySelectorAll('a[href]'));
        const hrefs = allLinks.map(a => a.href).filter(h => h.includes('linkedin.com'));

        // Categorize
        const patterns = {};
        for (const h of hrefs) {
            const m = h.match(/linkedin\.com\/([^/?#]+)/);
            if (m) {
                patterns[m[1]] = (patterns[m[1]] || 0) + 1;
            }
        }

        // Get sample links that might be post links
        const postLikeLinks = hrefs.filter(h =>
            h.includes('/posts/') ||
            h.includes('/feed/') ||
            h.includes('/activity') ||
            h.includes('/update/')
        ).slice(0, 20);

        // Get total link count
        const totalLinks = allLinks.length;

        // Try various selectors
        return {
            totalLinks,
            topPatterns: patterns,
            postLikeLinks,
            feedUpdateLinks: hrefs.filter(h => h.includes('/feed/update/')).slice(0, 5),
            postsLinks: hrefs.filter(h => h.includes('/posts/')).slice(0, 5),
            activityLinks: hrefs.filter(h => h.includes('activity')).slice(0, 5),
        };
    }''')

    print(f"Total links: {result['totalLinks']}")
    print(f"\nTop URL patterns:")
    for k, v in sorted(result['topPatterns'].items(), key=lambda x: -x[1])[:20]:
        print(f"  /{k}: {v}")
    print(f"\nPost-like links (first 20):")
    for h in result['postLikeLinks']:
        print(f"  {h}")
    print(f"\n/feed/update/ links: {result['feedUpdateLinks']}")
    print(f"\n/posts/ links: {result['postsLinks']}")
    print(f"\nactivity links: {result['activityLinks']}")

    context.close()
