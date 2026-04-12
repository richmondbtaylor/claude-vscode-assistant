# TARSEN n8n Workflow - Build Guide

This is the node-by-node spec for the n8n workflow that runs TARSEN. If the live workflow ever drifts from this doc, this doc is the source of truth unless Rich explicitly overrides it.

## Workflows to build

There are **three** separate n8n workflows:

1. `TARSEN - Reply Loop` - the main posting workflow
2. `TARSEN - Engagement Poller` - daily job that updates likes/replies/clicks on past posts
3. `TARSEN - Daily Digest` - daily report sent to Rich

Plus a **kill switch** that all three respect.

---

## Kill Switch

Simplest version: a single cell in the reply-history Sheet, on a tab called `control`, in cell `B1`, value `RUN` or `PAUSE`.

Every workflow's first node reads `control!B1`. If it's `PAUSE`, the workflow exits immediately and logs to a `kill_log` tab.

Rich can flip it manually from his phone. No webhook needed for v1.

When he says "kill TARSEN" or "pause TARSEN", set `control!B1 = PAUSE`. When he says "resume TARSEN", set it back to `RUN`.

---

## Workflow 1: TARSEN - Reply Loop

### Trigger
Cron, every 15 minutes, only between 7:00 AM and 11:00 PM America/New_York.

### Nodes

**1. Read kill switch**
Google Sheets > Read `control!B1`. If `PAUSE`, end.

**2. Read today's post count**
Google Sheets > Read `replies` filtered by `DATE(timestamp_et) == today` AND `approval_status IN ('auto', 'manual_approved')`. Count rows.

**3. Read today's warm-up cap**
Lookup against the warm-up table (see SKILL.md). If today's count >= cap, end.

**4. Pick a target tweet**
Two sub-branches:
- **a.** Read seed account list from `references/seed_accounts.md` (or a `seed_accounts` tab in the Sheet). For each handle, fetch the latest 5 tweets via X API.
- **b.** Run keyword search via X API for: `"AI automation" OR "RevOps" OR "GTM strategy" OR "pipeline generation"`, last 1 hour, min 50 likes (tier filter).

Merge results. Filter:
- Drop retweets
- Drop tweets older than 60 minutes (we want recency)
- Drop tweets younger than 3 minutes (the natural delay floor)
- Drop tweets from authors with < 5,000 followers
- Drop tweets from accounts already replied to twice today (check `replies` Sheet)
- Drop tweets where text contains political/religious keywords (see banlist)
- Drop tweets where Rich has previously replied via TARSEN (dedupe by tweet_url)

Pick the highest-priority remaining tweet. Priority = follower count weighted by recency.

**5. Fetch thread context**
Fetch up to 3 prior tweets in the thread. If thread > 3 tweets, fetch original + most recent reply only.

**6. Generate reply (Anthropic node, claude-sonnet-4-6)**
Use the system prompt + user prompt template defined in `references/ai_node_prompt.md`. That file is the source of truth for the AI node - keep them in sync.

The prompt returns a JSON object: `{ "reply_text", "tweet_type", "reply_style", "word_count", "closest_example", "skip_reason" }`.

If `skip_reason` is set, log to the `skipped` tab and end.

**7. Validate reply against guardrails**
A Function node that checks:
- Word count <= 80, ideally <= 40
- No links, no hashtags
- No banned phrases ("Great point", "Love this", "100%", "This!", em dashes, etc.)
- No competitor names (maintain a banlist)
- No political/religious/doomer keywords
- No personal attacks (sentiment check)

If any check fails, log to `failed_validation` tab and end. Do not retry in the same run - retrying tempts the model to hack constraints.

**8. Approval gate (week 1 only)**
If `control!B3` (manual_approval) is `ON`:
- Insert row into `replies` with `approval_status = 'pending'`
- Send Rich a WhatsApp notification (decided 2026-04-07 - reusing the WhatsApp infrastructure already running for the LinkedIn pod) containing the tweet URL, the draft, the chosen reply style, and two clickable webhook URLs: `<host>/tarsen/approve?id={row_id}` and `<host>/tarsen/reject?id={row_id}`
- End the workflow run. The approval webhook handles the rest.

Otherwise, continue.

The WhatsApp send can use the same `whatsapp_monitor.py` Playwright session that the LinkedIn pod uses, OR n8n can send via the WhatsApp Business Cloud API node if Rich prefers a cleaner separation. Default to reusing the Playwright session for v1 since it's already authenticated.

**9. Like the tweet**
X API > like endpoint, target tweet ID.

**10. Random delay 1**
Wait a random number of seconds between 10 and 45.

**11. Enforce minimum age**
Compute `now - tweet.created_at`. If less than a random threshold between 3 and 20 minutes, wait the difference. This makes timing look natural.

**12. Post the reply**
X API > tweet endpoint with `in_reply_to_tweet_id`.

**13. Log to Sheet**
Insert the row into `replies` with all fields populated, `approval_status = 'auto'` (or `manual_approved` if it came from the approval webhook).

**14. End**

### Approval webhook (week 1 only)

A separate webhook workflow listens for Rich's Approve/Reject clicks. On approve, it executes nodes 9-13 above for the queued draft. On reject, it updates the row to `manual_rejected` and ends.

---

## Workflow 2: TARSEN - Engagement Poller

### Trigger
Cron, daily at 3:00 AM ET.

### Nodes

1. Read all rows from `replies` where `posted_at` is within the last 7 days.
2. For each, call X API to get current likes/replies counts.
3. If profile clicks are available via X analytics API, fetch them too.
4. Update columns N, O, P in place.

---

## Workflow 3: TARSEN - Daily Digest

### Trigger
Cron, daily at 7:00 AM ET.

### Nodes

1. Read all rows from `replies` where `DATE(timestamp_et) == yesterday_et`.
2. Compute:
   - Total replies posted
   - Total likes received
   - Total replies-back received
   - Total profile clicks (if available)
   - Top 3 replies by `likes + replies*3 + clicks*5`
   - Any rows with `notes` set (flags)
   - Any rows in `failed_validation` or `skipped` tabs from yesterday
3. Format as a markdown digest.
4. Send to Rich via his preferred channel.

---

## Banlists

Maintain three banlist tabs in the Sheet:

- `banlist_competitors` - specific competitor names TARSEN must never mention
- `banlist_political` - political/religious keywords that auto-skip a tweet
- `banlist_phrases` - generic agreement openers TARSEN must never use

The validation node (step 7) reads all three on every run.

---

## API tier notes

Start on X API **Basic** tier. Watch the rate-limit headers in every response and log them. If TARSEN hits >70% of any limit two days in a row, upgrade to Pro before the warm-up ramps past 25 replies/day.

---

## Status

_(Populate as the workflow gets built)_

- [ ] Workflow 1: Reply Loop - not started
- [ ] Workflow 2: Engagement Poller - not started
- [ ] Workflow 3: Daily Digest - not started
- [ ] Approval webhook - not started
- [ ] Sheet created and Sheet ID recorded in `reply_history_schema.md`
- [ ] Seed account list populated in `seed_accounts.md`
- [ ] Banlists populated
- [ ] X API credentials in n8n
- [ ] Anthropic credentials in n8n
- [ ] Notification channel chosen for week-1 approvals
