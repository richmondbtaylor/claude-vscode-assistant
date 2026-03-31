"""
Clawd Bot - Main Orchestrator
Coordinates WhatsApp monitoring, Claude AI comment generation, and LinkedIn posting
"""

import os
import time
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from playwright.sync_api import sync_playwright
from whatsapp_monitor import WhatsAppMonitor
from linkedin_commenter import LinkedInCommenter
from claude_generator import ClaudeCommentGenerator

load_dotenv()


class ClawdBot:
    def __init__(self):
        self.playwright = None
        self.whatsapp = None
        self.linkedin = None
        self.claude = None

        # Configuration
        self.scan_interval = 60    # Scan WhatsApp every 60 seconds
        self.feed_interval = 3600  # Scan LinkedIn feed every hour
        self.max_comments_per_day = int(os.getenv('MAX_COMMENTS_PER_DAY', 50))

        # State tracking
        self.comments_today = 0
        self.last_reset = datetime.now()
        self.processed_urls_file = 'processed_urls.json'
        self.processed_urls = self._load_processed_urls()
        self.log_file = 'bot_activity.log'

    def _load_processed_urls(self):
        """Load previously processed URLs from disk."""
        try:
            with open(self.processed_urls_file, 'r', encoding='utf-8') as f:
                urls = json.load(f)
                print(f"Loaded {len(urls)} previously processed URLs from {self.processed_urls_file}")
                return set(urls)
        except (FileNotFoundError, json.JSONDecodeError):
            print("No previous URL history found, starting fresh.")
            return set()

    def _save_processed_urls(self):
        """Save processed URLs to disk."""
        with open(self.processed_urls_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.processed_urls), f, indent=2)

    def _mark_url_processed(self, url):
        """Add a URL to the processed set and persist to disk."""
        self.processed_urls.add(url)
        self._save_processed_urls()


    def initialize(self):
        """Initialize all components"""
        print("\n" + "="*60)
        print("CLAWD BOT - LinkedIn Auto Commenter")
        print("="*60 + "\n")

        try:
            # Initialize shared Playwright instance
            print("Initializing browser engine...")
            self.playwright = sync_playwright().start()
            print("[OK] Browser engine ready\n")

            # Initialize Claude
            print("Initializing Claude AI...")
            self.claude = ClaudeCommentGenerator()
            print("[OK] Claude AI ready\n")

            # Initialize LinkedIn
            print("Initializing LinkedIn...")
            self.linkedin = LinkedInCommenter(playwright=self.playwright)
            self.linkedin.start()
            print("[OK] LinkedIn ready\n")

            # Initialize WhatsApp
            print("Initializing WhatsApp...")
            self.whatsapp = WhatsAppMonitor(playwright=self.playwright, known_urls=self.processed_urls)
            if not self.whatsapp.start():
                raise Exception("Failed to initialize WhatsApp")

            print("[OK] WhatsApp ready\n")

            return True

        except Exception as e:
            print(f"\n[X] Initialization failed: {e}")
            return False

    def log_activity(self, action, details):
        """Log bot activities"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}\n"

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(log_entry.strip())

    def reset_daily_counter(self):
        """Reset daily comment counter if it's a new day"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.comments_today = 0
            self.last_reset = now
            self.log_activity("COUNTER_RESET", "Daily comment counter reset")

    def can_post_comment(self):
        """Check if bot can post another comment today"""
        self.reset_daily_counter()
        return self.comments_today < self.max_comments_per_day

    def process_linkedin_post(self, message):
        """
        Process a LinkedIn post from WhatsApp message.
        Handles all URLs in the message sequentially with delays between them.
        """
        urls = message.get('linkedin_urls', [])
        # Filter to only unprocessed URLs
        new_urls = [u for u in urls if u not in self.processed_urls]

        for i, url in enumerate(new_urls):
            try:
                # Check daily limit
                if not self.can_post_comment():
                    self.log_activity("LIMIT_REACHED",
                                    f"Daily limit reached ({self.max_comments_per_day})")
                    break

                self.log_activity("PROCESSING", f"New LinkedIn post: {url}")

                # Extract post content
                post_data = self.linkedin.extract_post_content(url)

                if not post_data or not post_data.get('content'):
                    self.log_activity("ERROR", f"Could not extract post content: {url}")
                    self._mark_url_processed(url)
                    continue

                self.log_activity("EXTRACTED",
                                f"Post by {post_data.get('author', 'Unknown')}")

                # Skip own posts
                author = post_data.get('author', '')
                if 'richmond' in author.lower() or 'You' in author:
                    self.log_activity("SKIP", "Skipping own post")
                    self._mark_url_processed(url)
                    continue

                # Generate comment using Claude
                comment = self.claude.generate_comment(
                    post_content=post_data['content'],
                    post_author=post_data.get('author')
                )

                if not comment:
                    self.log_activity("ERROR", "Failed to generate comment")
                    self._mark_url_processed(url)
                    continue

                self.log_activity("GENERATED", f"Comment: {comment[:100]}...")

                # Display comment before posting
                print(f"\n{'='*60}")
                print(f"POST: {post_data['content'][:200]}...")
                print(f"\nGENERATED COMMENT: {comment}")
                print(f"{'='*60}")

                # Like the post first
                self.linkedin.like_post(url)

                # Post comment to LinkedIn
                success = self.linkedin.post_comment(url, comment)

                if success:
                    self.comments_today += 1
                    self._mark_url_processed(url)
                    self.log_activity("SUCCESS",
                                    f"Comment posted ({self.comments_today}/{self.max_comments_per_day} today)")
                else:
                    self.log_activity("FAILED", f"Could not post comment: {url}")
                    self._mark_url_processed(url)

                # Delay between posts (not after the last one)
                if i < len(new_urls) - 1:
                    delay = random.randint(45, 120)
                    self.log_activity("WAITING", f"Next comment in {delay}s")
                    time.sleep(delay)

            except Exception as e:
                self.log_activity("ERROR", f"Error processing post {url}: {str(e)}")
                self._mark_url_processed(url)
                continue

    def process_feed_posts(self, count=10):
        """Scrape the LinkedIn feed and comment on the first `count` new posts."""
        print(f"\n{'='*60}")
        print(f"Scanning LinkedIn feed for {count} new posts...")
        print(f"{'='*60}")

        urls = self.linkedin.scrape_feed_posts(count=count)
        new_urls = [u for u in urls if u not in self.processed_urls]

        if not new_urls:
            print("No new feed posts to process.")
            return

        print(f"Found {len(new_urls)} unprocessed feed posts")

        for i, url in enumerate(new_urls):
            try:
                if not self.can_post_comment():
                    self.log_activity("LIMIT_REACHED", f"Daily limit reached ({self.max_comments_per_day})")
                    break

                self.log_activity("PROCESSING", f"Feed post: {url}")

                post_data = self.linkedin.extract_post_content(url)

                if not post_data or not post_data.get('content'):
                    self.log_activity("ERROR", f"Could not extract feed post content: {url}")
                    self._mark_url_processed(url)
                    continue

                author = post_data.get('author', '')
                if 'richmond' in author.lower() or 'You' in author:
                    self.log_activity("SKIP", "Skipping own post")
                    self._mark_url_processed(url)
                    continue

                comment = self.claude.generate_comment(
                    post_content=post_data['content'],
                    post_author=author
                )

                if not comment:
                    self.log_activity("ERROR", "Failed to generate comment")
                    self._mark_url_processed(url)
                    continue

                print(f"\n{'='*60}")
                print(f"POST: {post_data['content'][:200]}...")
                print(f"\nGENERATED COMMENT: {comment}")
                print(f"{'='*60}")

                self.linkedin.like_post(url)
                success = self.linkedin.post_comment(url, comment)

                if success:
                    self.comments_today += 1
                    self._mark_url_processed(url)
                    self.log_activity("SUCCESS", f"Feed comment posted ({self.comments_today}/{self.max_comments_per_day} today)")
                else:
                    self.log_activity("FAILED", f"Could not post feed comment: {url}")
                    self._mark_url_processed(url)

                if i < len(new_urls) - 1:
                    delay = random.randint(45, 120)
                    self.log_activity("WAITING", f"Next comment in {delay}s")
                    time.sleep(delay)

            except Exception as e:
                self.log_activity("ERROR", f"Error processing feed post {url}: {str(e)}")
                self._mark_url_processed(url)
                continue

    def run(self, group_name):
        """
        Run the bot

        Args:
            group_name: WhatsApp group name to monitor
        """
        if not self.initialize():
            print("Failed to initialize. Exiting...")
            return

        # Select WhatsApp group
        if not self.whatsapp.select_group(group_name):
            print(f"Could not find group: {group_name}")
            print("Make sure the group name is exactly correct")
            return

        self.log_activity("STARTED", f"Monitoring group: {group_name}")

        # On startup, comment on the first 10 new posts from the feed
        self.process_feed_posts(count=10)

        print(f"\n{'='*60}")
        print(f"Bot is now running!")
        print(f"Group: {group_name}")
        print(f"WhatsApp scan: every {self.scan_interval}s")
        print(f"Feed scan: every {self.feed_interval}s")
        print(f"Daily limit: {self.max_comments_per_day} comments")
        print(f"Comments today: {self.comments_today}")
        print(f"Previously processed URLs: {len(self.processed_urls)}")
        print(f"\nPress Ctrl+C to stop")
        print(f"{'='*60}\n")

        # Run an initial WhatsApp diagnostics scan
        self.whatsapp.dump_page_diagnostics()

        last_feed_scan = time.time()
        scan_count = 0

        try:
            while True:
                scan_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Check WhatsApp for new LinkedIn URLs
                new_messages = self.whatsapp.get_new_messages()
                print(f"[{timestamp}] WhatsApp scan #{scan_count} - {len(new_messages)} new URL(s)")

                for message in new_messages:
                    self.process_linkedin_post(message)

                # Hourly LinkedIn feed scan
                now = time.time()
                if now - last_feed_scan >= self.feed_interval:
                    self.process_feed_posts(count=10)
                    last_feed_scan = time.time()

                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n\nStopping bot...")
            self.log_activity("STOPPED", "Bot stopped by user")

        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")

        if self.whatsapp:
            self.whatsapp.close()

        if self.linkedin:
            self.linkedin.close()

        if self.playwright:
            self.playwright.stop()

        print("Bot shutdown complete")


def main():
    """Main entry point"""
    bot = ClawdBot()

    print("\nWelcome to Clawd Bot!")
    print("\nThis bot will:")
    print("1. Monitor a WhatsApp group for LinkedIn post URLs")
    print("2. Use Claude AI to generate relevant comments")
    print("3. Automatically post comments to LinkedIn")
    print("\n[!] WARNING: Use responsibly! This may violate LinkedIn ToS.")

    group_name = os.getenv('WHATSAPP_GROUP', 'LinkedIn B2B Creators')

    try:
        bot.run(group_name)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        bot.cleanup()


if __name__ == "__main__":
    main()
