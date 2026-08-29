"""Cost-ordered enrichment for Tier 1 rows. Free steps first, Apify last.

Waterfall order, each step skipped once the row is satisfied (a valid
contact name paired with a verified email):

1. site scrape output already on the row (free)
2. Maps phone already on the row (free)
3. state registry officer lookup (free, Florida only for this build --
   RULING (task brief): do not generalize registry lookup across states)
4. LinkedIn company page decision-maker -- OUT OF SCOPE. Task 8 confirmed
   the saved LinkedIn session no longer authenticates.
5. Hunter domain search plus verification (existing key)
6. Apollo people search by domain and title (existing key)
7. Apify code_crafter~leads-finder (paid, hard $10 ceiling) -- stubbed;
   wiring a real actor call is future work, not part of this build.

RULING C9: an earlier draft of this module implemented only steps 5-7,
so contact data the site scrape already found was ignored and Hunter was
billed for rows that a free step would have already satisfied. Steps 1-3
below close that gap.
"""
import argparse
import json
import os
import pathlib
import re
import time
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

import config
from lib.normalize import is_valid_person_name
from lib.records import append_jsonl, read_jsonl, row_key

SECURITY = pathlib.Path.home() / ".claude" / "security"

DECISION_TITLES = (
    "owner", "founder", "co-founder", "president", "ceo", "principal",
    "partner", "managing", "general manager", "coo", "cfo", "controller",
    "vice president", "director of operations", "office manager",
)


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Hard ceiling on paid enrichment. Raises rather than overspending."""

    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self.spent = 0.0

    def charge(self, amount: float) -> None:
        if self.spent + amount > self.limit_usd:
            raise BudgetExceeded(
                f"${self.spent + amount:.2f} would exceed ${self.limit_usd:.2f}")
        self.spent += amount

    def remaining(self) -> float:
        return self.limit_usd - self.spent


# Every value _key() has ever resolved this run, so _redact() can strip
# a credential out of a message even if a call site forgets to.
_SEEN_KEYS: set[str] = set()


def _key(name: str) -> str:
    """Read a secret from the environment, falling back to
    ~/.claude/security/*.env. Several bots share this directory and some
    of their .env files carry the same variable name as an unfilled
    placeholder (an empty value after "="); a placeholder must never win
    over a real value in another file, so an empty match keeps searching
    instead of returning."""
    value = os.environ.get(name)
    if value:
        _SEEN_KEYS.add(value)
        return value
    for path in sorted(SECURITY.glob("*.env")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                candidate = line.split("=", 1)[1].strip()
                if candidate:
                    _SEEN_KEYS.add(candidate)
                    return candidate
    raise RuntimeError(f"{name} not found")


_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\"'&\s]+")


def _redact(text: str) -> str:
    """Strip credential material out of a message before it is ever
    recorded. Two layers: any value _key() has actually resolved this
    run (an exact match, however it got into the string), and anything
    that merely looks like a key= or key: parameter, as a backstop for a
    value _key() never saw. Every call site that writes to
    enrich_errors must route through this via _record_error -- a
    RULING C38 fix, after a live check found httpx.HTTPStatusError's
    default message embeds the full request URL, api_key query param
    included, and that string was being written straight into
    data/enriched.jsonl."""
    for value in _SEEN_KEYS:
        if value:
            text = text.replace(value, "***REDACTED***")
    return _KEY_PATTERN.sub(r"\1***REDACTED***", text)


def _record_error(out: dict, message: str) -> None:
    """The only way enrich_errors should ever be appended to. Redacts
    first, so a future call site cannot reintroduce a credential leak
    just by forgetting to be careful."""
    out.setdefault("enrich_errors", []).append(_redact(message))


def _http_error_summary(exc: Exception) -> str:
    """A safe, generic description of a failure -- a status code where
    there is one, otherwise just the exception's class name. Never the
    exception's own message: httpx.HTTPStatusError's message is built
    from the full request, and for a GET the request URL includes every
    query parameter, api_key among them."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"http {exc.response.status_code}"
    return type(exc).__name__


def is_satisfied(row: dict) -> bool:
    """A row is done when it has a real name and a verified email."""
    name = row.get("contact_name") or ""
    return (is_valid_person_name(name)
            and row.get("contact_email_status") == "verified")


def pick_best_contact(people: list[dict]) -> dict | None:
    """Highest-ranking valid decision-maker from a list of people."""
    best, best_rank = None, len(DECISION_TITLES)
    for person in people:
        if not is_valid_person_name(person.get("name") or ""):
            continue
        title = (person.get("title") or "").lower()
        for rank, keyword in enumerate(DECISION_TITLES):
            if keyword in title and rank < best_rank:
                best, best_rank = person, rank
                break
    return best


def seed_contact_from_row(row: dict) -> dict:
    """Steps 1-2: use what site scrape and Maps already found, for free,
    before anything paid runs.

    Step 1 -- the site scrape wrote top-level email/email_status. A
    personal-classified address is a real person's address that has not
    been SMTP-verified, so it becomes a "guessed" candidate, never
    "verified" (that label is earned only by an actual verification
    call). A generic-classified address (info@, sales@) is not tied to a
    named person but is still a usable contact channel, carried over as
    contact_email_status "generic".

    Step 2 -- Maps wrote top-level phone. Carried to contact_phone so a
    row that never gets a named contact still has a way to reach it.

    Never overwrites an existing contact_* already on the row.
    """
    out = dict(row)
    if not out.get("contact_email"):
        email = out.get("email")
        status = out.get("email_status")
        if email and status == "personal":
            out["contact_email"] = email
            out["contact_email_status"] = "guessed"
        elif email and status == "generic":
            out["contact_email"] = email
            out["contact_email_status"] = "generic"
    if not out.get("contact_phone") and out.get("phone"):
        out["contact_phone"] = out["phone"]
    return out


# --- Step 3: Florida Sunbiz officer lookup -----------------------------
#
# Adapted from the working implementation at
# ~/.claude/bob-miami-150/sunbiz_fill.py. Sunbiz is Cloudflare-gated and
# needs headful Chrome via Playwright; the clearance cookie is per
# browser context, so callers must reuse one context across a whole run
# rather than opening a fresh browser per row. Florida only -- do not
# generalize to other states in this build.

_SUNBIZ_URL = "https://search.sunbiz.org"
_SUNBIZ_AGENT_CO = re.compile(r"registered agent|corp|inc\b|llc|company|service|agents", re.I)
_SUNBIZ_STOP = re.compile(r"\b(llc|inc|corp|pa|pllc|pl|co|ltd|the|of|and|a)\b")


def _sunbiz_norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = _SUNBIZ_STOP.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def _sunbiz_flip(name: str) -> str:
    # "SMITH, JOHN A" -> "John A Smith"
    name = name.strip()
    if "," in name:
        last, first = name.split(",", 1)
        name = f"{first.strip()} {last.strip()}"
    return " ".join(w.capitalize() for w in name.split())


def _sunbiz_html(page, url: str) -> str:
    page.goto(url, timeout=45000)
    for _ in range(30):
        html = page.content()
        if "Just a moment" not in html and "challenges.cloudflare.com" not in html:
            break
        time.sleep(1)
    return page.content()


def _sunbiz_search_candidates(page, firm: str) -> list[tuple[str, str]]:
    """Every exact-normalized-name match, not just the first. The
    source implementation (sunbiz_fill.py) also accepted an 8-character
    prefix match, which a live check against real Tampa rows showed
    picks the wrong entity -- "SouthShore Roofing & Exteriors" matched
    "SOUTHSHORE ROTARY FOUNDATION, INC." on the shared "southshore"
    prefix and would have attributed that foundation's officer to the
    roofing company. A missed match is acceptable (the row just stays
    unsatisfied and falls through to the next step); a wrong company is
    not. RULING C39: even exact-name matching is not enough on its own
    -- two genuinely different FL entities can normalize identically
    ("X Roofing LLC" and "X Roofing Inc" both become "x roofing") -- so
    every match is returned here and registry_lookup_fl decides what to
    do when there is more than one."""
    html = _sunbiz_html(
        page, f"{_SUNBIZ_URL}/Inquiry/CorporationSearch/SearchResults"
              f"?inquiryType=EntityName&searchTerm={quote(firm)}")
    soup = BeautifulSoup(html, "html.parser")
    want = _sunbiz_norm(firm)
    out: list[tuple[str, str]] = []
    if not want:
        return out
    for a in soup.select("td.large-width a, a[href*='SearchResultDetail']"):
        if _sunbiz_norm(a.get_text()) == want:
            out.append((a.get_text(strip=True), _SUNBIZ_URL + a["href"]))
    return out


_SUNBIZ_CITY_RE = re.compile(r"([A-Z][A-Za-z .'-]+),\s*FL\s*\d{5}")


def _sunbiz_detail_city(page, detail_url: str) -> str | None:
    """Best-effort city out of an entity's detail page (principal or
    mailing address is normally the first "CITY, FL ZIP" on the page).
    Used only to disambiguate when the name search returns more than
    one candidate."""
    html = _sunbiz_html(page, detail_url)
    text = BeautifulSoup(html, "html.parser").get_text("\n")
    m = _SUNBIZ_CITY_RE.search(text)
    return m.group(1).strip() if m else None


def _sunbiz_officers(page, detail_url: str) -> list[dict]:
    html = _sunbiz_html(page, detail_url)
    text = BeautifulSoup(html, "html.parser").get_text("\n")
    out = []
    sec = re.search(
        r"(Officer/Director Detail|Authorized Person\(s\) Detail)(.*?)"
        r"(Annual Reports|Document Images)", text, re.S)
    if not sec:
        return out
    block = sec.group(2)
    for m in re.finditer(r"Title\s+([A-Z, ]{1,12})\n+\s*([A-Z][A-Za-z ,.'-]+)", block):
        title = m.group(1).strip()
        name = m.group(2).strip().split("\n")[0]
        if _SUNBIZ_AGENT_CO.search(name) or len(name) < 5:
            continue
        out.append({"title": title, "name": _sunbiz_flip(name)})
    return out


def registry_lookup_fl(page, firm_name: str, city: str | None = None) -> dict | None:
    """Step 3: best valid decision-maker from Sunbiz for a FL entity, or
    None if the firm was not found, was ambiguous with no corroborating
    city, or had no usable officer names.

    RULING C39: when the name search returns more than one candidate,
    a name match alone is not enough to trust -- attributing a real
    named human to the wrong company is worse than having no name, so a
    second entity is only accepted if its registered address city
    agrees with the row's own city, and only if exactly one candidate
    agrees. Zero or more than one corroborating candidate means no
    officer is recorded at all.
    """
    candidates = _sunbiz_search_candidates(page, firm_name)
    if not candidates:
        return None
    if len(candidates) == 1:
        _, url = candidates[0]
    else:
        if not city:
            return None
        want_city = _sunbiz_norm(city)
        corroborated = [
            (name, url) for name, url in candidates
            if want_city and _sunbiz_norm(_sunbiz_detail_city(page, url) or "") == want_city
        ]
        if len(corroborated) != 1:
            return None
        _, url = corroborated[0]
    officers = _sunbiz_officers(page, url)
    return pick_best_contact([{"name": o["name"], "title": o["title"]} for o in officers])


def open_sunbiz_page():
    """Launch one headful browser context for the whole run. Sunbiz's
    Cloudflare clearance cookie is per-context, so this must be opened
    once and reused across every FL row, not per row."""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(channel="chrome", headless=False)
    except Exception:
        browser = pw.chromium.launch(headless=False)
    page = browser.new_context().new_page()
    return pw, browser, page


# --- Step 5: Hunter -----------------------------------------------------

def hunter_domain_search(domain: str) -> dict:
    """Hunter emails for a domain. Returns {'emails': [...], 'pattern': str}."""
    resp = httpx.get("https://api.hunter.io/v2/domain-search",
                      params={"domain": domain, "api_key": _key("HUNTER_API_KEY"),
                              "limit": 10},
                      timeout=30.0)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return {
        "pattern": data.get("pattern") or "",
        "emails": [{"name": " ".join(x for x in [e.get("first_name"),
                                                   e.get("last_name")] if x),
                    "title": e.get("position") or "",
                    "email": e.get("value"),
                    "confidence": e.get("confidence", 0)}
                   for e in data.get("emails", [])],
    }


def hunter_verify(email: str) -> str:
    """Return 'verified' or 'guessed' for one address. Any failure --
    HTTP error, a missing key, or a response body that is not valid JSON
    (RULING C54) -- degrades to 'guessed' rather than raising, since a
    guess is honest and a crash mid-batch is not."""
    try:
        resp = httpx.get("https://api.hunter.io/v2/email-verifier",
                          params={"email": email, "api_key": _key("HUNTER_API_KEY")},
                          timeout=30.0)
        resp.raise_for_status()
        result = resp.json().get("data", {}).get("result")
    except (httpx.HTTPError, RuntimeError, json.JSONDecodeError):
        return "guessed"
    return "verified" if result == "deliverable" else "guessed"


# --- Step 6: Apollo -------------------------------------------------------

def apollo_contact(domain: str) -> dict | None:
    """One decision-maker from Apollo for this domain. Any failure --
    HTTP error, a missing key, or a non-JSON response body (RULING C54)
    -- returns None rather than raising.

    Apollo now requires the key in the X-Api-Key header, not the JSON
    body, and the People Search path is mixed_people/api_search -- a
    live check against the account in this environment confirmed the
    older body-param /mixed_people/search form used to draft this
    module returns 422 INVALID_API_KEY_LOCATION on every call."""
    try:
        resp = httpx.post(
            "https://api.apollo.io/v1/mixed_people/api_search",
            headers={"X-Api-Key": _key("APOLLO_API_KEY")},
            json={"q_organization_domains": domain,
                  "person_titles": list(DECISION_TITLES[:8]),
                  "page": 1, "per_page": 5},
            timeout=30.0)
        resp.raise_for_status()
        people = [{"name": p.get("name"), "title": p.get("title"),
                   "email": p.get("email")}
                  for p in resp.json().get("people", []) if p.get("email")]
    except (httpx.HTTPError, RuntimeError, json.JSONDecodeError):
        return None
    return pick_best_contact(people)


def waterfall(row: dict, budget: Budget, page=None) -> dict:
    """Run the cost-ordered steps until the row is satisfied.

    `page` is an optional Playwright page for step 3 (FL Sunbiz), reused
    across a whole run by the caller. When None, step 3 is skipped --
    the same as any other state.
    """
    out = dict(row)

    # Steps 1-2: free, already on the row.
    out = seed_contact_from_row(out)

    # Step 3: FL registry lookup, free. Skipped for every other state,
    # and skipped entirely when no page was supplied.
    if not is_satisfied(out) and out.get("state") == "FL" and out.get("name") and page is not None:
        try:
            best = registry_lookup_fl(page, out["name"], out.get("city"))
            if best:
                out["contact_name"] = best["name"]
                out["contact_title"] = best.get("title", "")
        except Exception as exc:  # Cloudflare/network flake must not kill the batch
            _record_error(out, f"sunbiz: {_http_error_summary(exc)}")

    # Step 4: LinkedIn -- deliberately out of scope (Task 8).

    domain = out.get("domain")

    # Step 5: Hunter domain search plus verification.
    if not is_satisfied(out) and domain:
        try:
            found = hunter_domain_search(domain)
            best = pick_best_contact(found["emails"])
            if best:
                out["contact_name"] = best["name"]
                out["contact_title"] = best["title"]
                out["contact_email"] = best["email"]
                out["contact_email_status"] = hunter_verify(best["email"])
        except (httpx.HTTPError, RuntimeError, json.JSONDecodeError) as exc:
            _record_error(out, f"hunter: {_http_error_summary(exc)}")

    # Step 6: Apollo.
    if not is_satisfied(out) and domain:
        try:
            best = apollo_contact(domain)
            if best:
                out["contact_name"] = best["name"]
                out["contact_title"] = best["title"]
                out["contact_email"] = best["email"]
                out["contact_email_status"] = hunter_verify(best["email"])
        except (httpx.HTTPError, RuntimeError, json.JSONDecodeError) as exc:
            _record_error(out, f"apollo: {_http_error_summary(exc)}")

    # Step 7: Apify, last and cheapest actor only. Stubbed -- no
    # apify-client import, no HTTP call, zero real dollars spent. Wiring
    # a live code_crafter~leads-finder call is future work.
    if not is_satisfied(out) and budget.remaining() > 0.05:
        try:
            budget.charge(0.05)
            _record_error(out, "apify: stub only, not wired")
        except BudgetExceeded:
            _record_error(out, "apify: budget exhausted")

    # RULING C41: name and email are independent facts. An invalid name
    # (one that slipped in some other way than pick_best_contact, which
    # already filters) must not erase a perfectly good email status.
    if out.get("contact_name") and not is_valid_person_name(out["contact_name"]):
        out["contact_name"] = ""
        out["contact_title"] = ""
    return out


def main():
    """RULING C45: scored.jsonl carries reject, master and tier1 rows.
    Only tier1 rows are ever enriched (the waterfall costs money), but
    every non-reject row must reach enriched.jsonl -- everything
    downstream (hooks.py, the QA gate, the Sheet) reads that one file,
    so a master row that never gets written there is a master row that
    never ships. Reject rows are excluded on purpose: Task 13 sources
    the Rejects tab from scored.jsonl directly, not from this file.

    `--limit` bounds only the number of tier1 rows actually run through
    the waterfall in this invocation; passing a master row through
    unchanged is free and must never count against it, so a low
    --limit still lets every master row in the input reach the output
    in a single run.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=250)
    args = ap.parse_args()

    budget = Budget(config.APIFY_BUDGET_USD)
    out_path = config.DATA / "enriched.jsonl"
    # RULING C53: keyed on row_key, not a bare company_id. The old
    # `{r.get("company_id") for r in ...}` had no truthiness guard: one
    # output row with no company_id put a literal None into `already`,
    # and every later input row that also lacked one then matched that
    # None and was silently skipped forever -- never enriched, never
    # passed through, just dropped. row_key never returns a falsy value
    # (it falls back to domain, then normalized name plus state), so
    # this class of bug cannot recur.
    already = {row_key(r) for r in read_jsonl(out_path)}

    pw = browser = page = None
    enriched = 0
    try:
        for row in read_jsonl(config.DATA / "scored.jsonl"):
            if row.get("tier") == "reject":
                continue
            if row_key(row) in already:
                continue
            if row.get("tier") != "tier1":
                # Master (or any other non-reject, non-tier1 tier):
                # pass through unchanged. Free, does not touch --limit.
                append_jsonl(out_path, [row])
                continue
            if enriched >= args.limit:
                # Leave this tier1 row for a future run rather than
                # writing it unenriched or stopping the whole loop --
                # master rows further down the file still need through.
                continue
            if page is None and row.get("state") == "FL":
                pw, browser, page = open_sunbiz_page()
            result = waterfall(row, budget, page)
            append_jsonl(out_path, [result])
            enriched += 1
    finally:
        if browser is not None:
            browser.close()
        if pw is not None:
            pw.stop()

    print(f"enriched {enriched} tier1 rows, Apify spend ${budget.spent:.2f}")


if __name__ == "__main__":
    main()
