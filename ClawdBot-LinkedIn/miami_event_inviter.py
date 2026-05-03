"""
Miami AI Builders Event Inviter
1. 1st-connections people search → apply Miami location filter (all options)
2. For each person: hover their card → click the Message button next to them
3. Type and send the event invite → close compose → next person
"""
import json
import os
import random
import re
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

# ── Config ────────────────────────────────────────────────────────────────────
SESSION_DIR     = os.path.join(os.path.dirname(__file__), "linkedin_session")
LOG_FILE        = os.path.join(os.path.dirname(__file__), "miami_event_log.json")
SEND_DELAY_MIN  = 12
SEND_DELAY_MAX  = 22

MESSAGE_TEMPLATE = (
    "Hey {first_name}, I see you're in Miami and AI is getting bigger than ever. "
    "We have a huge lineup of demoers covering how to manage and build agents. "
    "The room will be full of builders, users, and investors. "
    "We'd love to see you there tomorrow at 6 PM: https://luma.com/mia-apr30"
)

SKIP_FULL_NAMES = {n.lower() for n in [
    "Andrés Preschel",  "Andrea Urbina",    "Valeria Guerrero",
    "Luba Olmstead",    "David Goecke",     "Katie Neck",
    "Alexander Neff",   "Max Free",         "Anatoly Kholodovsky",
    "Jorge Coll",       "Avi Amoyal",       "Zoé Fox",  "Zoe Fox",
    "Matias Viera",     "Stefan Birrer",    "Varun Sakilam",
    "Antonio Goncalves","Tariq Alinur",     "Eugenia Di Marco",
    "Abdul Ramirez",    "Sunit Kulkarni",   "Isabella Mongalo",
    "Nathan Codner",
]}
SKIP_FIRST_NAMES = {"rob"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"sent": [], "skipped": [], "failed": []}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def get_first_name(name):
    return name.strip().split()[0] if name.strip() else name

def should_skip(full_name, log):
    lower = full_name.lower()
    first = get_first_name(full_name).lower()
    if lower in SKIP_FULL_NAMES:               return True, "already_registered"
    if first in SKIP_FIRST_NAMES:              return True, "first_name_match"
    if lower in {e["name"].lower() for e in log["sent"]}:
                                               return True, "already_sent"
    return False, None


# ── Step 1: Navigate and apply Miami filter ────────────────────────────────────

def go_to_miami_search(page):
    print("Navigating to 1st-connections people search...")
    page.goto(
        "https://www.linkedin.com/search/results/people/?network=%5B%22F%22%5D",
        wait_until="domcontentloaded", timeout=60000
    )
    time.sleep(3)
    print("\n>>> Set your Miami location filters in the browser now.")
    print(">>> Script will wait 90 seconds then start sending messages...")
    for i in range(90, 0, -10):
        print(f"    {i}s remaining...")
        time.sleep(10)
    print(">>> Starting now!\n")
    return True


def _apply_locations_filter(page):
    time.sleep(2)

    # Click the Locations filter pill
    loc_btn = None
    try:
        candidate = page.locator('div').filter(has_text=re.compile(r'^Locations$')).first
        if candidate.is_visible():
            loc_btn = candidate
    except Exception:
        pass
    if not loc_btn:
        for sel in ['div:text-is("Locations")', '[role="button"]:has-text("Locations")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    loc_btn = el; break
            except Exception:
                continue
    if not loc_btn:
        print("  [!] Locations filter not found")
        return False

    loc_btn.click()
    time.sleep(2)
    print("  Clicked Locations filter")

    # Find typeahead input
    inp = None
    for sel in ['input[placeholder*="location" i]', 'input[aria-label*="location" i]',
                '.search-basic-typeahead input', '.artdeco-typeahead__input', 'input[type="text"]']:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                inp = el; break
        except Exception:
            continue
    if not inp:
        print("  [!] Location input not found")
        return False

    # Type "Miami" and click only Florida Miami options — re-query after each to avoid stale handles
    inp.click(); time.sleep(0.3)
    inp.fill(""); inp.type("Miami", delay=80)
    time.sleep(2.5)
    print("  Typed 'Miami'")

    def _is_miami_fl(label):
        lo = label.lower()
        if "miami-fort lauderdale" in lo: return True
        if "miami" in lo and "florida" in lo: return True
        return False

    selected = []
    for attempt in range(15):
        clicked_one = False
        for sel in ['[role="option"]', 'li.basic-typeahead__selectable']:
            try:
                opts = page.query_selector_all(sel)
                for opt in (opts or []):
                    try:
                        label = (opt.inner_text() or "").strip()[:80]
                        if label in selected: continue
                        if not _is_miami_fl(label): continue
                        if opt.is_visible():
                            opt.click(); time.sleep(0.8)
                            selected.append(label)
                            print(f"  Selected: {label}")
                            clicked_one = True; break
                    except Exception:
                        continue
                if clicked_one: break
            except Exception:
                continue
        if not clicked_one: break

    if not selected:
        for term in ["Miami-Fort Lauderdale", "Miami, Florida", "Miami Beach, Florida"]:
            for sel in [f'[role="option"]:has-text("{term}")', f'li:has-text("{term}")']:
                try:
                    opt = page.query_selector(sel)
                    if opt and opt.is_visible():
                        opt.click(); time.sleep(0.8)
                        selected.append(opt.inner_text().strip()[:60])
                        print(f"  Selected (fallback): {selected[-1]}")
                        break
                except Exception:
                    continue
            if selected: break

    page.screenshot(path=os.path.join(os.path.dirname(__file__), "miami_step3_selected.png"))
    time.sleep(1)

    # Click "Show results" using Playwright locators (handles shadow DOM)
    clicked = False
    for name_pat in ["Show results", re.compile(r'show .*(result|people)', re.IGNORECASE)]:
        try:
            btn = page.get_by_role("button", name=name_pat)
            if btn.is_visible(timeout=3000):
                btn.click(); time.sleep(5)
                clicked = True; print("  Clicked Show results"); break
        except Exception:
            continue

    if not clicked:
        try:
            btn = page.locator('button.artdeco-button--primary').last
            if btn.is_visible(timeout=3000):
                btn.click(); time.sleep(5)
                clicked = True; print("  Clicked Show results (primary)")
        except Exception:
            pass

    if not clicked:
        page.keyboard.press("Enter"); time.sleep(3)
        if "geoUrn" in page.url:
            clicked = True; print("  Filter applied via Enter")

    if not clicked:
        print("  [!] Show results not found — unfiltered results")
    return clicked


# ── Step 2: Extract people from page ──────────────────────────────────────────

JS_GET_PEOPLE = """() => {
    const BAD = ['linkedin member','connect','follow','1st','2nd','3rd',
                 'degree connection','mutual connection','message','more'];
    function clean(txt) {
        const t = (txt||'').trim();
        if (t.length < 2 || t.length > 80) return '';
        const lo = t.toLowerCase();
        if (BAD.some(b => lo === b || lo === b+'s')) return '';
        if (lo.includes('linkedin member')) return '';
        if (t.includes('·') || t.includes('•')) return '';
        if (/^[0-9]/.test(t)) return '';
        return t;
    }
    function inNav(el) {
        for (let e = el; e; e = e.parentElement) {
            const t = e.tagName;
            if (t==='HEADER'||t==='FOOTER'||t==='NAV') return true;
            if (e.id==='global-nav') return true;
        }
        return false;
    }
    function getCardText(link) {
        // Prefer the closest <li> — each search result card is a list item
        const li = link.closest('li');
        if (li) return (li.innerText || li.textContent || '').substring(0, 500);
        // Fallback: walk up until we find a container sized for one card
        let el = link.parentElement;
        for (let i = 0; i < 20; i++) {
            if (!el) break;
            const t = (el.innerText || el.textContent || '').trim();
            if (t.length >= 80 && t.length <= 500) return t;
            el = el.parentElement;
        }
        return '';
    }
    const results = [], seen = new Set();
    for (const link of document.querySelectorAll('a[href*="/in/"]')) {
        if (inNav(link)) continue;
        const href = link.href.split('?')[0];
        if (seen.has(href)) continue;
        let name = '';
        for (const span of link.querySelectorAll('span')) {
            const n = clean(span.textContent);
            if (n) { name = n; break; }
        }
        if (!name) {
            const lines = (link.textContent||'').split(/[\\n\\r]/).map(l=>clean(l)).filter(Boolean);
            if (lines.length) name = lines[0];
        }
        if (!name) continue;
        const slug = href.split('/in/').slice(1).join('/in/').split('/')[0];
        if (!slug) continue;
        const cardText = getCardText(link);
        seen.add(href);
        results.push({name, href, slug, cardText});
    }
    return results;
}"""


# ── Step 3: Click Message button using Playwright locator (pierces shadow DOM) ─

def click_message_button(page, slug, full_name):
    """
    Hover the person's card to reveal their Message button, then click it.
    LinkedIn only renders the Message button after hovering the card.
    """
    MSG_PAT = re.compile(r'^message', re.IGNORECASE)

    link_loc = page.locator(f'a[href*="/in/{slug}"]').first
    try:
        link_loc.scroll_into_view_if_needed(timeout=5000)
        link_loc.hover(timeout=5000)
        time.sleep(1)
    except Exception:
        pass

    # After hover, only the hovered card's button is visible
    for loc in [
        page.get_by_role('button', name=MSG_PAT),
        page.locator('button:has-text("Message")'),
        page.get_by_role('link', name=MSG_PAT),
    ]:
        try:
            btn = loc.first
            if btn.is_visible(timeout=2000):
                btn.scroll_into_view_if_needed(timeout=3000)
                btn.click(timeout=10000)
                print(f"  Message btn: clicked")
                return True
        except Exception:
            continue

    print(f"  [!] No Message button found for {full_name} — skipping")
    return False


# ── Step 4: Type and send in the compose popup ─────────────────────────────────

def type_and_send(page, first_name, full_name):
    time.sleep(1)

    # Verify the compose window shows the right person before typing anything.
    # Check the compose bubble title / header for the expected name.
    compose_name = ""
    for sel in [
        '.msg-overlay-conversation-bubble__title',
        '.msg-compose-form__header',
        '.artdeco-entity-lockup__title',
        '.msg-thread__link-to-profile',
        '[aria-label*="conversation" i]',
    ]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                compose_name = (el.inner_text() or "").strip()
                if compose_name:
                    break
        except Exception:
            continue

    expected_parts = [p.lower() for p in full_name.split() if len(p) > 1]
    if compose_name:
        lo = compose_name.lower()
        match = any(part in lo for part in expected_parts)
        print(f"  Compose header: '{compose_name}' — {'OK' if match else 'MISMATCH'}")
        if not match:
            print(f"  [!] Wrong person in compose — skipping {full_name}")
            page.keyboard.press("Escape")
            return False
    else:
        print(f"  Compose header: (not found — proceeding)")

    time.sleep(0.5)

    # Find the message text editor
    editor = None
    for sel in [
        ".msg-form__contenteditable",
        '[role="textbox"][aria-label*="message" i]',
        '.msg-form__msg-content-container [contenteditable="true"]',
        'div[contenteditable="true"][data-placeholder]',
        '[role="textbox"]',
    ]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                editor = el; break
        except Exception:
            continue

    if not editor:
        try:
            loc = page.get_by_role('textbox').first
            if loc.is_visible(timeout=2000):
                editor = loc
        except Exception:
            pass

    if not editor:
        print(f"  [!] No compose editor for {full_name}")
        page.keyboard.press("Escape")
        return False

    try:
        editor.scroll_into_view_if_needed()
    except Exception:
        pass
    # Use force=True to bypass any overlay still present
    try:
        editor.click(timeout=5000, force=True)
    except Exception:
        try:
            editor.click(timeout=5000)
        except Exception:
            pass
    time.sleep(0.5)

    page.keyboard.type(MESSAGE_TEMPLATE.format(first_name=first_name), delay=20)
    time.sleep(1.5)

    # Click the Send button (Enter just adds a newline in LinkedIn's editor)
    sent = False
    for btn_sel in [
        'button.msg-form__send-button',
        'button[aria-label*="Send" i]',
        'button[type="submit"]',
    ]:
        try:
            btn = page.query_selector(btn_sel)
            if btn and btn.is_enabled():
                btn.click(); time.sleep(2); sent = True; break
        except Exception:
            continue
    if not sent:
        page.keyboard.press("Enter"); time.sleep(2)

    print(f"  [OK] Sent to {full_name}")

    # Close the compose window
    for sel in ['button[aria-label*="close" i]', 'button[aria-label*="dismiss" i]',
                'button[aria-label*="minimis" i]']:
        try:
            cl = page.query_selector(sel)
            if cl and cl.is_visible():
                cl.click(); time.sleep(0.8); break
        except Exception:
            continue

    return True


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    log = load_log()
    print(f"Log: {len(log['sent'])} sent | {len(log['skipped'])} skipped | {len(log['failed'])} failed\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=False,
            ignore_https_errors=True,
            args=["--start-maximized", "--ignore-certificate-errors"],
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        waited = 0
        while any(kw in page.url for kw in ("login", "checkpoint", "authwall", "uas/")):
            if waited == 0:
                print("[!] Not logged in — please log in in the browser window.")
                print("    Waiting up to 10 minutes...")
            time.sleep(5); waited += 5
            if waited >= 600:
                print("[!] Timed out."); ctx.close(); return

        print("[OK] Logged in.\n")

        filter_applied = go_to_miami_search(page)
        if not filter_applied:
            print("[!] Could not apply Miami filter — results may not be location-filtered.")

        # Close any open modal/overlay before scraping
        page.keyboard.press("Escape"); time.sleep(2)

        base_url = page.url.split('&page=')[0]
        print(f"\n=== Sending DMs ===")
        print(f"  Base URL: {base_url}")

        page_num   = 1
        total_sent = len(log["sent"])

        while True:
            print(f"\n--- Page {page_num} ---")
            if page_num > 1:
                page.goto(f"{base_url}&page={page_num}",
                          wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                page.keyboard.press("Escape"); time.sleep(1)

            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), f"miami_results_p{page_num}.png"))

            people = page.evaluate(JS_GET_PEOPLE)
            print(f"  Found {len(people)} profiles")
            if not people:
                print("  No profiles — done."); break

            MIAMI_KEYWORDS = ["miami", "fort lauderdale", "coral gables", "hialeah",
                              "brickell", "doral", "kendall", "homestead", "aventura",
                              "hollywood, fl", "miramar", "pembroke pines", "hallandale"]

            for person in people:
                name = person["name"]
                slug = person["slug"]
                card_text = (person.get("cardText") or "").lower()

                # Check already-sent/skip-list first
                skip, reason = should_skip(name, log)
                if skip:
                    print(f"  SKIP [{reason}]: {name}")
                    if reason != "already_sent":
                        existing = {e["name"].lower() for e in log["skipped"]}
                        if name.lower() not in existing:
                            log["skipped"].append({"name": name, "reason": reason})
                    continue

                # Skip non-Miami people (location filter may have failed)
                if not any(kw in card_text for kw in MIAMI_KEYWORDS):
                    print(f"  SKIP [not miami]: {name} — {card_text[:80]}")
                    continue

                first_name = get_first_name(name)
                print(f"\n  [{total_sent + 1}] {name}")

                if not click_message_button(page, slug, name):
                    log["failed"].append({
                        "name": name, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_log(log); continue

                time.sleep(3)

                success = type_and_send(page, first_name, name)
                entry = {"name": name, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                if success:
                    log["sent"].append(entry); total_sent += 1
                else:
                    log["failed"].append(entry)
                save_log(log)

                delay = random.randint(SEND_DELAY_MIN, SEND_DELAY_MAX)
                print(f"  Waiting {delay}s...")
                time.sleep(delay)

            # Navigate back to results page to check for next page
            nav_url = f"{base_url}&page={page_num}" if page_num > 1 else base_url
            page.goto(nav_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            try:
                nxt = page.query_selector('button[aria-label="Next"]')
                if nxt and nxt.is_visible() and nxt.is_enabled():
                    page_num += 1
                else:
                    print("  No next page."); break
            except Exception:
                break

        print(f"\n=== DONE ===")
        print(f"Sent: {len(log['sent'])} | Skipped: {len(log['skipped'])} | Failed: {len(log['failed'])}")
        time.sleep(10)
        ctx.close()


if __name__ == "__main__":
    run()
