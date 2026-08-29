from hooks import hook_for, lint_hook

JOB_ROW = {"name": "Rivera Mechanical", "city": "Austin", "state": "TX",
           "signals": {"open_finance_req": True, "job_title": "Bookkeeper at Rivera Mechanical",
                       "job_url": "https://boards.greenhouse.io/rivera/jobs/1"}}
TECH_ROW = {"name": "Summit Roofing", "city": "Denver", "state": "CO",
            "signals": {"tech": ["quickbooks", "stripe"], "jobs_supported": 30}}
BARE_ROW = {"name": "Plain Co", "city": "Tampa", "state": "FL", "signals": {}}


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


def test_every_generated_hook_passes_lint():
    for row in (JOB_ROW, TECH_ROW):
        assert lint_hook(hook_for(row)) == []
