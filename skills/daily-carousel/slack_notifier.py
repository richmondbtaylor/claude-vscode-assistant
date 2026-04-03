"""
Slack Notifier -- Sends carousel approval cards to #marketing-updates.

Posts a rich Block Kit message with topic, captions, hashtags,
and a Google Drive link to review the slide images.
"""

import json
import os

import requests


def send_slack_approval(carousel: dict, image_paths: list[str], drive_links: list[str]) -> bool:
    """
    Send a carousel approval notification to Slack.
    Returns True on success.
    """
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL_ID", "")
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")

    if not channel and not webhook_url:
        print("[slack] No SLACK_CHANNEL_ID or SLACK_WEBHOOK_URL set -- skipping")
        return False

    topic = carousel.get("chosen_topic", {})
    style = carousel.get("style_preset", "unknown")
    slides = carousel.get("slides", [])
    ig_caption = carousel.get("instagram_caption", "")
    li_caption = carousel.get("linkedin_caption", "")
    ig_hashtags = carousel.get("instagram_hashtags", [])
    li_hashtags = carousel.get("linkedin_hashtags", [])
    cta = carousel.get("cta_used", {})

    # Build slide summary
    slide_summary = ""
    for s in slides:
        slide_summary += f"  {s['number']}. *{s.get('headline', '')}*"
        if s.get("subtext"):
            slide_summary += f" -- {s['subtext']}"
        slide_summary += "\n"

    # Find any working Drive links
    valid_drive_links = [l for l in drive_links if l and "drive" in l.lower()]
    drive_section = ""
    if valid_drive_links:
        drive_section = f"\n*Google Drive:* {valid_drive_links[0]}"
    elif image_paths:
        drive_section = f"\n*Local:* {len(image_paths)} slides at `{os.path.dirname(image_paths[0])}`"

    ig_tags = " ".join(f"#{t}" for t in ig_hashtags[:10])
    li_tags = " ".join(f"#{t}" for t in li_hashtags[:5])

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Daily Carousel Ready for Review",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Topic:* {topic.get('title', 'Unknown')}\n"
                    f"*Angle:* {topic.get('angle', 'N/A')}\n"
                    f"*Style:* {style}\n"
                    f"*Slides:* {len(slides)}\n"
                    f"*CTA:* {cta.get('slide_text', 'N/A')}"
                    f"{drive_section}"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Slide Content:*\n{slide_summary}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Instagram Caption:*\n>{ig_caption}\n\n{ig_tags}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*LinkedIn Caption:*\n>{li_caption[:500]}{'...' if len(li_caption) > 500 else ''}\n\n{li_tags}",
            },
        },
    ]

    # Try Bot Token API first (richer messages, button support)
    if token and channel:
        try:
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": channel,
                    "blocks": blocks,
                    "text": f"Daily Carousel: {topic.get('title', 'Ready for review')}",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("ok"):
                print(f"[slack] Approval card sent to channel {channel}")
                return True
            else:
                print(f"[slack] Bot API failed: {data.get('error')} -- falling back to webhook")
        except Exception as e:
            print(f"[slack] Bot API error: {e} -- falling back to webhook")

    # Fallback to webhook
    if webhook_url:
        try:
            resp = requests.post(
                webhook_url,
                json={"blocks": blocks, "text": f"Daily Carousel: {topic.get('title', '')}"},
                timeout=10,
            )
            resp.raise_for_status()
            print("[slack] Approval card sent via webhook")
            return True
        except Exception as e:
            print(f"[slack] Webhook failed: {e}")
            return False

    return False


def send_slack_error(error_msg: str) -> bool:
    """Send an error notification to Slack when the pipeline fails."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False

    try:
        resp = requests.post(
            webhook_url,
            json={
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "Daily Carousel Pipeline Failed"},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error_msg[:500]}```"},
                    },
                ],
                "text": f"Carousel pipeline error: {error_msg[:100]}",
            },
            timeout=10,
        )
        resp.raise_for_status()
        print("[slack] Error notification sent")
        return True
    except Exception as e:
        print(f"[slack] Failed to send error notification: {e}")
        return False
