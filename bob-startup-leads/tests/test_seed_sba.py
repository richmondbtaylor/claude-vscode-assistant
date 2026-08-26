from seed_sba import row_from_7a, row_from_ppp

SEVEN_A = {
    "BorrName": "AMERIPRO CONSTRUCTION SERVICES, INC.",
    "BorrStreet": "1403 SENTRY LANE", "BorrCity": "Norristown",
    "BorrState": "PA", "BorrZip": "19403", "GrossApproval": "450000.0",
    "JobsSupported": "12", "NaicsCode": "236220",
    "NaicsDescription": "Commercial Building Construction",
    "LoanStatus": "NOT PIF", "ApprovalFY": "2024", "BusinessAge": "Existing",
}

PPP = {
    "BorrowerName": "SUMTER COATINGS, INC.", "BorrowerAddress": "2410 Highway 15 South",
    "BorrowerCity": "Sumter", "BorrowerState": "SC", "BorrowerZip": "29150-9662",
    "InitialApprovalAmount": "769358.78", "JobsReported": "62",
    "NAICSCode": "325510", "LoanStatus": "Paid in Full",
}


def test_7a_row_maps_core_fields():
    out = row_from_7a(SEVEN_A)
    assert out["name"] == "AMERIPRO CONSTRUCTION SERVICES, INC."
    assert out["state"] == "PA"
    assert out["city"] == "Norristown"
    assert out["naics"] == "236220"
    assert out["sources"] == ["sba_7a"]
    assert out["signals"]["jobs_supported"] == 12
    assert out["signals"]["loan_amount"] == 450000.0
    assert out["domain"] is None


def test_7a_row_rejected_below_jobs_floor():
    small = dict(SEVEN_A, JobsSupported="2")
    assert row_from_7a(small) is None


def test_7a_row_rejected_below_amount_floor():
    small = dict(SEVEN_A, GrossApproval="40000.0", JobsSupported="12")
    assert row_from_7a(small) is None


def test_7a_row_rejected_when_charged_off():
    dead = dict(SEVEN_A, LoanStatus="CHGOFF")
    assert row_from_7a(dead) is None


def test_7a_row_rejected_for_stale_approval_year():
    old = dict(SEVEN_A, ApprovalFY="2020")
    assert row_from_7a(old) is None


def test_ppp_row_flagged_for_liveness_check():
    out = row_from_ppp(PPP)
    assert out["sources"] == ["ppp"]
    assert out["signals"]["needs_liveness_check"] is True
    assert out["signals"]["jobs_supported"] == 62


def test_malformed_numbers_do_not_raise():
    assert row_from_7a(dict(SEVEN_A, JobsSupported="")) is None
    assert row_from_7a(dict(SEVEN_A, GrossApproval="N/A")) is None
