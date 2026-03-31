"""
Clawd Bot - FEED EDITION
Monitors LinkedIn feed and auto-engages with posts
"""

import os
import time
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from linkedin_feed_monitor import LinkedInFeedMonitor
from linkedin_commenter import LinkedInCommenter
from claude_generator import ClaudeCommentGenerator

load_dotenv()


class FeedBot:
    def __init__(self):
        self.playwright = None
        self.linkedin = None
        self.feed_monitor = None
        self.claude = None

        # Configuration (base values, will be randomized)
        self.base_scan_interval = int(os.getenv('SCAN_INTERVAL', 2700))  # 45 min base (40-60 min range)
        self.posts_per_scan = int(os.getenv('POSTS_PER_SCAN', 10))  # Posts per scan
        self.max_comments_per_day = int(os.getenv('MAX_COMMENTS_PER_DAY', 50))

        # State tracking
        self.comments_today = 0
        self.last_reset = datetime.now()
        self.processed_posts_file = 'processed_feed_posts.json'
        self.processed_post_ids = self._load_processed_posts()
        self.log_file = 'feed_bot_activity.log'

    def _load_processed_posts(self):
        """Load previously processed post IDs from disk"""
        try:
            with open(self.processed_posts_file, 'r', encoding='utf-8') as f:
                post_ids = json.load(f)
                print(f"[OK] Loaded {len(post_ids)} previously processed posts")
                return set(post_ids)
        except (FileNotFoundError, json.JSONDecodeError):
            print("[!] No previous post history found, starting fresh")
            return set()

    def _save_processed_posts(self):
        """Save processed post IDs to disk"""
        with open(self.processed_posts_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.processed_post_ids), f, indent=2)

    def _mark_post_processed(self, post_id):
        """Add a post ID to processed set and persist"""
        self.processed_post_ids.add(post_id)
        self._save_processed_posts()

    def initialize(self):
        """Initialize all components"""
        print("\n" + "="*60)
        print("CLAWD BOT - FEED EDITION")
        print("Auto-engage with your LinkedIn feed")
        print("="*60 + "\n")

        try:
            # Initialize Playwright
            print("Initializing browser engine...")
            self.playwright = sync_playwright().start()
            print("[OK] Browser ready\n")

            # Initialize Claude
            print("Initializing Claude AI...")
            self.claude = ClaudeCommentGenerator()
            print("[OK] Claude ready\n")

            # Initialize LinkedIn (this logs in)
            print("Initializing LinkedIn...")
            self.linkedin = LinkedInCommenter(playwright=self.playwright)
            self.linkedin.start()
            if not self.linkedin.logged_in:
                raise Exception("LinkedIn login failed — not logged in after start()")
            print("[OK] LinkedIn ready\n")

            # Initialize Feed Monitor (uses same page as LinkedIn)
            print("Initializing feed monitor...")
            self.feed_monitor = LinkedInFeedMonitor(self.linkedin.page)
            print("[OK] Feed monitor ready\n")

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

    def process_feed_post(self, post_data):
        """
        Process a single post from feed: extract, generate comment, post

        Args:
            post_data: Dictionary with postId, postUrl, author, content (preview)
        """
        post_id = post_data['postId']
        post_url = post_data['postUrl']

        try:
            # Check daily limit
            if not self.can_post_comment():
                self.log_activity("LIMIT_REACHED",
                                f"Daily limit reached ({self.max_comments_per_day})")
                return False

            self.log_activity("PROCESSING", f"Post by {post_data['author'][:40]}")

            # Extract full post content (go to the post page)
            full_post = self.linkedin.extract_post_content(post_url)

            if not full_post or not full_post.get('content'):
                self.log_activity("ERROR", f"Could not extract content: {post_url}")
                self._mark_post_processed(post_id)
                return False

            # Generate comment
            comment = self.claude.generate_comment(
                post_content=full_post['content'],
                post_author=full_post.get('author')
            )

            if not comment:
                self.log_activity("ERROR", "Failed to generate comment")
                self._mark_post_processed(post_id)
                return False

            # Display before posting
            print(f"\n{'='*60}")
            print(f"POST: {full_post['content'][:200]}...")
            print(f"\nGENERATED COMMENT: {comment}")
            print(f"{'='*60}\n")

            # Like first
            self.linkedin.like_post(post_url)

            # Post comment
            success = self.linkedin.post_comment(post_url, comment)

            if success:
                self.comments_today += 1
                self._mark_post_processed(post_id)
                self.log_activity("SUCCESS",
                                f"Comment posted ({self.comments_today}/{self.max_comments_per_day} today)")
                return True
            else:
                self.log_activity("FAILED", "Could not post comment")
                self._mark_post_processed(post_id)
                return False

        except Exception as e:
            self.log_activity("ERROR", f"Error processing post: {str(e)}")
            self._mark_post_processed(post_id)
            return False

    def get_random_scan_interval(self):
        """
        Get randomized scan interval between 40-60 minutes
        """
        return random.randint(2400, 3600)  # 40-60 minutes

    def get_random_comment_delay(self):
        """
        Get randomized delay between individual comments (30-120 seconds)
        """
        return random.randint(30, 120)

    def generate_random_delays(self, num_posts, total_time):
        """
        Generate random delays to space out posts across the total time period

        Args:
            num_posts: Number of posts to space out
            total_time: Total time in seconds to distribute posts across

        Returns:
            List of delays in seconds
        """
        if num_posts <= 1:
            return []

        # Create random intervals that sum to approximately total_time
        # Leave some buffer at the end (10%)
        available_time = int(total_time * 0.9)

        # Generate random delays between posts
        delays = []
        for i in range(num_posts - 1):
            # Calculate average time per post, then randomize +/- 50%
            avg_delay = available_time // (num_posts - i)
            min_delay = max(60, int(avg_delay * 0.5))  # At least 1 minute
            max_delay = int(avg_delay * 1.5)

            delay = random.randint(min_delay, max_delay)
            delays.append(delay)
            available_time -= delay

        return delays

    def run(self):
        """Main bot loop"""
        if not self.initialize():
            print("[X] Failed to initialize. Exiting...")
            return

        # Pass processed IDs to feed monitor
        self.feed_monitor.processed_post_ids = self.processed_post_ids

        print(f"\n{'='*60}")
        print(f"FEED BOT IS NOW RUNNING")
        print(f"Scan interval: 40-60 min (randomized)")
        print(f"Posts per scan: {self.posts_per_scan}")
        print(f"Delay between comments: 30-120 seconds (randomized)")
        print(f"Daily limit: {self.max_comments_per_day} comments")
        print(f"Comments today: {self.comments_today}")
        print(f"Previously processed posts: {len(self.processed_post_ids)}")
        print(f"\nPress Ctrl+C to stop")
        print(f"{'='*60}\n")

        is_first_scan = True

        try:
            while True:
                if is_first_scan:
                    print(f"\n{'='*60}")
                    print(f"INITIAL SCAN - scraping first {self.posts_per_scan} posts now...")
                    print(f"{'='*60}\n")
                    self.log_activity("INITIAL_SCAN", f"Scraping first {self.posts_per_scan} posts on startup")
                else:
                    self.log_activity("SCAN_START", f"Scanning feed for {self.posts_per_scan} posts")

                # Get posts from feed
                posts = self.feed_monitor.get_posts_for_engagement(
                    posts_per_scan=self.posts_per_scan
                )

                # Calculate next scan interval (40-60 min, randomized)
                next_scan_delay = self.get_random_scan_interval()

                if not posts:
                    self.log_activity("NO_POSTS", "No new posts found, waiting until next scan")
                    print(f"\n{'='*60}")
                    print(f"No posts found. Next scan in {next_scan_delay//60}m {next_scan_delay%60}s")
                    print(f"{'='*60}\n")
                    is_first_scan = False
                    time.sleep(next_scan_delay)
                    continue

                self.log_activity("FOUND_POSTS", f"Found {len(posts)} posts to engage with")

                # Process each post with short random delays between each (30-120 sec)
                for i, post in enumerate(posts):
                    print(f"\n--- Post {i+1}/{len(posts)} ---")
                    self.process_feed_post(post)

                    # Short random delay between comments
                    if i < len(posts) - 1:
                        delay = self.get_random_comment_delay()
                        self.log_activity("WAITING", f"Next comment in {delay}s")
                        time.sleep(delay)

                is_first_scan = False

                print(f"\n{'='*60}")
                print(f"Scan complete. {len(posts)} posts processed.")
                print(f"Next scan in {next_scan_delay//60}m {next_scan_delay%60}s")
                print(f"{'='*60}\n")
                time.sleep(next_scan_delay)

        except KeyboardInterrupt:
            print("\n\nStopping bot...")
            self.log_activity("STOPPED", "Bot stopped by user")

        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")

        if self.linkedin:
            self.linkedin.close()

        if self.playwright:
            self.playwright.stop()

        print("Bot shutdown complete")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("CLAWD BOT - FEED EDITION")
    print("="*60)
    print("\nThis bot will:")
    print("1. Scan your LinkedIn feed every 40-60 minutes (randomized)")
    print("2. Find 10 new posts to engage with per scan")
    print("3. Use Claude AI to generate relevant comments")
    print("4. Automatically like and comment on posts")
    print("5. Wait 30-120 seconds between each comment (randomized)")
    print("\n[!] WARNING: Use responsibly! May violate LinkedIn ToS.")
    print("="*60 + "\n")

    bot = FeedBot()

    try:
        bot.run()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        bot.cleanup()


if __name__ == "__main__":
    main()
