"""Lane 2a: seed companies by sweeping Google Maps across metros x categories.

Port of ~/.claude/bob-miami-150/maps_scrape.py, which produced 2,669 clean
records in production. `load_seen`, `save_seen`, `feature_id`, `scroll_feed`,
`get_attr`, `scrape_place` and their scroll/sleep pacing are unchanged. What
changed: the hardcoded DADE/BROWARD city lists became config.METROS, the
BATCHES query dict became config.MAPS_CATEGORIES, and every scraped place is
routed through place_to_record so output matches the canonical record shape
instead of the old firms_raw.jsonl shape.

Collects: name, category, rating, review count, address, phone, website, maps URL.
Checkpoints by feature-id so re-runs skip already-scraped places. Each accepted
record is appended (append_jsonl) and flushed to data/seed_maps.jsonl before its
feature-id is ever added to the in-memory seen set, and seen_ids.json is only
saved after that (C14) - so a crash can at worst cost a harmless re-scrape of a
handful of places, never a silent permanent loss of an already-durable record.

Usage:
  uv run seed_maps.py
  uv run seed_maps.py --metros "Tampa FL" --categories "roofing contractor"
"""
import argparse
import json
import random
import re
import time

from playwright.sync_api import sync_playwright

import config
from lib.normalize import norm_phone, registrable_domain
from lib.records import append_jsonl, company_id

OUT = config.DATA / "seed_maps.jsonl"
SEEN_PATH = config.DATA / "seen_ids.json"

# "20350 S Dixie Hwy Suite 202, Cutler Bay, FL 33189"
_ADDR_TAIL = re.compile(r",\s*([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})")

FID_RE = re.compile(r"0x[0-9a-f]+:0x[0-9a-f]+")


def place_to_record(place: dict, query: str, city: str) -> dict | None:
    """Map one scraped Maps place to the canonical record shape."""
    phone = norm_phone(place.get("phone"))
    domain = registrable_domain(place.get("website"))
    if not phone and not domain:
        return None  # unreachable, no point carrying it

    name = (place.get("name") or "").strip()
    if not name:
        return None

    addr = place.get("address") or ""
    match = _ADDR_TAIL.search(addr)
    if match:
        city_out, state, zip_out = match.group(1), match.group(2), match.group(3)
    else:
        city_out, state, zip_out = city.rsplit(" ", 1)[0], city.rsplit(" ", 1)[-1], ""

    return {
        "company_id": company_id(name, state, domain),
        "name": name,
        "domain": domain,
        "website": place.get("website"),
        "phone": phone,
        "email": None,
        "email_status": "none",
        "address": addr,
        "city": city_out,
        "state": state,
        "zip": zip_out,
        "naics": "",
        "category": place.get("category") or "",
        "sources": ["maps"],
        "signals": {
            "reviews": place.get("reviews") or 0,
            "rating": place.get("rating"),
            "maps_query": query,
            "maps_city": city,
            "needs_liveness_check": False,
        },
    }


def load_seen():
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text()))
    return set()


def save_seen(seen):
    SEEN_PATH.write_text(json.dumps(sorted(seen)))


def feature_id(href):
    m = FID_RE.search(href)
    return m.group(0) if m else href.split("/maps/place/")[-1][:80]


def scroll_feed(page, max_scrolls=10):
    links = {}
    for _ in range(max_scrolls):
        feed = page.query_selector('div[role="feed"]')
        if not feed:
            break
        page.evaluate("el => el.scrollBy(0, 4000)", feed)
        time.sleep(random.uniform(1.5, 2.6))
        for item in page.eval_on_selector_all(
            'a[href*="/maps/place/"]',
            'els => els.map(e => ({href: e.href, name: e.getAttribute("aria-label")}))',
        ):
            if item["name"]:
                links[feature_id(item["href"])] = item
        try:
            if page.get_by_text("You've reached the end of the list").count() > 0:
                break
        except Exception:
            pass
    return links


def get_attr(page, selector, attr):
    el = page.query_selector(selector)
    return el.get_attribute(attr) if el else None


def fresh_only(links: dict, seen: set) -> dict:
    """Feature-ids in links that are not already in seen.

    This is the sole resume gate: a re-run of the same metro/category cell
    rediscovers the same feature-ids on the feed, and every one of them is
    filtered out here before the loop that calls scrape_place / append_jsonl
    ever runs, so a resumed run appends nothing for places already recorded.
    """
    return {fid: v for fid, v in links.items() if fid not in seen}


def scrape_place(page, href):
    page.goto(href, timeout=45000)
    page.wait_for_selector("h1", timeout=20000)
    time.sleep(random.uniform(1.2, 2.2))
    rec = {"maps_url": href.split("?")[0]}
    try:
        rec["name"] = page.locator("h1").first.inner_text().strip()
    except Exception:
        return None
    phone_id = get_attr(page, 'button[data-item-id^="phone:tel:"]', "data-item-id")
    rec["phone"] = phone_id.split("tel:")[-1] if phone_id else None
    rec["website"] = get_attr(page, 'a[data-item-id="authority"]', "href")
    addr = get_attr(page, 'button[data-item-id="address"]', "aria-label")
    rec["address"] = addr.replace("Address: ", "").strip() if addr else None
    try:
        cat = page.query_selector('button[jsaction*="category"]')
        rec["category"] = cat.inner_text().strip() if cat else None
    except Exception:
        rec["category"] = None
    # rating + reviews from the "x.y stars n Reviews" aria-label block
    try:
        blk = page.query_selector('div[role="main"] span[role="img"][aria-label*="star"]')
        if blk:
            label = blk.get_attribute("aria-label") or ""
            m = re.search(r"([\d.]+)\s+star", label)
            rec["rating"] = float(m.group(1)) if m else None
        txt = page.locator('div[role="main"]').first.inner_text()[:600]
        m = re.search(r"\(([\d,]+)\)", txt)
        rec["reviews"] = int(m.group(1).replace(",", "")) if m else None
    except Exception:
        rec["rating"] = rec.get("rating")
        rec["reviews"] = None
    return rec


def run(categories, metros):
    # Resume relies only on seen_ids.json; data/seed_maps.jsonl is append-only
    # so there is nothing to preload from it (C14).
    seen = load_seen()
    n_new = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()
        for metro in metros:
            for q in categories:
                url = f"https://www.google.com/maps/search/{q.replace(' ', '+')}+in+{metro.replace(' ', '+')}"
                try:
                    page.goto(url, timeout=45000)
                    page.wait_for_selector('div[role="feed"], h1', timeout=25000)
                except Exception as e:
                    print(f"[skip] {q} / {metro}: {e}", flush=True)
                    continue
                time.sleep(random.uniform(2, 3.5))
                links = scroll_feed(page)
                fresh = fresh_only(links, seen)
                print(f"[{metro} | {q}] feed={len(links)} new={len(fresh)}", flush=True)
                for fid, item in fresh.items():
                    try:
                        place = scrape_place(page, item["href"])
                    except Exception as e:
                        print(f"  [err] {item['name']}: {type(e).__name__}", flush=True)
                        continue
                    if place:
                        rec = place_to_record(place, q, metro)
                        if rec:
                            # C14: append (and flush) the record before this fid's
                            # seen-state is ever persisted to disk, so a crash never
                            # leaves seen_ids.json claiming a fid whose record is not
                            # yet durable.
                            append_jsonl(OUT, [rec])
                            n_new += 1
                    seen.add(fid)
                    if n_new and n_new % 25 == 0:
                        save_seen(seen)
                    time.sleep(random.uniform(1.5, 3.5))
                save_seen(seen)
        browser.close()
    save_seen(seen)
    print(f"DONE: {n_new} new records written to {OUT}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metros", default=None,
                     help="comma-separated subset, e.g. \"Tampa FL,Miami FL\"")
    ap.add_argument("--categories", default=None,
                     help="comma-separated subset, e.g. \"roofing contractor\"")
    args = ap.parse_args()
    metros = [m.strip() for m in args.metros.split(",")] if args.metros else config.METROS
    categories = ([c.strip() for c in args.categories.split(",")]
                   if args.categories else config.MAPS_CATEGORIES)
    run(categories, metros)


if __name__ == "__main__":
    main()
