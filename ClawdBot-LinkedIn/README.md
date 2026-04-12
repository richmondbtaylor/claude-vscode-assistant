# Clawd Bot - LinkedIn Auto Commenter

An intelligent bot that monitors WhatsApp groups for LinkedIn posts and automatically generates and posts relevant comments using Claude AI.

## Warning

This bot automates LinkedIn and WhatsApp interactions. Please be aware:
- May violate LinkedIn's Terms of Service
- Risk of account suspension or ban
- Use responsibly and at your own risk
- Consider using for educational purposes only

## Features

- Monitors WhatsApp group messages for LinkedIn post URLs
- Extracts LinkedIn post content
- Uses Claude AI to generate contextual, professional comments
- Automatically posts comments to LinkedIn
- Rate limiting and safety features

## Prerequisites

- Python 3.8+
- Anthropic API key (get from https://console.anthropic.com/)
- LinkedIn account
- WhatsApp account
- Chrome browser installed

## Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your actual credentials

## Usage

Run the bot:
```bash
python main.py
```

First run will require:
- LinkedIn login (saved for future use)
- WhatsApp Web QR code scan

## Configuration

Edit `.env` to customize:
- `CHECK_INTERVAL`: How often to check for new messages (seconds)
- `MAX_COMMENTS_PER_DAY`: Daily comment limit for safety

## Project Structure

```
ClawdBot-LinkedIn/
├── main.py              # Main bot orchestrator
├── whatsapp_monitor.py  # WhatsApp message monitoring
├── linkedin_commenter.py # LinkedIn automation
├── claude_generator.py  # AI comment generation
├── requirements.txt     # Python dependencies
├── .env                # Configuration (create from .env.example)
└── README.md           # This file
```

## How It Works

1. Bot monitors specified WhatsApp group
2. Detects LinkedIn post URLs in messages
3. Extracts post content from LinkedIn
4. Sends post content to Claude AI for comment generation
5. Posts generated comment to LinkedIn
6. Logs all actions for review

## Safety Features

- Rate limiting (configurable max comments per day)
- Comment review log
- Duplicate post detection
- Error handling and retries

## Disclaimer

This is an educational project. The authors are not responsible for any consequences of using this bot, including but not limited to account suspensions or violations of terms of service.
