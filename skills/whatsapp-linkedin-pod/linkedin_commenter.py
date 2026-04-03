"""
LinkedIn Automation Module
Handles LinkedIn login, post scraping, and comment posting
"""

import os
import time
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()


class LinkedInCommenter:
    def __init__(self, playwright=None):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')

        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not found in .env file")

        self._owns_playwright = playwright is None
        self.playwright = playwright
        self.context = None
        self.page = None
        self.logged_in = False

    def start(self):
        """Initialize browser and login to LinkedIn"""
        print("Starting LinkedIn automation...")

        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self._owns_playwright = True

        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_profile')
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=['--start-maximized', '--disable-blink-features=AutomationControlled'],
            viewport={'width': 1920, 'height': 1080},
        )

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self._login()

    def _prompt_for_code(self):
        """Wait for Claude Code to supply the verification code via file handshake."""
        import time
        SIGNAL_FILE = r'C:\tmp\wa_pod_needs_input.txt'
        RESPONSE_FILE = r'C:\tmp\wa_pod_input_response.txt'

        # Clear any old response
        if os.path.exists(RESPONSE_FILE):
            os.remove(RESPONSE_FILE)

        # Signal that we need a code
        with open(SIGNAL_FILE, 'w') as f:
            f.write('>>> Enter verification code:')

        print('[WAITING] Waiting for verification code from Claude Code...')

        # Poll for the response (up to 5 minutes)
        for _ in range(300):
            if os.path.exists(RESPONSE_FILE):
                with open(RESPONSE_FILE) as f:
                    code = f.read().strip()
                os.remove(RESPONSE_FILE)
                if os.path.exists(SIGNAL_FILE):
                    os.remove(SIGNAL_FILE)
                return code
            time.sleep(1)

        print('[X] Timed out waiting for verification code.')
        return ''

    def _handle_checkpoint(self):
        """Handle LinkedIn checkpoint: CAPTCHA, verification code, or error page."""
        self.page.screenshot(path=r'C:\tmp\linkedin_checkpoint.png')

        # Check page content to determine what type of checkpoint
        page_text = self.page.inner_text('body').lower()

        # Case 1: CAPTCHA / security check
        if 'security check' in page_text or 'captcha' in page_text:
            print("\n[!] LinkedIn is showing a CAPTCHA / security check.")
            print("    Please solve it in the browser window.")
            print("    Waiting up to 3 minutes for you to complete it...")
            # Wait for the URL to change (user solved the CAPTCHA)
            for i in range(180):
                time.sleep(1)
                current = self.page.url
                if 'feed' in current or 'mynetwork' in current or 'linkedin.com/in/' in current:
                    print("[OK] CAPTCHA solved! Logged in successfully.")
                    self.logged_in = True
                    return
                # Check if moved to a verification code page
                page_text_now = self.page.inner_text('body').lower()
                if 'enter' in page_text_now and ('code' in page_text_now or 'pin' in page_text_now):
                    print("[OK] CAPTCHA solved, now on verification code page.")
                    break
            # If we broke out, check for code field
            if not self.logged_in:
                self._handle_verification_code()
            return

        # Case 2: Verification code page (has a pin/code input)
        pin_field = None
        try:
            pin_field = self.page.wait_for_selector(
                'input[name="pin"], input[id*="pin" i], input[id*="code" i], input[type="text"], input[type="number"]',
                timeout=8000
            )
        except Exception:
            pass

        if pin_field:
            self._handle_verification_code()
            return

        # Case 3: Error page - no CAPTCHA, no code field
        print("[!] Checkpoint page with no code input and no CAPTCHA.")
        print("    Check the browser window and resolve manually.")
        print("    Waiting up to 3 minutes...")
        for i in range(180):
            time.sleep(1)
            current = self.page.url
            if 'feed' in current or 'mynetwork' in current or 'linkedin.com/in/' in current:
                print("[OK] Logged in successfully.")
                self.logged_in = True
                return
        print("[X] Could not resolve checkpoint.")

    def _handle_verification_code(self):
        """Handle the verification code input page."""
        pin_field = None
        try:
            pin_field = self.page.wait_for_selector(
                'input[name="pin"], input[id*="pin" i], input[id*="code" i], input[type="text"], input[type="number"]',
                timeout=10000
            )
        except Exception:
            print("[X] Could not find code input field.")
            return

        if not pin_field:
            return

        print("\n[!] LinkedIn is asking for a verification code.")
        passcode = self._prompt_for_code()
        if passcode:
            try:
                pin_field.click()
                time.sleep(0.3)
                pin_field.fill(passcode)
                time.sleep(0.5)
                submit = self.page.query_selector('button[type="submit"], button:has-text("Submit"), button:has-text("Verify")')
                if submit:
                    submit.click()
                else:
                    self.page.keyboard.press('Enter')
                time.sleep(5)
                current = self.page.url
                print(f"[OK] Code submitted. URL: {current}")
                if 'feed' in current or 'mynetwork' in current or 'linkedin.com/in/' in current:
                    self.logged_in = True
            except Exception as e:
                print(f"[X] Could not enter code: {e}")
        else:
            print("[!] No code entered.")

    def _login(self):
        """Login to LinkedIn"""
        print("Logging in to LinkedIn...")

        try:
            self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)

            # If already logged in, skip
            current = self.page.url
            if any(x in current for x in ['feed', 'mynetwork', 'linkedin.com/in/']):
                print("Already logged in to LinkedIn!")
                self.logged_in = True
                return

            # Wait for the email field to appear
            email_field = self.page.wait_for_selector('input[name="session_key"]', timeout=30000)
            if not email_field:
                raise Exception("Email field not found on login page")

            # Fill email
            email_field.click()
            time.sleep(0.3)
            email_field.fill(self.email)
            time.sleep(0.5)
            print(f"[DEBUG] Email filled: {self.email[:3]}***")

            # Screenshot after filling email
            self.page.screenshot(path=r'C:\tmp\linkedin_email_filled.png')

            # Wait for and fill password
            password_field = self.page.wait_for_selector('input[name="session_password"]', timeout=10000)
            password_field.click()
            time.sleep(0.3)
            password_field.fill(self.password)
            time.sleep(0.5)
            print("[DEBUG] Password filled")

            # Screenshot after filling both fields
            self.page.screenshot(path=r'C:\tmp\linkedin_creds_filled.png')

            # Click login button
            submit_btn = self.page.wait_for_selector('button[type="submit"]', timeout=10000)
            submit_btn.click()
            print("[DEBUG] Sign in clicked, waiting for redirect...")

            # Wait for redirect after login
            time.sleep(8)

            current_url = self.page.url
            print(f"Post-login URL: {current_url}")

            if 'feed' in current_url or 'mynetwork' in current_url or 'linkedin.com/in/' in current_url:
                print("Successfully logged in to LinkedIn!")
                self.logged_in = True
            elif 'checkpoint' in current_url or 'challenge' in current_url or 'verification' in current_url:
                self._handle_checkpoint()
                self.logged_in = True
            else:
                print(f"[OK] Post-login URL looks fine: {current_url}")
                self.logged_in = True

        except Exception as e:
            print(f"Error during LinkedIn login: {e}")
            self.logged_in = False

    def extract_post_content(self, post_url):
        """
        Extract content from a LinkedIn post

        Args:
            post_url: The URL of the LinkedIn post

        Returns:
            Dictionary with post content, author, etc.
        """
        if not self.logged_in:
            print("Not logged in to LinkedIn")
            return None

        try:
            print(f"Extracting post content from: {post_url}")
            self.page.goto(post_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(8)  # Give LinkedIn's JS time to render content

            # Click "see more" / "...more" if present to expand truncated posts
            try:
                see_more = self.page.query_selector('button[aria-label*="see more" i], button:has-text("...more"), button:has-text("see more")')
                if see_more and see_more.is_visible():
                    see_more.click()
                    time.sleep(1)
            except Exception:
                pass

            # Extract post text using multiple strategies
            post_text = ""

            # Strategy 1: Try CSS selectors (multiple generations of LinkedIn DOM)
            content_selectors = [
                '.feed-shared-update-v2__description',
                '.feed-shared-text',
                '.update-components-text',
                '[data-test-id="main-feed-activity-card__commentary"]',
                '.feed-shared-inline-show-more-text',
                'div.break-words',
                'article .break-words',
            ]
            for selector in content_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        post_text = elements[0].inner_text().strip()
                        if len(post_text) > 20:
                            break
                except Exception:
                    continue

            # Strategy 2: Use JS to find the post text via aria/semantic hints
            if not post_text or len(post_text) < 20:
                try:
                    post_text = self.page.evaluate('''() => {
                        // Look for the main post content area
                        const candidates = [
                            ...document.querySelectorAll('[data-ad-preview="message"]'),
                            ...document.querySelectorAll('.attributed-text-segment-list__container'),
                            ...document.querySelectorAll('article span[dir="ltr"]'),
                            ...document.querySelectorAll('.feed-shared-update-v2 span[dir="ltr"]'),
                        ];
                        // Return the longest text block (most likely the post body)
                        let best = '';
                        for (const el of candidates) {
                            const t = el.innerText.trim();
                            if (t.length > best.length) best = t;
                        }
                        return best;
                    }''') or ""
                except Exception:
                    pass

            # Strategy 3: Grab the page's meta description (often contains post text)
            if not post_text or len(post_text) < 20:
                try:
                    post_text = self.page.evaluate('''() => {
                        const meta = document.querySelector('meta[property="og:description"]')
                                  || document.querySelector('meta[name="description"]');
                        return meta ? meta.content : '';
                    }''') or ""
                except Exception:
                    pass

            # Strategy 4: Just grab all visible text from the main content area
            if not post_text or len(post_text) < 20:
                try:
                    post_text = self.page.evaluate('''() => {
                        const main = document.querySelector('main')
                                  || document.querySelector('[role="main"]')
                                  || document.querySelector('.scaffold-layout__main');
                        return main ? main.innerText.substring(0, 2000) : '';
                    }''') or ""
                except Exception:
                    pass

            # Extract author name
            author = ""
            author_selectors = [
                '.update-components-actor__name',
                '.feed-shared-actor__name',
                'a.app-aware-link span[dir="ltr"]',
                '.update-components-actor__title',
            ]
            for sel in author_selectors:
                try:
                    el = self.page.query_selector(sel)
                    if el:
                        author = el.inner_text().strip()
                        if author:
                            break
                except Exception:
                    continue

            if not author:
                try:
                    author = self.page.evaluate('''() => {
                        const meta = document.querySelector('meta[property="og:title"]');
                        return meta ? meta.content : '';
                    }''') or ""
                except Exception:
                    pass

            # Strategy 5: Get the page title as a last resort hint
            if not post_text or len(post_text) < 20:
                try:
                    title = self.page.title() or ""
                    # LinkedIn titles often contain post snippet
                    if 'linkedin' in title.lower() and len(title) > 30:
                        post_text = title
                except Exception:
                    pass

            print(f"Extracted: author='{author[:50]}', content length={len(post_text)}")
            if post_text:
                print(f"  Content preview: '{post_text[:120]}...'")

            # Save screenshot of the post page for debugging
            try:
                self.page.screenshot(path='linkedin_extract_page.png')
                print("Post page screenshot saved to linkedin_extract_page.png")
            except Exception:
                pass

            return {
                'url': post_url,
                'content': post_text,
                'author': author
            }

        except Exception as e:
            print(f"Error extracting post content: {e}")
            return None

    def scrape_feed_posts(self, count=10):
        """
        Scrape uninteracted post URLs from the LinkedIn home feed.
        Skips posts that have already been liked or reacted to.

        Args:
            count: Number of post URLs to return

        Returns:
            List of post URL strings
        """
        if not self.logged_in:
            print("Not logged in to LinkedIn")
            return []

        print(f"Scraping LinkedIn feed for up to {count} new posts...")
        try:
            self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)

            urls = []
            scroll_attempts = 0
            max_scrolls = 20

            while len(urls) < count and scroll_attempts < max_scrolls:
                found = self.page.evaluate('''() => {
                    const results = [];

                    // LinkedIn sets data-id="urn:li:activity:..." on every feed post container
                    const containers = document.querySelectorAll('[data-id*="urn:li:activity"]');

                    for (const container of containers) {
                        const dataId = container.getAttribute('data-id');
                        if (!dataId) continue;

                        // Skip if already liked/reacted — the button label switches to "Unlike" / "Unreact"
                        let alreadyLiked = false;
                        const buttons = container.querySelectorAll('button[aria-label]');
                        for (const btn of buttons) {
                            const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                            if (label.includes('unlike') || label.includes('unreact') || label.includes('remove like')) {
                                alreadyLiked = true;
                                break;
                            }
                        }
                        if (alreadyLiked) continue;

                        // Build canonical post URL from the activity URN
                        const postUrl = 'https://www.linkedin.com/feed/update/' + dataId + '/';
                        if (!results.includes(postUrl)) {
                            results.push(postUrl);
                        }
                    }

                    return results;
                }''')

                for url in found:
                    if url not in urls:
                        urls.append(url)

                if len(urls) >= count:
                    break

                self.page.evaluate('window.scrollBy(0, 1500)')
                time.sleep(2)
                scroll_attempts += 1

            result = urls[:count]
            print(f"[OK] Found {len(result)} uninteracted feed post URLs")
            return result

        except Exception as e:
            print(f"Error scraping feed: {e}")
            return []

    def like_post(self, post_url):
        """
        Like a LinkedIn post.

        Args:
            post_url: The URL of the LinkedIn post

        Returns:
            Boolean indicating success
        """
        if not self.logged_in:
            return False

        try:
            # Make sure we're on the post page
            if self.page.url != post_url:
                self.page.goto(post_url, wait_until='domcontentloaded', timeout=60000)
                time.sleep(8)

            # Check if already liked (button label contains "unlike" or "unreact")
            already_liked = self.page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (label.includes('unlike') || label.includes('unreact')) {
                        return true;
                    }
                }
                return false;
            }''')

            if already_liked:
                print("Post already liked, skipping")
                return True

            # Find the Like button and click it using Playwright (real click, not JS)
            like_btn = None
            like_selectors = [
                'button[aria-label^="Like" i]',
                'button[aria-label="React Like"]',
                'button[aria-label*="like" i]:not([aria-label*="unlike" i])',
            ]
            for selector in like_selectors:
                try:
                    btn = self.page.query_selector(selector)
                    if btn and btn.is_visible():
                        like_btn = btn
                        break
                except Exception:
                    continue

            if like_btn:
                like_btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                like_btn.click()
                print("Post liked successfully!")
                time.sleep(2)
                return True

            # Fallback: find the first social action button (Like is always first)
            try:
                social_buttons = self.page.query_selector_all('.social-actions-button, .reactions-react-button, button[aria-label]')
                for btn in social_buttons:
                    if not btn.is_visible():
                        continue
                    label = (btn.get_attribute('aria-label') or '').lower()
                    if 'like' in label and 'unlike' not in label:
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        print(f"Liked via fallback (label='{label}')")
                        time.sleep(2)
                        return True
            except Exception:
                pass

            print("Could not find like button")
            self._dump_buttons()
            return False

        except Exception as e:
            print(f"Error liking post: {e}")
            return False

    def _dump_buttons(self):
        """Debug helper: dump all visible buttons on the page."""
        try:
            buttons = self.page.evaluate('''() => {
                return Array.from(document.querySelectorAll('button'))
                    .filter(b => b.offsetParent !== null)
                    .map(b => ({
                        text: b.innerText.trim().substring(0, 40),
                        label: (b.getAttribute('aria-label') || '').substring(0, 60),
                        classes: (b.className || '').substring(0, 80),
                        disabled: b.disabled
                    }));
            }''')
            print(f"\n--- Visible buttons on page ({len(buttons)}) ---")
            for i, b in enumerate(buttons):
                print(f"  [{i}] text='{b['text']}' | label='{b['label']}' | disabled={b['disabled']}")
            print("--- End buttons ---\n")
        except Exception as e:
            print(f"Could not dump buttons: {e}")

    def post_comment(self, post_url, comment_text):
        """
        Post a comment on a LinkedIn post

        Args:
            post_url: The URL of the LinkedIn post
            comment_text: The comment text to post

        Returns:
            Boolean indicating success
        """
        if not self.logged_in:
            print("Not logged in to LinkedIn")
            return False

        try:
            print(f"Posting comment to: {post_url}")

            # Navigate to post if not already there
            if self.page.url != post_url:
                self.page.goto(post_url, wait_until='domcontentloaded', timeout=60000)
                time.sleep(8)

            # Take a "before" screenshot
            try:
                self.page.screenshot(path='linkedin_step1_before.png')
            except Exception:
                pass

            # Step 1: Click the "Comment" button to open comment section
            # Use Playwright's real click (not JS click) for proper event dispatch
            comment_clicked = False
            comment_selectors = [
                'button[aria-label*="Comment" i]',
                'button:has-text("Comment")',
            ]
            for selector in comment_selectors:
                try:
                    btns = self.page.query_selector_all(selector)
                    for btn in btns:
                        if btn.is_visible():
                            label = btn.get_attribute('aria-label') or ''
                            # Skip "show comments" type buttons
                            if 'show' in label.lower():
                                continue
                            btn.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            btn.click()
                            comment_clicked = True
                            print(f"Clicked comment button: {selector} (label='{label}')")
                            break
                    if comment_clicked:
                        break
                except Exception:
                    continue

            if comment_clicked:
                time.sleep(3)
            else:
                print("Warning: Could not click Comment button")
                self._dump_buttons()

            # Screenshot after opening comment section
            try:
                self.page.screenshot(path='linkedin_step2_comment_open.png')
            except Exception:
                pass

            # Step 2: Find the comment text editor
            editor = None
            editor_selectors = [
                '[role="textbox"][aria-label*="comment" i]',
                '[role="textbox"][aria-label*="Comment" i]',
                '.ql-editor[contenteditable="true"]',
                'div.ql-editor',
                '[role="textbox"][contenteditable="true"]',
                'div[contenteditable="true"][data-placeholder]',
                '.comments-comment-box [contenteditable="true"]',
                '.editor-content [contenteditable="true"]',
            ]
            for selector in editor_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for el in elements:
                        if el.is_visible():
                            editor = el
                            print(f"Found editor: {selector}")
                            break
                    if editor:
                        break
                except Exception:
                    continue

            # Fallback: find any visible contenteditable
            if not editor:
                try:
                    all_editable = self.page.query_selector_all('[contenteditable="true"]')
                    for el in all_editable:
                        if el.is_visible():
                            box = el.bounding_box()
                            if box and box['height'] > 10:
                                editor = el
                                print("Found editor via contenteditable fallback")
                                break
                except Exception:
                    pass

            if not editor:
                print("Could not find comment editor!")
                self._dump_buttons()
                try:
                    self.page.screenshot(path='linkedin_no_editor.png')
                except Exception:
                    pass
                return False

            # Step 3: Focus editor and type comment
            editor.scroll_into_view_if_needed()
            time.sleep(0.5)
            editor.click()
            time.sleep(0.5)

            # Use Playwright's keyboard.type for real keystrokes
            self.page.keyboard.type(comment_text, delay=30)
            time.sleep(2)

            # Verify text was actually entered
            try:
                editor_text = editor.inner_text().strip()
                print(f"Editor text after typing: '{editor_text[:80]}'")
                if not editor_text:
                    print("Editor empty! Trying alternative input method...")
                    # Alternative: use execCommand which works with contenteditable + React
                    editor.click()
                    editor.focus()
                    self.page.evaluate('''(text) => {
                        const el = document.activeElement;
                        if (el) {
                            el.textContent = '';
                            document.execCommand('insertText', false, text);
                        }
                    }''', comment_text)
                    time.sleep(2)
                    editor_text = editor.inner_text().strip()
                    print(f"Editor text after execCommand: '{editor_text[:80]}'")
            except Exception as e:
                print(f"Could not verify editor text: {e}")

            # Screenshot after typing
            try:
                self.page.screenshot(path='linkedin_step3_typed.png')
            except Exception:
                pass

            # Step 4: Submit the comment
            # IMPORTANT: Try Ctrl+Enter FIRST while editor still has focus
            # This avoids clicking wrong buttons that open context menus
            posted = False

            # Method 1: Ctrl+Enter — LinkedIn's native shortcut, most reliable
            print("Submitting with Ctrl+Enter...")
            try:
                # Editor should still be focused from typing
                self.page.keyboard.press('Control+Enter')
                time.sleep(5)

                # Check if the editor is now empty (comment was submitted)
                try:
                    remaining = editor.inner_text().strip()
                    if not remaining or len(remaining) < 3:
                        posted = True
                        print("Ctrl+Enter succeeded (editor cleared)")
                    else:
                        print(f"Editor still has text after Ctrl+Enter: '{remaining[:40]}'")
                except Exception:
                    # Editor might be detached if comment was posted
                    posted = True
                    print("Ctrl+Enter may have succeeded (editor detached)")
            except Exception as e:
                print(f"Ctrl+Enter failed: {e}")

            # Method 2: Find submit button near the comment box
            if not posted:
                print("Ctrl+Enter didn't clear editor, trying submit button...")
                submit_selectors = [
                    'button.comments-comment-box__submit-button',
                    'button.comments-comment-box__submit-button--cr',
                    'form.comments-comment-box__form button[type="submit"]',
                ]
                for selector in submit_selectors:
                    try:
                        button = self.page.query_selector(selector)
                        if button and button.is_visible() and button.is_enabled():
                            button.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            button.click()
                            posted = True
                            print(f"Clicked submit button: {selector}")
                            time.sleep(5)
                            break
                    except Exception:
                        continue

            # Method 3: Find button with 'submit' in class name only (safe, narrow match)
            if not posted:
                try:
                    all_buttons = self.page.query_selector_all('button')
                    for btn in all_buttons:
                        if not btn.is_visible() or not btn.is_enabled():
                            continue
                        classes = btn.get_attribute('class') or ''
                        if 'submit' in classes.lower():
                            btn.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            btn.click()
                            posted = True
                            print(f"Clicked submit by class: '{classes[:60]}'")
                            time.sleep(5)
                            break
                except Exception as e:
                    print(f"Button search error: {e}")

            # Dump buttons for diagnostics if nothing worked
            if not posted:
                self._dump_buttons()

            # Take final screenshot
            try:
                self.page.screenshot(path='linkedin_step4_submitted.png')
                print("Final screenshot saved to linkedin_step4_submitted.png")
            except Exception:
                pass

            if posted:
                print("Comment posted successfully!")
                return True
            else:
                print("Could not find or click post button")
                return False

        except Exception as e:
            print(f"Error posting comment: {e}")
            return False

    def close(self):
        """Close browser and cleanup"""
        if self.context:
            self.context.close()
        if self._owns_playwright and self.playwright:
            self.playwright.stop()
        print("LinkedIn automation closed")


# Test function
if __name__ == "__main__":
    commenter = LinkedInCommenter()
    commenter.start()

    # Test with a sample post URL
    test_url = input("Enter a LinkedIn post URL to test: ")

    if test_url:
        # Extract post content
        post_data = commenter.extract_post_content(test_url)
        if post_data:
            print(f"\nExtracted Post Data:")
            print(f"Author: {post_data['author']}")
            print(f"Content: {post_data['content'][:200]}...")

            # Test posting a comment
            test_comment = "Great post! Thanks for sharing these insights."
            response = input("\nPost this test comment? (y/n): ")

            if response.lower() == 'y':
                success = commenter.post_comment(test_url, test_comment)
                print(f"Comment posting {'successful' if success else 'failed'}")

    input("\nPress Enter to close browser...")
    commenter.close()
