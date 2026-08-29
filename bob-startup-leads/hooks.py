"""One-line outreach angle per Tier 1 row, built from that company's own material."""
import re

import config
from lib.records import read_jsonl, write_jsonl

# AI-tell filler vocabulary. Anything here reads as machine-written, not as
# an operator describing a fact.
BANNED = {
    "actually", "genuinely", "seamless", "seamlessly", "leverage", "leverages",
    "robust", "cutting-edge", "game-changer", "unlock", "delve", "elevate",
    "streamline", "supercharge", "revolutionize", "transformative",
}
MAX_WORDS = 25
_MIRROR = re.compile(r"\bnot\s+\w+[,;]?\s+but\s+\w+", re.I)

# Correct capitalization for the tech fingerprints this stage names in a
# hook. tech[0].title() alone mangles multi-word or mixed-case brand names
# (woocommerce -> "Woocommerce" instead of "WooCommerce"), and a hook is
# supposed to be a fact stated back to the company, so getting their own
# vendor's name wrong undercuts the one thing the hook has to get right.
# Only covers platforms this stage actually names (quickbooks explicitly,
# plus the others verified present in real scraped data).
DISPLAY_NAME = {
    "quickbooks": "QuickBooks",
    "woocommerce": "WooCommerce",
    "hubspot": "HubSpot",
    "calendly": "Calendly",
    "authorizenet": "Authorize.Net",
    "podium": "Podium",
    "freshdesk": "Freshdesk",
    "klaviyo": "Klaviyo",
}


def lint_hook(text: str) -> list[str]:
    """Return copy-rule violations. Empty list means the hook can ship."""
    problems = []
    if "—" in text or "--" in text:
        problems.append("em dash present")
    words = re.findall(r"[a-z'-]+", text.lower())
    for word in words:
        if word in BANNED:
            problems.append(f"banned word: {word}")
    if len(words) > MAX_WORDS:
        problems.append(f"too long: {len(words)} words")
    if _MIRROR.search(text):
        problems.append("mirrored two-beat construction")
    return problems


def hook_for(row: dict) -> str:
    """Build the angle. Requisition first, then QuickBooks specifically,
    then any other detected tech, then nothing.

    Each branch only asserts what the underlying signal actually supports.
    open_finance_req and job_title come from a real job posting, so naming
    the role is a fact. tech is a regex hit against an embedded script or
    widget URL on the company's own site, not proof the company "runs its
    business" on that platform, so the copy stays to what a widget on the
    page actually shows: the site uses it.
    """
    sig = row.get("signals", {})
    name = row.get("name", "")

    if sig.get("open_finance_req"):
        title = (sig.get("job_title") or "").split(" at ")[0].strip() or "bookkeeper"
        return f"{name} is hiring a {title}. BOB does that work, so the req can wait."

    tech = sig.get("tech") or []
    if "quickbooks" in tech:
        return f"{name} runs QuickBooks. BOB reads it and handles the bills around it."
    if tech:
        display = DISPLAY_NAME.get(tech[0], tech[0].title())
        return f"{name}'s site runs {display}. BOB keeps the books straight either way."

    return ""


def main():
    rows = []
    processed = 0
    written = 0
    blanked = 0
    for row in read_jsonl(config.DATA / "enriched.jsonl"):
        if row.get("tier") == "tier1":
            processed += 1
            hook = hook_for(row)
            problems = lint_hook(hook) if hook else []
            if problems:
                row["hook"] = ""
                row.setdefault("enrich_errors", []).append(f"hook lint: {problems}")
                blanked += 1
            else:
                row["hook"] = hook
                if hook:
                    written += 1
        rows.append(row)

    print(f"{processed} tier1 rows, {written} hooks written, {blanked} blanked by lint")
    write_jsonl(config.DATA / "hooks.jsonl", rows)


if __name__ == "__main__":
    main()
