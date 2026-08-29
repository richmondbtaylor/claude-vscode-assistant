import config
import hooks as hooks_module
from hooks import ACCOUNTING_TECH, hook_for, lint_hook
from lib.records import read_jsonl, write_jsonl

JOB_ROW = {"name": "Rivera Mechanical", "city": "Austin", "state": "TX",
           "signals": {"open_finance_req": True, "job_title": "Bookkeeper at Rivera Mechanical",
                       "job_url": "https://boards.greenhouse.io/rivera/jobs/1"}}
TECH_ROW = {"name": "Summit Roofing", "city": "Denver", "state": "CO",
            "signals": {"tech": ["quickbooks", "stripe"], "jobs_supported": 30}}
BARE_ROW = {"name": "Plain Co", "city": "Tampa", "state": "FL", "signals": {}}

# RULING C42 fixtures. PAYMENT_ROW exercises the payment-processor branch
# (a checkout/gateway platform, no ledger present). NONFINANCIAL_ROW
# exercises the no-hook outcome for a marketing or support embed that has
# nothing true to say about a bookkeeping product.
PAYMENT_ROW = {"name": "Coastal Plumbing", "city": "Miami", "state": "FL",
               "signals": {"tech": ["woocommerce"], "jobs_supported": 20}}
NONFINANCIAL_ROW = {"name": "Hillside Landscaping", "city": "Raleigh", "state": "NC",
                     "signals": {"tech": ["hubspot", "calendly"]}}

# RULING C44 fixture: an accounting ledger with no payment processor in the
# tech list at all, so this exercises the accounting branch on its own,
# separate from TECH_ROW (which mixes quickbooks with stripe).
ACCOUNTING_ROW = {"name": "Beacon Electrical", "city": "Nashville", "state": "TN",
                   "signals": {"tech": ["xero"], "jobs_supported": 15}}


def test_job_row_gets_requisition_hook():
    hook = hook_for(JOB_ROW)
    assert "bookkeeper" in hook.lower()
    assert lint_hook(hook) == []


def test_tech_row_gets_stack_hook():
    hook = hook_for(TECH_ROW)
    assert "quickbooks" in hook.lower()
    assert lint_hook(hook) == []


def test_bare_row_gets_no_hook():
    assert hook_for(BARE_ROW) == ""


def test_lint_flags_em_dash():
    assert "em dash" in " ".join(lint_hook("You posted a bookkeeper role — worth a look"))


def test_lint_flags_banned_vocabulary():
    violations = lint_hook("This seamlessly and genuinely leverages your stack")
    assert len(violations) >= 2


def test_lint_flags_overlong_hook():
    long_hook = " ".join(["word"] * 40)
    assert any("too long" in v for v in lint_hook(long_hook))


# RULING C43 item 3 / RULING C44: after the financial split, every branch
# that can actually produce a hook (requisition, accounting ledger, payment
# processor) must pass its own lint, not just the two the brief originally
# covered.
def test_every_generated_hook_passes_lint():
    for row in (JOB_ROW, TECH_ROW, ACCOUNTING_ROW, PAYMENT_ROW):
        assert lint_hook(hook_for(row)) == []


# RULING C42: a marketing, support, booking or reputation platform (HubSpot
# and Calendly here) supports no true statement connecting it to a
# bookkeeping product, so it must get no hook at all, not a filler line.
def test_nonfinancial_tech_gets_no_hook():
    assert hook_for(NONFINANCIAL_ROW) == ""


def test_payment_platform_names_the_platform_and_reconciliation():
    hook = hook_for(PAYMENT_ROW)
    assert "woocommerce" in hook.lower()
    assert lint_hook(hook) == []


# RULING C44: an accounting ledger is not a payment gateway. Xero, like
# QuickBooks, gets the "runs the ledger" phrasing, never the payments
# sentence.
def test_accounting_platform_gets_ledger_hook_not_payments_hook():
    hook = hook_for(ACCOUNTING_ROW)
    assert "xero" in hook.lower()
    assert "payments" not in hook.lower()
    assert lint_hook(hook) == []


# RULING C44 regression guard: this is exactly the bug the ruling reported
# ("Acme Roofing's site takes payments through Xero" is false because Xero
# is a ledger, not a gateway). Sweep every accounting platform this stage
# can name and assert none of them ever produces the word "payments".
def test_no_accounting_platform_ever_says_payments():
    for platform in ACCOUNTING_TECH:
        row = {"name": "Test Co", "city": "Austin", "state": "TX",
               "signals": {"tech": [platform]}}
        hook = hook_for(row)
        assert "payments" not in hook.lower(), f"{platform} hook wrongly claims payments: {hook!r}"
        assert lint_hook(hook) == []


# RULING C43 item 1: this is the entire point of the lint gate in main() -
# a hook that fails lint must never reach data/hooks.jsonl, and the
# violation must be recorded on the row instead of silently dropped.
def test_main_blanks_a_lint_failing_hook_and_records_violation(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    # A payment-branch hook whose fixed template already runs ~12 words, so
    # a 15-word company name (a real, if unusual, long legal entity name)
    # pushes the generated hook past MAX_WORDS and forces a lint failure
    # through the real hook_for() branch, not a stubbed one.
    long_name = " ".join(["Word"] * 15)
    row = {"name": long_name, "city": "Austin", "state": "TX", "tier": "tier1",
           "signals": {"tech": ["stripe"]}}
    write_jsonl(tmp_path / "enriched.jsonl", [row])

    hooks_module.main()

    out = list(read_jsonl(tmp_path / "hooks.jsonl"))
    assert len(out) == 1
    assert lint_hook(hook_for(row)) != []  # sanity: the fixture really fails lint
    assert out[0]["hook"] == ""
    assert any("hook lint" in e for e in out[0].get("enrich_errors", []))


# RULING C43 item 2: a row that never reached tier1 must flow through
# main() unmodified, with no hook key added at all.
def test_main_passes_non_tier1_row_through_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    row = {"name": "Untouched Co", "city": "Tampa", "state": "FL", "tier": "master",
           "signals": {"tech": ["hubspot"]}}
    write_jsonl(tmp_path / "enriched.jsonl", [dict(row)])

    hooks_module.main()

    out = list(read_jsonl(tmp_path / "hooks.jsonl"))
    assert len(out) == 1
    assert out[0] == row
    assert "hook" not in out[0]
