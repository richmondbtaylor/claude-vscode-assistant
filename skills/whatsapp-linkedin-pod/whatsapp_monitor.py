"""
WhatsApp Group Monitor
Monitors WhatsApp Web for LinkedIn post URLs in group messages
"""

import re
import time
from playwright.sync_api import sync_playwright
from datetime import datetime


class WhatsAppMonitor:
    def __init__(self, group_name=None, playwright=None, known_urls=None):
        """
        Initialize WhatsApp monitor

        Args:
            group_name: Name of the WhatsApp group to monitor (optional)
            playwright: Optional shared Playwright instance
            known_urls: Set of URLs already processed in previous sessions
        """
        self.group_name = group_name
        self._owns_playwright = playwright is None
        self.playwright = playwright
        self.browser = None
        self.page = None
        self.known_urls = known_urls or set()
        self.processed_urls = set()
        self._initial_scan_done = False

    def start(self):
        """Start WhatsApp Web and wait for QR code scan"""
        print("Starting WhatsApp Web...")

        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self._owns_playwright = True
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir='./whatsapp_session',
            headless=False,
            args=['--start-maximized']
        )

        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        self.page.goto('https://web.whatsapp.com')

        print("\n" + "="*60)
        print("SCAN QR CODE WITH YOUR PHONE")
        print("Open WhatsApp > Linked Devices > Link a Device")
        print("You have 2 minutes to scan.")
        print("="*60)
        print("\nWaiting for WhatsApp to load...")

        # Wait for WhatsApp to load — try multiple selectors since they change often
        chat_loaded = False
        selectors = [
            '#pane-side',
            '[data-testid="chat-list"]',
            '[aria-label="Chat list"]',
            'div[role="grid"]',
        ]
        try:
            for selector in selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=120000)
                    chat_loaded = True
                    break
                except Exception:
                    continue
        except Exception:
            pass

        if chat_loaded:
            print("WhatsApp Web loaded successfully!")
        else:
            print("Could not detect WhatsApp chat list.")
            print("If WhatsApp is loaded in the browser, press Enter to continue anyway.")
            try:
                input("Press Enter to continue, or Ctrl+C to abort: ")
                chat_loaded = True
            except KeyboardInterrupt:
                return False

        return True

    def select_group(self, group_name=None):
        """
        Select a specific WhatsApp group

        Args:
            group_name: Name of the group to select
        """
        target_group = group_name or self.group_name

        if not target_group:
            print("No group name specified")
            return False

        try:
            print(f"Searching for group: {target_group}")

            # Click on search box — try multiple selectors
            search_box = None
            search_selectors = [
                '[data-testid="search-bar-input"]',
                '[aria-label="Search input textbox"]',
                '[aria-label="Search or start new chat"]',
                '[data-testid="chat-list-search"]',
                'div[contenteditable="true"][data-tab="3"]',
                'div[role="textbox"][title="Search input textbox"]',
                '#side div[contenteditable="true"]',
                'div[title="Search or start new chat"]',
                'div[role="textbox"]',
            ]
            for sel in search_selectors:
                try:
                    search_box = self.page.wait_for_selector(sel, timeout=5000)
                    if search_box:
                        break
                except Exception:
                    continue

            if not search_box:
                print("Could not find search box")
                return False

            search_box.click()
            time.sleep(1)
            self.page.keyboard.type(target_group, delay=50)
            time.sleep(2)

            # Click on the group from search results
            group_selector = f'span[title="{target_group}"]'
            group = self.page.query_selector(group_selector)

            if group:
                group.click()
                time.sleep(2)
                print(f"Selected group: {target_group}")
                return True
            else:
                print(f"Could not find group: {target_group}")
                return False

        except Exception as e:
            print(f"Error selecting group: {e}")
            return False

    def extract_linkedin_urls(self, text):
        """
        Extract LinkedIn post URLs from text

        Args:
            text: Message text to search

        Returns:
            List of LinkedIn URLs found
        """
        # Pattern to match LinkedIn post URLs (posts, feed updates, pulse articles)
        pattern = r'https?://(?:www\.)?linkedin\.com/(?:posts|feed/update|pulse)/[^\s\'"<>]+'

        urls = re.findall(pattern, text)
        return urls

    def _get_all_linkedin_urls(self):
        """Get all LinkedIn URLs currently visible on the page."""
        found_urls = set()

        # Strategy 1: Use JS to grab all hrefs containing 'linkedin' (fastest)
        try:
            hrefs = self.page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(h => h.includes('linkedin.com'))
            }''')
            for href in hrefs:
                for url in self.extract_linkedin_urls(href):
                    found_urls.add(url)
        except Exception:
            pass

        # Strategy 2: Use JS to get all visible text from the chat panel
        try:
            text = self.page.evaluate('''() => {
                const main = document.querySelector('#main');
                return main ? main.innerText : '';
            }''')
            if text:
                for url in self.extract_linkedin_urls(text):
                    found_urls.add(url)
        except Exception:
            pass

        # Strategy 3: Search the full page text as last resort
        if not found_urls:
            try:
                text = self.page.evaluate('document.body.innerText')
                for url in self.extract_linkedin_urls(text):
                    found_urls.add(url)
            except Exception:
                pass

        return found_urls

    def get_new_messages(self):
        """
        Get new LinkedIn URLs from the current chat.
        On first scan, marks all existing URLs as seen (skips them).
        """
        try:
            current_urls = self._get_all_linkedin_urls()

            if not self._initial_scan_done:
                # First scan: compare visible URLs against known history
                self._initial_scan_done = True
                self.processed_urls = current_urls.copy()

                # Find URLs visible in chat that were NOT processed in a previous session
                new_urls = current_urls - self.known_urls
                count = len(current_urls)
                new_count = len(new_urls)

                if count:
                    print(f"Initial scan: found {count} LinkedIn URL(s) in chat, {new_count} are new.")
                else:
                    print("Initial scan: no LinkedIn URLs visible in chat yet.")

                if not new_urls:
                    return []

                # Return the genuinely new URLs for processing
                new_messages = []
                for url in new_urls:
                    new_messages.append({
                        'id': url,
                        'text': url,
                        'sender': 'Unknown',
                        'linkedin_urls': [url],
                        'timestamp': datetime.now()
                    })
                    print(f"\n{'='*60}")
                    print(f"New LinkedIn URL detected (from previous session)!")
                    print(f"URL: {url}")
                    print(f"{'='*60}\n")
                return new_messages

            # Find URLs we haven't seen before
            new_urls = current_urls - self.processed_urls

            new_messages = []
            for url in new_urls:
                self.processed_urls.add(url)
                new_messages.append({
                    'id': url,
                    'text': url,
                    'sender': 'Unknown',
                    'linkedin_urls': [url],
                    'timestamp': datetime.now()
                })
                print(f"\n{'='*60}")
                print(f"New LinkedIn URL detected!")
                print(f"URL: {url}")
                print(f"{'='*60}\n")

            return new_messages

        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    def dump_page_diagnostics(self):
        """One-time diagnostic: save page snapshot and report what the bot can see."""
        print(f"\n--- Page diagnostics ---")
        print(f"URL: {self.page.url}")

        # Save page HTML snapshot for debugging
        try:
            html = self.page.content()
            with open('whatsapp_page_snapshot.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Page HTML saved to whatsapp_page_snapshot.html ({len(html)} chars)")
        except Exception as e:
            print(f"Could not save page snapshot: {e}")

        # Save all visible text
        try:
            all_text = self.page.evaluate('document.body.innerText')
            with open('whatsapp_page_text.txt', 'w', encoding='utf-8') as f:
                f.write(all_text)
            print(f"Page text saved to whatsapp_page_text.txt ({len(all_text)} chars)")

            # Check if 'linkedin' appears anywhere in the text
            linkedin_mentions = all_text.lower().count('linkedin')
            print(f"'linkedin' appears {linkedin_mentions} time(s) in page text")
        except Exception as e:
            print(f"Could not save page text: {e}")

        # Check all hrefs on the page via JS
        try:
            all_hrefs = self.page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.includes('linkedin'))
            }''')
            print(f"LinkedIn hrefs via JS: {len(all_hrefs)}")
            for h in all_hrefs[:10]:
                print(f"  {h}")
        except Exception as e:
            print(f"Could not get hrefs: {e}")

        urls = self._get_all_linkedin_urls()
        print(f"LinkedIn URLs detected by scanner: {len(urls)}")
        for u in urls:
            print(f"  {u}")
        print(f"--- End diagnostics ---\n")

    def monitor_group(self, callback=None, check_interval=10):
        """
        Continuously monitor group for new LinkedIn URLs

        Args:
            callback: Function to call when new LinkedIn URL is found
            check_interval: Seconds between checks
        """
        print(f"\n{'='*60}")
        print(f"Monitoring group for LinkedIn posts...")
        print(f"Check interval: {check_interval} seconds")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        # Run diagnostics on first cycle
        self.dump_page_diagnostics()

        scan_count = 0
        try:
            while True:
                scan_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                new_messages = self.get_new_messages()
                url_count = len(self.processed_urls)
                print(f"[{timestamp}] Scan #{scan_count} complete - {url_count} URLs tracked, {len(new_messages)} new")

                if new_messages and callback:
                    for message in new_messages:
                        callback(message)

                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        except Exception as e:
            print(f"Error during monitoring: {e}")

    def close(self):
        """Close browser and cleanup"""
        if self.browser:
            self.browser.close()
        if self._owns_playwright and self.playwright:
            self.playwright.stop()
        print("WhatsApp monitor closed")


# Test function
if __name__ == "__main__":
    monitor = WhatsAppMonitor()

    if monitor.start():
        # Ask for group name
        group_name = input("\nEnter the WhatsApp group name to monitor: ")

        if monitor.select_group(group_name):
            print("\nMonitoring started...")

            def on_new_message(message):
                print(f"Callback triggered for message: {message['id']}")
                print(f"LinkedIn URLs: {message['linkedin_urls']}")

            try:
                monitor.monitor_group(callback=on_new_message, check_interval=5)
            except KeyboardInterrupt:
                print("\nStopping...")

    monitor.close()
