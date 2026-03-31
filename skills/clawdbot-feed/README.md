# ClawdBot - Feed Edition

Auto-engages with posts in your LinkedIn feed using Claude AI to generate comments.

## Setup Instructions

### 1. Install Dependencies

```bash
cd C:/Users/richm/.claude/skills/clawdbot-feed
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Settings

Your `.env` file should be in the skill directory with:
- LinkedIn credentials (from your main bot)
- Claude API key
- Scan interval: 3600s (1 hour)
- Posts per scan: 5
- Daily limit: 50 comments

### 3. Run the Bot

```bash
python main.py
```

## How It Works

1. **Scans your feed** every hour
2. **Finds 3-5 new posts** (skips sponsored posts and your own posts)
3. **Extracts post content** using Playwright
4. **Generates comment** using Claude AI (10-20 words, fun, engaging)
5. **Likes the post** first
6. **Posts the comment** automatically
7. **Waits 45-120s** between posts (randomized delay)

## Files Created at Runtime

- `processed_feed_posts.json` - Tracks which posts you've already engaged with
- `feed_bot_activity.log` - Log of all bot activity
- `linkedin_step*.png` - Debug screenshots (if errors occur)

## Configuration Options (in .env)

```env
SCAN_INTERVAL=3600       # How often to scan feed (seconds)
POSTS_PER_SCAN=5         # How many posts to engage with per scan
MAX_COMMENTS_PER_DAY=50  # Safety limit
```

## Tips

- Start with conservative settings (current defaults are good)
- The bot skips:
  - Sponsored/promoted posts
  - Posts you've already engaged with
  - Your own posts (Richmond Taylor)
  - Posts with very little content (<20 chars)

- The bot randomizes delays between posts (45-120s) to appear more human
- All comments follow your preferences: 10-20 words, no em dashes, no AI jargon

## Safety Features

- Daily comment limit (50 by default)
- Tracks processed posts to avoid duplicates
- Human-like delays between actions
- Comprehensive logging for review

## Stopping the Bot

Press `Ctrl+C` to stop gracefully.
