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

# RULING C42: a marketing or support embed (HubSpot, Calendly, Freshdesk,
# Klaviyo, Podium, Drift, Intercom, and so on) supports no specific true
# statement connecting it to a bookkeeping product, so those platforms get
# no hook at all. Only platforms that actually move, hold or record a
# company's money earn a hook.
#
# RULING C44: a payment processor and an accounting ledger are not the same
# claim. "Takes payments through Xero" is false; Xero is a ledger, not a
# gateway. So the financial platforms split into two disjoint sets rather
# than one, each with its own sentence:
#   - ACCOUNTING_TECH: a ledger the company's books actually live in.
#   - PAYMENT_TECH: a processor or ecommerce checkout that moves money.
#     Ecommerce checkouts (woocommerce, shopify, bigcommerce) stay here on
#     purpose: the storefront itself processes the payment even though a
#     gateway sits behind it, so "takes payments through" still holds.
ACCOUNTING_TECH = {"quickbooks", "xero", "freshbooks", "billcom"}
PAYMENT_TECH = {
    "authorizenet", "stripe", "square", "paypal", "braintree", "clover",
    "toast", "woocommerce", "shopify", "bigcommerce",
}

# Correct capitalization for the payment/accounting platforms this stage
# names in a hook. tech.title() alone mangles multi-word or mixed-case
# brand names (woocommerce -> "Woocommerce" instead of "WooCommerce",
# billcom -> "Billcom" instead of "Bill.com"), and a hook is supposed to be
# a fact stated back to the company, so getting their own vendor's name
# wrong undercuts the one thing the hook has to get right. Platforms whose
# .title() already reads correctly (stripe, square, braintree, clover,
# toast, shopify, xero) are left out on purpose.
DISPLAY_NAME = {
    "quickbooks": "QuickBooks",
    "paypal": "PayPal",
    "woocommerce": "WooCommerce",
    "bigcommerce": "BigCommerce",
    "freshbooks": "FreshBooks",
    "billcom": "Bill.com",
    "authorizenet": "Authorize.Net",
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
    """Build the angle. Requisition first, then an accounting platform,
    then a payment processor or ecommerce checkout, then nothing.

    Each branch only asserts what the underlying signal actually supports.
    open_finance_req and job_title come from a real job posting, so naming
    the role is a fact. tech is a regex hit against an embedded script or
    widget URL on the company's own site, not proof the company "runs its
    business" on that platform.

    RULING C42: a marketing, support, booking or reputation embed (HubSpot,
    Calendly, Freshdesk, Klaviyo, Podium, and the like) supports no true
    statement connecting it to a bookkeeping product, so it earns no hook.

    RULING C44: a ledger (QuickBooks, Xero, FreshBooks, Bill.com) and a
    payment processor or ecommerce checkout are different claims and get
    different sentences. QuickBooks used to have its own hardcoded branch;
    it is now just the first entry ACCOUNTING_TECH can match, so the wording
    for every ledger platform cannot drift apart from QuickBooks by
    accident. Accounting stays ahead of payments in priority, same as
    QuickBooks outranked generic tech before this split.
    """
    sig = row.get("signals", {})
    name = row.get("name", "")

    if sig.get("open_finance_req"):
        title = (sig.get("job_title") or "").split(" at ")[0].strip() or "bookkeeper"
        return f"{name} is hiring a {title}. BOB does that work, so the req can wait."

    tech = sig.get("tech") or []

    accounting_tech = next((t for t in tech if t in ACCOUNTING_TECH), None)
    if accounting_tech:
        display = DISPLAY_NAME.get(accounting_tech, accounting_tech.title())
        return f"{name} runs {display}. BOB reads it and keeps the books straight."

    payment_tech = next((t for t in tech if t in PAYMENT_TECH), None)
    if payment_tech:
        display = DISPLAY_NAME.get(payment_tech, payment_tech.title())
        return f"{name}'s site takes payments through {display}. BOB reconciles what lands in the account."

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
