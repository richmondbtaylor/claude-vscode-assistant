# 🚀 START HERE - Clawd Bot Setup

## Welcome! Your bot is ready. Follow these steps:

### ✅ Step 1: Install Dependencies (5 minutes)

Open a terminal in VS Code (Terminal → New Terminal) and run:

```bash
pip install -r requirements.txt
```

Then install Playwright browsers:

```bash
playwright install chromium
```

**OR** use the setup wizard:

```bash
python setup.py
```

---

### ✅ Step 2: Get Your API Keys (5 minutes)

#### Anthropic API Key
1. Visit: https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-...`)

---

### ✅ Step 3: Create Your .env File (2 minutes)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in VS Code and fill in:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   LINKEDIN_EMAIL=your-email@example.com
   LINKEDIN_PASSWORD=your-linkedin-password
   WHATSAPP_PHONE=+1234567890
   CHECK_INTERVAL=60
   MAX_COMMENTS_PER_DAY=20
   ```

---

### ✅ Step 4: Test Each Component (10 minutes)

**Test 1: Claude AI (No browser needed)**
```bash
python claude_generator.py
```
Should generate a sample comment. If you see an API error, check your key.

**Test 2: LinkedIn (Browser will open)**
```bash
python linkedin_commenter.py
```
- Browser opens and logs into LinkedIn
- Paste a LinkedIn post URL when prompted
- It will extract the post and optionally comment

**Test 3: WhatsApp (Browser will open)**
```bash
python whatsapp_monitor.py
```
- Browser opens WhatsApp Web
- Scan QR code with your phone
- Enter a group name to monitor
- Post a LinkedIn URL in that group to test

---

### ✅ Step 5: Run the Full Bot (1 minute)

```bash
python main.py
```

The bot will:
1. ✓ Login to LinkedIn
2. ✓ Open WhatsApp Web (scan QR)
3. ✓ Ask for group name
4. ✓ Start monitoring!

When it finds a LinkedIn URL:
- Extracts the post
- Generates a comment with Claude
- Shows you the comment for approval
- Posts it to LinkedIn

---

## 🎯 Quick Debug in VS Code

Press **F5** and select:
- "Run Clawd Bot" - Run the full bot
- "Test Claude Generator" - Test AI only
- "Test LinkedIn Commenter" - Test LinkedIn only
- "Test WhatsApp Monitor" - Test WhatsApp only

---

## ⚙️ Configuration

### Manual Review Mode (Default: ON)

Review each comment before posting. To disable, edit [main.py](main.py):

```python
def should_review_comment(self):
    return False  # Change True to False
```

### Daily Limits

Edit `.env`:
```env
MAX_COMMENTS_PER_DAY=20  # Adjust as needed
CHECK_INTERVAL=60        # Check every 60 seconds
```

---

## 📋 Project Files

| File | Purpose |
|------|---------|
| [main.py](main.py) | Main bot - Run this |
| [claude_generator.py](claude_generator.py) | AI comment generator |
| [linkedin_commenter.py](linkedin_commenter.py) | LinkedIn automation |
| [whatsapp_monitor.py](whatsapp_monitor.py) | WhatsApp monitoring |
| [setup.py](setup.py) | Setup wizard |
| `.env` | Your credentials (CREATE THIS) |
| [README.md](README.md) | Full documentation |
| [QUICKSTART.md](QUICKSTART.md) | Quick start guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview |

---

## ⚠️ Important Warnings

### Legal & Ethical
- ⚠️ May violate LinkedIn Terms of Service
- ⚠️ Risk of account suspension/ban
- ⚠️ Use responsibly and ethically
- ⚠️ Consider this educational only

### Best Practices
- ✅ Start with manual review enabled
- ✅ Use low daily limits (5-10 at first)
- ✅ Don't run 24/7
- ✅ Monitor `bot_activity.log`
- ✅ Personalize Claude's prompts

---

## 🆘 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
playwright install chromium
```

### "API key not found"
- Check `.env` file exists
- Check `ANTHROPIC_API_KEY` is set correctly
- Make sure no spaces around the `=`

### "Could not find group"
- Type the EXACT group name (case-sensitive)
- Make sure you're in the group
- Try copying the name from WhatsApp

### "Login failed"
- Check LinkedIn credentials in `.env`
- Complete 2FA in the browser
- Wait for the page to fully load

### "Comment not posted"
- LinkedIn changes their HTML frequently
- Check `bot_activity.log` for details
- May need to update selectors

---

## 🎨 Customization

### Change Comment Style

Edit [claude_generator.py](claude_generator.py), find `_build_prompt()`:

```python
prompt += """
INSTRUCTIONS:
1. Write a professional, genuine LinkedIn comment (2-4 sentences)
2. Be supportive, insightful, or add value to the conversation
...
# Customize these instructions!
"""
```

### Add Features

Ideas:
- Different prompts for different post types
- Sentiment analysis
- Multiple WhatsApp groups
- Web dashboard
- Analytics

---

## 📊 Activity Logging

All actions are logged to `bot_activity.log`:

```
[2024-02-11 10:30:15] STARTED: Monitoring group: Tech Leaders
[2024-02-11 10:31:20] PROCESSING: New LinkedIn post: https://...
[2024-02-11 10:31:25] EXTRACTED: Post by John Doe
[2024-02-11 10:31:30] GENERATED: Comment: Great insights on...
[2024-02-11 10:31:45] SUCCESS: Comment posted (1/20 today)
```

---

## ✨ You're All Set!

1. Install dependencies ✓
2. Get API keys ✓
3. Create `.env` ✓
4. Test components ✓
5. Run the bot ✓

**Ready to start?**

```bash
python main.py
```

Good luck! Use responsibly! 🤖

---

**Need Help?**
- Check [QUICKSTART.md](QUICKSTART.md)
- Read [README.md](README.md)
- Review `bot_activity.log`
- Check each test script individually
