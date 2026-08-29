import pytest

from enrich_tier1 import (Budget, BudgetExceeded, is_satisfied,
                           pick_best_contact, seed_contact_from_row, waterfall)


def test_row_with_verified_named_contact_is_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is True


def test_row_with_guessed_email_is_not_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "guessed"}
    assert is_satisfied(row) is False


def test_row_with_junk_name_is_not_satisfied():
    row = {"contact_name": "Get Ah", "contact_email": "info@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is False


def test_pick_best_contact_prefers_decision_maker_titles():
    people = [
        {"name": "Sam Reed", "title": "Marketing Intern", "email": "sam@acme.com"},
        {"name": "Maria Gonzalez", "title": "Owner", "email": "maria@acme.com"},
        {"name": "Lee Park", "title": "Technician", "email": "lee@acme.com"},
    ]
    assert pick_best_contact(people)["name"] == "Maria Gonzalez"


def test_pick_best_contact_rejects_invalid_names():
    people = [{"name": "Contact Us", "title": "Owner", "email": "info@acme.com"}]
    assert pick_best_contact(people) is None


def test_budget_blocks_spend_over_ceiling():
    budget = Budget(limit_usd=0.05)
    budget.charge(0.04)
    with pytest.raises(BudgetExceeded):
        budget.charge(0.03)


def test_budget_reports_remaining():
    budget = Budget(limit_usd=10.0)
    budget.charge(2.5)
    assert budget.remaining() == pytest.approx(7.5)


# RULING C9: steps 1-2 seed contact_* from data already on the row (free)
# before anything paid runs. These pin down that behaviour.

def test_seed_contact_from_row_uses_personal_email_as_guessed_candidate():
    row = {"email": "maria.gonzalez@acme.com", "email_status": "personal", "phone": "+15125550111"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "maria.gonzalez@acme.com"
    assert out["contact_email_status"] == "guessed"


def test_seed_contact_from_row_uses_generic_email_as_generic_status():
    row = {"email": "info@acme.com", "email_status": "generic"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "info@acme.com"
    assert out["contact_email_status"] == "generic"


def test_seed_contact_from_row_never_labels_a_seeded_email_verified():
    row = {"email": "maria.gonzalez@acme.com", "email_status": "personal"}
    out = seed_contact_from_row(row)
    assert out["contact_email_status"] != "verified"


def test_seed_contact_from_row_skips_when_no_email_on_row():
    row = {"email": None, "email_status": "none", "phone": "+15125550111"}
    out = seed_contact_from_row(row)
    assert "contact_email" not in out
    assert out["contact_phone"] == "+15125550111"


def test_seed_contact_from_row_does_not_overwrite_existing_contact():
    row = {"email": "info@acme.com", "email_status": "generic",
           "contact_email": "maria@acme.com", "contact_email_status": "verified"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "maria@acme.com"
    assert out["contact_email_status"] == "verified"


def test_seed_contact_from_row_seeds_phone_from_maps():
    row = {"phone": "+13055550199"}
    out = seed_contact_from_row(row)
    assert out["contact_phone"] == "+13055550199"


def test_seed_contact_from_row_preserves_all_other_fields():
    row = {"company_id": "abc123", "name": "Acme LLC", "state": "FL",
           "email": "info@acme.com", "email_status": "generic"}
    out = seed_contact_from_row(row)
    assert out["company_id"] == "abc123"
    assert out["name"] == "Acme LLC"
    assert out["state"] == "FL"


# The waterfall must never crash a whole batch when a key is missing --
# money-safety demands the row comes back with an error noted, not a
# stack trace that kills every row after it.

def test_waterfall_survives_missing_hunter_and_apollo_keys(monkeypatch):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)
    monkeypatch.setattr("enrich_tier1.SECURITY", pytest.importorskip("pathlib").Path("no/such/dir"))
    row = {"company_id": "x1", "name": "Acme LLC", "domain": "acme-example-nonexistent.test",
           "state": "TX"}
    budget = Budget(limit_usd=0.0)
    out = waterfall(row, budget)
    assert out["company_id"] == "x1"
    assert not is_satisfied(out)
    assert out.get("enrich_errors")
