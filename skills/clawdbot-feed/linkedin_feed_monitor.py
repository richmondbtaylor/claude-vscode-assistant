"""
LinkedIn Feed Monitor
Scrapes LinkedIn feed and extracts posts for engagement

Strategy: intercept network responses from LinkedIn's SDUI pagination API
(/flagship-web/rsc-action/actions/pagination) to extract activity IDs.
This is more reliable than DOM scraping since LinkedIn's class names are
obfuscated/hashed and change frequently.
"""

import time
import re


class LinkedInFeedMonitor:
    def __init__(self, playwright_page):
        """
        Args:
            playwright_page: Existing Playwright page object (already logged into LinkedIn)
        """
        self.page = playwright_page
        self.processed_post_ids = set()

    def mark_post_processed(self, post_id):
        """Mark a post as processed so we don't engage with it again"""
        self.processed_post_ids.add(post_id)

    def get_posts_for_engagement(self, posts_per_scan=5):
        """
        Get posts from LinkedIn feed by intercepting API responses.

        LinkedIn's new SDUI architecture loads feed posts via:
          /flagship-web/rsc-action/actions/pagination?sduiid=...mainFeed...
        Each response contains ~4 unique urn:li:activity:XXXX IDs.
        We scroll to trigger multiple pagination calls until we have enough posts.

        Returns:
            List of {postId, postUrl, author, content} dicts
        """
        captured_ids = []
        seen_in_capture = set()

        def handle_response(response):
            url = response.url
            if 'linkedin.com' not in url:
                return
            # Skip static assets
            if any(url.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.ico', '.woff', '.woff2']):
                return
            try:
                body = response.body()
                text = body.decode('utf-8', errors='ignore')
                ids = re.findall(r'urn:li:activity:(\d{15,})', text)
                added = 0
                for aid in ids:
                    if aid not in seen_in_capture:
                        seen_in_capture.add(aid)
                        captured_ids.append(aid)
                        added += 1
                if added:
                    print(f"[DEBUG] API response +{added} IDs from: {url[url.find('linkedin.com')+12:url.find('linkedin.com')+80]}", flush=True)
            except Exception:
                pass

        # Register listener BEFORE navigating so we catch the initial page load too
        self.page.on('response', handle_response)

        try:
            print("Navigating to LinkedIn feed...")
            self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
            time.sleep(10)

            try:
                self.page.screenshot(path='feed_state.png')
                print("[DEBUG] Screenshot saved to feed_state.png")
            except Exception:
                pass

            print(f"[DEBUG] Feed URL: {self.page.url}")
            print(f"[DEBUG] Feed title: {self.page.title()}")
            print("[OK] Feed loaded")

            # Scroll to trigger LinkedIn's pagination API calls
            # Each scroll batch fires ~1 API call with ~4 new post IDs
            target = posts_per_scan * 3  # overshoot so filtered list still has enough
            max_scrolls = 20
            for _ in range(max_scrolls):
                new_count = sum(1 for aid in captured_ids if aid not in self.processed_post_ids)
                if new_count >= target:
                    print(f"[OK] Collected {new_count} new IDs — stopping scroll early")
                    break
                self.page.evaluate('window.scrollBy(0, window.innerHeight * 0.9)')
                time.sleep(3)

        finally:
            self.page.remove_listener('response', handle_response)

        print(f"[OK] Intercepted {len(captured_ids)} total unique activity IDs from network")

        # Filter out already-processed and build post list
        new_posts = []
        for aid in captured_ids:
            if aid in self.processed_post_ids:
                continue
            post_url = f'https://www.linkedin.com/feed/update/urn:li:activity:{aid}/'
            new_posts.append({
                'postId': aid,
                'postUrl': post_url,
                'author': 'Unknown',   # filled in by extract_post_content()
                'content': '',         # filled in by extract_post_content()
            })

        # Own-post filter (activity IDs of Rich's own posts show up when others comment on them)
        # We don't have the author here yet, so we let process_feed_post handle that
        # after extract_post_content populates the author field.

        # Trim to a reasonable number to avoid over-engaging
        new_posts = new_posts[:posts_per_scan * 3]

        print(f"[OK] Found {len(new_posts)} new posts (after filtering {len(self.processed_post_ids)} already-processed)")
        return new_posts
