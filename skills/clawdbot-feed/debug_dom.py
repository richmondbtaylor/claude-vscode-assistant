"""Dig into the actual DOM structure of LinkedIn feed posts"""
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
    time.sleep(12)
    page.evaluate('window.scrollBy(0, 400)')
    time.sleep(3)

    result = page.evaluate('''() => {
        const out = {};

        // Find time elements - every post has a timestamp
        const times = document.querySelectorAll('time');
        out.timeCount = times.length;
        out.timeSamples = Array.from(times).slice(0, 5).map(t => ({
            datetime: t.getAttribute('datetime'),
            text: t.innerText,
            parentTag: t.parentElement ? t.parentElement.tagName : null,
            parentHref: t.parentElement ? t.parentElement.getAttribute('href') : null,
            grandparentTag: (t.parentElement && t.parentElement.parentElement) ? t.parentElement.parentElement.tagName : null,
        }));

        // Check for aria-label patterns on buttons
        const buttons = document.querySelectorAll('[aria-label]');
        const ariaLabels = Array.from(buttons).slice(0, 30).map(b => b.getAttribute('aria-label')).filter(l => l);
        out.ariaLabels = ariaLabels;

        // Check for any element with a numeric ID of 15+ digits in href
        const allAs = document.querySelectorAll('a[href]');
        const longNumLinks = Array.from(allAs)
            .map(a => a.href)
            .filter(h => /\d{15,}/.test(h))
            .slice(0, 10);
        out.longNumLinks = longNumLinks;

        // Look for article elements or post containers
        const articles = document.querySelectorAll('article, [role="article"]');
        out.articleCount = articles.length;
        if (articles[0]) {
            // Get first 500 chars of text from first article
            out.firstArticleText = articles[0].innerText.substring(0, 300);
            // Get all links in first article
            out.firstArticleLinks = Array.from(articles[0].querySelectorAll('a[href]')).map(a => a.href);
        }

        // Look for li elements in the main feed area
        const mainContent = document.querySelector('main') || document.querySelector('[role="main"]') || document.body;
        const feedItems = mainContent.querySelectorAll('li');
        out.mainLiCount = feedItems.length;
        if (feedItems[0]) {
            out.firstLiClass = feedItems[0].className.substring(0, 100);
            out.firstLiText = feedItems[0].innerText.substring(0, 200);
            out.firstLiLinks = Array.from(feedItems[0].querySelectorAll('a[href]')).map(a => a.href).slice(0, 5);
        }

        // Check for spans with role=link
        const spanLinks = document.querySelectorAll('[role="link"]');
        out.spanLinkCount = spanLinks.length;
        out.spanLinkSamples = Array.from(spanLinks).slice(0, 5).map(el => ({
            tag: el.tagName,
            text: el.innerText.substring(0, 50),
            ariaLabel: el.getAttribute('aria-label'),
        }));

        // Get all unique link patterns that include numbers
        const allHrefs = Array.from(document.querySelectorAll('a[href]')).map(a => a.href);
        const withNumbers = allHrefs.filter(h => /\/\d{5,}/.test(h) || /activity/.test(h));
        out.numericLinks = withNumbers.slice(0, 20);

        return out;
    }''')

    print(f"Time elements found: {result['timeCount']}")
    print(f"\nTime samples:")
    for t in result.get('timeSamples', []):
        print(f"  {t}")

    print(f"\nArticle elements: {result['articleCount']}")
    if result.get('firstArticleText'):
        print(f"First article text: {result['firstArticleText'][:200]}")
        print(f"First article links: {result.get('firstArticleLinks', [])}")

    print(f"\nMain feed li count: {result['mainLiCount']}")
    if result.get('firstLiText'):
        print(f"First li class: {result.get('firstLiClass')}")
        print(f"First li text: {result.get('firstLiText')}")
        print(f"First li links: {result.get('firstLiLinks', [])}")

    print(f"\nSpan/role=link count: {result['spanLinkCount']}")
    for s in result.get('spanLinkSamples', []):
        print(f"  {s}")

    print(f"\nLinks with long numbers/activity: {result.get('numericLinks', [])}")

    print(f"\nAria labels (first 30): {result.get('ariaLabels', [])[:20]}")

    print(f"\nLinks with 15+ digit numbers: {result.get('longNumLinks', [])}")

    context.close()
