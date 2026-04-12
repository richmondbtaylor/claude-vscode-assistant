# Clawd Bot - Quick Start Guide

## Step-by-Step Setup

### 1. Install Dependencies

Open terminal in the project folder and run:

```bash
pip install -r requirements.txt
playwright install chromium
```

Or run the setup wizard:

```bash
python setup.py
```

### 2. Configure Your Credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your favorite editor
notepad .env  # On Windows
```

You'll need:
- **Anthropic API Key**: Get from https://console.anthropic.com/
- **LinkedIn Email & Password**: Your LinkedIn login credentials
- **WhatsApp Phone**: Your phone number with country code

### 3. Run the Bot

```bash
python main.py
```

The bot will:
1. Login to LinkedIn (browser will open)
2. Open WhatsApp Web (scan QR code with your phone)
3. Ask for the WhatsApp group name to monitor
4. Start monitoring for LinkedIn URLs

### 4. Testing Individual Components

Before running the full bot, test each component:

#### Test Claude AI Comment Generator
```bash
python claude_generator.py
```

#### Test LinkedIn Automation
```bash
python linkedin_commenter.py
```
- Will login to LinkedIn
- Ask for a LinkedIn post URL
- Extract post content
- Optionally post a test comment

#### Test WhatsApp Monitor
```bash
python whatsapp_monitor.py
```
- Scan QR code
- Enter group name
- Will detect LinkedIn URLs in messages

## How It Works

```
┌─────────────────┐
│ WhatsApp Group  │
│  (Monitors for  │
│  LinkedIn URLs) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LinkedIn Post   │
│   (Extracts     │
│    content)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Claude AI     │
│  (Generates     │
│   comment)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LinkedIn      │
│ (Posts comment) │
└─────────────────┘
```

## Configuration Options

Edit `.env` to customize:

- `CHECK_INTERVAL`: How often to check for new messages (default: 60 seconds)
- `MAX_COMMENTS_PER_DAY`: Safety limit for daily comments (default: 20)

## Safety Features

✓ **Manual Review Mode**: Review each comment before posting (enabled by default)
✓ **Daily Limits**: Prevents spam with configurable daily limits
✓ **Duplicate Detection**: Won't comment on the same post twice
✓ **Activity Logging**: All actions logged to `bot_activity.log`

## Disabling Manual Review

To run fully automatically, edit `main.py`:

```python
def should_review_comment(self):
    return False  # Change True to False
```

## Troubleshooting

### "Could not find group"
- Make sure you typed the exact group name (case-sensitive)
- Check that you're a member of the group

### "Login failed"
- Check your LinkedIn credentials in `.env`
- LinkedIn might require 2FA - complete it in the browser

### "WhatsApp won't load"
- Make sure you scanned the QR code
- Try closing other WhatsApp Web sessions
- Clear `whatsapp_session` folder and try again

### "Comment not posted"
- LinkedIn's DOM changes frequently
- Check `bot_activity.log` for errors
- You may need to update selectors in `linkedin_commenter.py`

## Important Warnings

⚠️ **Use at Your Own Risk**
- This bot may violate LinkedIn's Terms of Service
- Your account could be suspended or banned
- Use responsibly and ethically
- Consider this an educational project

⚠️ **WhatsApp Automation**
- Uses unofficial WhatsApp Web automation
- Could result in WhatsApp ban
- Don't use with important accounts

## Recommended Usage

1. **Start with manual review enabled** - Review all comments before posting
2. **Use low daily limits** - Start with 5-10 comments per day
3. **Vary your timing** - Don't run 24/7
4. **Personalize comments** - Adjust the Claude prompt to match your style
5. **Monitor logs** - Check `bot_activity.log` regularly

## Customizing Claude's Comments

Edit `claude_generator.py` to customize the comment generation prompt:

```python
def _build_prompt(self, post_content, post_author, additional_context):
    prompt = f"""You are a professional LinkedIn user...

    # Customize this section to match your style!
    """
```

## Next Steps

- [ ] Test each component individually
- [ ] Configure your credentials
- [ ] Run a test with manual review enabled
- [ ] Monitor the bot's performance
- [ ] Adjust prompts and settings as needed

## Support

If you encounter issues:
1. Check `bot_activity.log` for errors
2. Test individual components
3. Verify your credentials in `.env`
4. Make sure all dependencies are installed

Good luck! Use responsibly! 🤖
