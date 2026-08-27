import pytest

from site_scrape import (classify_email, clean_emails, extract_jsonld_org,
                          extract_phone, fingerprint_tech)


def test_clean_emails_drops_asset_and_vendor_noise():
    found = {"info@acme.com", "logo@2x.png", "sentry@sentry.io",
             "a@wixpress.com", "owner@acme.com", "test@example.com"}
    assert sorted(clean_emails(found, "acme.com")) == ["info@acme.com", "owner@acme.com"]


def test_clean_emails_prefers_matching_domain():
    found = {"info@acme.com", "hello@gmail.com"}
    assert clean_emails(found, "acme.com") == ["info@acme.com"]


def test_classify_email_generic_vs_personal():
    assert classify_email("info@acme.com", "acme.com") == "generic"
    assert classify_email("sales@acme.com", "acme.com") == "generic"
    assert classify_email("maria.gonzalez@acme.com", "acme.com") == "personal"


def test_fingerprint_detects_payment_stack():
    html = ('<script src="https://js.stripe.com/v3/"></script>'
            '<script>window.Shopify={};</script>'
            '<a href="https://quickbooks.intuit.com/app">books</a>')
    assert sorted(fingerprint_tech(html)) == ["quickbooks", "shopify", "stripe"]


def test_fingerprint_returns_empty_for_plain_page():
    assert fingerprint_tech("<html><body>hello</body></html>") == []


def test_extract_jsonld_org_pulls_phone_and_address():
    html = '''<script type="application/ld+json">
    {"@type":"LocalBusiness","name":"Acme","telephone":"(512) 555-0111",
     "address":{"streetAddress":"9 Elm St","addressLocality":"Austin",
     "addressRegion":"TX","postalCode":"78701"}}</script>'''
    out = extract_jsonld_org(html)
    assert out["phone"] == "+15125550111"
    assert out["city"] == "Austin"
    assert out["state"] == "TX"


def test_extract_jsonld_org_survives_broken_json():
    assert extract_jsonld_org('<script type="application/ld+json">{oops</script>') == {}


# --- RULING C28: every TECH_PATTERNS entry gets its own positive test
# against a realistic embed, not just the three exercised above. The short
# platform names (adp, square) additionally get a negative test proving
# they do not fire on ordinary page text or unrelated URLs. A false
# positive here inflates the money score by up to 35% of that family for a
# company with no real payment stack.

PLATFORM_EMBEDS = {
    "stripe": '<script src="https://js.stripe.com/v3/"></script>',
    "shopify": '<script>window.Shopify = {};</script>',
    "square": '<script src="https://js.squareup.com/v2/paymentform"></script>',
    "quickbooks": '<a href="https://quickbooks.intuit.com/app/login">Pay Invoice</a>',
    "billcom": '<a href="https://www.bill.com/login">Pay Invoice</a>',
    "gusto": '<a href="https://gusto.com/careers">Careers powered by Gusto</a>',
    "adp": '<a href="https://workforcenow.adp.com/theme">Employee Login</a>',
    "servicetitan": '<script src="https://www.servicetitan.com/widget.js"></script>',
    "jobber": '<a href="https://getjobber.com/booking/xyz">Book Now</a>',
    "housecallpro": '<a href="https://housecallpro.com/booking">Schedule</a>',
}


@pytest.mark.parametrize("platform, html", PLATFORM_EMBEDS.items())
def test_fingerprint_detects_each_platform(platform, html):
    assert fingerprint_tech(html) == [platform]


def test_fingerprint_adp_no_false_positive_on_ordinary_text():
    html = "<p>We install ADP-rated backflow preventers on every job.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_square_no_false_positive_on_place_name():
    html = "<p>Located near Beacon Square Plaza in downtown Austin.</p>"
    assert fingerprint_tech(html) == []


# --- RULING C26: phone extraction order is tel: href, then a digit run
# near a phone label, then a bare match; reject a candidate immediately
# preceded by a license/invoice/order/PO/EIN label.

def test_extract_phone_prefers_tel_href_over_bare_match():
    html = '<a href="tel:+15125550111">Call</a> Invoice #512-555-0199 due now.'
    assert extract_phone(html) == "+15125550111"


def test_extract_phone_prefers_labeled_over_bare():
    html = "Order #512-555-0100 shipped. Phone: 512-555-0111 for questions."
    assert extract_phone(html) == "+15125550111"


def test_extract_phone_rejects_license_number():
    html = "License #512-555-0199. Call our office for details."
    assert extract_phone(html) is None


def test_extract_phone_bare_fallback_when_no_label():
    html = "Reach us anytime: 512-555-0123"
    assert extract_phone(html) == "+15125550123"


def test_extract_phone_returns_none_for_no_candidates():
    assert extract_phone("<html><body>no numbers here</body></html>") is None
