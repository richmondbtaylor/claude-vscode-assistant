import sys

import pytest

import config
import site_scrape
from lib.records import read_jsonl, row_key, write_jsonl
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


# --- RULING C29: TECH_PATTERNS expanded from 10 to 43 platforms across
# payments, ecommerce, paid marketing/CRM, support, booking, field
# service, payroll/HR, accounting and reviews. Same C28 discipline: every
# new pattern gets a positive test against a realistic embed; the ordinary-
# English-word names (drift, toast, clover, podium, acuity) additionally
# get a negative test.

NEW_PLATFORM_EMBEDS = {
    "paypal": '<a href="https://www.paypal.com/paypalme/example">Pay with PayPal</a>',
    "braintree": '<script src="https://js.braintreegateway.com/web/dropin/1.33.7/js/dropin.min.js"></script>',
    "authorizenet": '<script src="https://js.authorize.net/v1/Accept.js"></script>',
    "clover": '<script src="https://checkout.clover.com/sdk.js"></script>',
    "toast": '<a href="https://order.toasttab.com/online/example-restaurant">Order Online</a>',
    "helcim": '<script src="https://secure.helcim.com/js/helcim.js"></script>',
    "bigcommerce": '<link rel="stylesheet" href="https://cdn11.bigcommerce.com/theme.css">',
    "woocommerce": '<body class="woocommerce woocommerce-page">',
    "hubspot": '<script src="https://js.hs-scripts.com/123456.js"></script>',
    "salesforce": '<a href="https://mycompany.my.salesforce.com/login">Client Portal</a>',
    "pardot": '<script src="https://pi.pardot.com/pd.js"></script>',
    "marketo": '<script src="https://app-abc.marketo.com/js/forms2/forms2.min.js"></script>',
    "activecampaign": '<script src="https://example123.activehosted.com/f/1.js"></script>',
    "klaviyo": '<script src="https://static.klaviyo.com/onsite/js/klaviyo.js"></script>',
    "mailchimp": '<a href="https://mycompany.list-manage.com/subscribe">Subscribe</a>',
    "constantcontact": '<a href="https://visitor.constantcontact.com/d.jsp?m=abc">Subscribe</a>',
    "zendesk": '<script src="https://static.zdassets.com/ekr/snippet.js"></script>',
    "intercom": '<script src="https://widget.intercom.io/widget/abc123"></script>',
    "freshdesk": '<script src="https://mycompany.freshdesk.com/widget.js"></script>',
    "drift": '<script src="https://js.driftt.com/include/12345/abc.js"></script>',
    "calendly": '<a href="https://calendly.com/example/30min">Book a call</a>',
    "acuity": '<a href="https://app.acuityscheduling.com/schedule.php?owner=123">Book Now</a>',
    "mindbody": '<script src="https://widgets.mindbodyonline.com/widgets/schedules/123.js"></script>',
    "workiz": '<script src="https://app.workiz.com/booking-widget.js"></script>',
    "fieldedge": '<a href="https://www.fieldedge.com/login">Field Tech Login</a>',
    "paychex": '<a href="https://www.paychex.com/login">Employee Login</a>',
    "bamboohr": '<a href="https://mycompany.bamboohr.com/jobs/">Careers</a>',
    "rippling": '<a href="https://app.rippling.com/login">Employee Portal</a>',
    "xero": '<a href="https://www.xero.com/uk/pay/12345">Pay Invoice via Xero</a>',
    "freshbooks": '<a href="https://my.freshbooks.com/#/estimate/abc">View Estimate</a>',
    "birdeye": '<script src="https://birdeye.com/widget.js"></script>',
    "podium": '<script src="https://webchat.podium.com/widget.js"></script>',
    "nicejob": '<a href="https://nicejob.co/r/mycompany">Leave us a review</a>',
}


@pytest.mark.parametrize("platform, html", NEW_PLATFORM_EMBEDS.items())
def test_fingerprint_detects_each_new_platform(platform, html):
    assert fingerprint_tech(html) == [platform]


def test_fingerprint_drift_no_false_positive_on_ordinary_text():
    html = "<p>Watch for roof drift after heavy wind storms.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_toast_no_false_positive_on_ordinary_text():
    html = "<p>We'll toast to your new roof at the completion party.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_clover_no_false_positive_on_ordinary_text():
    html = "<p>Our clover lawn seed mix keeps your yard green year round.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_podium_no_false_positive_on_ordinary_text():
    html = "<p>The award-winning contractor stood on the podium at the gala.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_acuity_no_false_positive_on_ordinary_text():
    html = "<p>Our inspectors have the visual acuity to catch every missing shingle.</p>"
    assert fingerprint_tech(html) == []


def test_fingerprint_xero_no_false_positive_on_similar_domain():
    html = '<a href="https://www.flexero.com/careers">Careers at Flexero</a>'
    assert fingerprint_tech(html) == []


def test_fingerprint_excluded_platforms_never_tracked():
    """RULING C29: WordPress, Wix, Squarespace, GoDaddy and Webflow are
    deliberately excluded. A website builder is not evidence money moves."""
    html = ('<link rel="stylesheet" href="https://mysite.wordpress.com/wp-content/theme.css">'
            '<script src="https://static.wixstatic.com/site.js"></script>'
            '<img src="https://images.squarespace-cdn.com/logo.png">'
            '<a href="https://www.godaddy.com">Domains by GoDaddy</a>'
            '<meta name="generator" content="Webflow">')
    assert fingerprint_tech(html) == []


# --- RULING C30: clean_emails also drops template placeholder addresses,
# URL-encoding artifacts, and local parts that are purely numeric or a
# single character. Each closes a real gap found in the previous live run.

def test_clean_emails_drops_placeholder_localparts():
    found = {"email@acme.com", "youremail@acme.com", "name@acme.com",
             "example@acme.com", "yourname@acme.com", "owner@acme.com"}
    assert clean_emails(found, "acme.com") == ["owner@acme.com"]


def test_clean_emails_drops_placeholder_domains():
    found = {"info@company.com", "info@yourcompany.com", "info@yourdomain.com",
             "info@roofingcompany.com"}
    # "roofingcompany.com" is a real registrable domain that happens to end
    # in "company.com" -- must survive an exact rhs match, not a substring one.
    assert clean_emails(found, "roofingcompany.com") == ["info@roofingcompany.com"]


def test_clean_emails_drops_url_encoding_artifact():
    found = {"%20office@acme.com", "owner@acme.com"}
    assert clean_emails(found, "acme.com") == ["owner@acme.com"]


def test_clean_emails_drops_numeric_and_single_char_localparts():
    found = {"2@gmail.com", "789@gmail.com", "a@gmail.com", "owner@acme.com"}
    assert clean_emails(found, "acme.com") == ["owner@acme.com"]


# --- RULING C31: the license/invoice/order/PO/EIN reject list also
# applies to tel: hrefs, and a tel: link in a contact region is preferred
# over one that reads as a footer design credit, even when the credit
# link appears earlier in the document.

def test_extract_phone_rejects_tel_href_preceded_by_license_label():
    html = 'License: <a href="tel:+15125550199">Call</a>'
    assert extract_phone(html) is None


def test_extract_phone_prefers_contact_tel_over_earlier_footer_credit_tel():
    html = ('<footer>Site by <a href="tel:+15125550100">WebCo</a></footer>'
            '<div class="contact">Call us: <a href="tel:+15125550199">(512) 555-0199</a></div>')
    assert extract_phone(html) == "+15125550199"


# --- RULING C53: resume must key on row_key (company_id, falling back to
# domain, then normalized name plus state), not a bare company_id. The
# old `done_ids = {row.get("company_id") for row in ... if row.get(
# "company_id")}` filtered OUT any idless row from the done-set, so an
# idless row already sitting in sites.jsonl was never recognized as
# already scraped and got rescraped on every resumed run.

def test_main_resume_skips_a_row_already_scraped_even_without_company_id(
        tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    row = {"company_id": None, "name": "Acme Roofing", "domain": "acmeroofing.com",
           "website": "https://acmeroofing.com", "state": "TX"}
    write_jsonl(tmp_path / "resolved.jsonl", [row])
    write_jsonl(tmp_path / "sites.jsonl", [row])  # already scraped, no id on it

    calls = []
    monkeypatch.setattr(site_scrape, "scrape_row", lambda r: (calls.append(r) or r))
    monkeypatch.setattr(sys, "argv", ["site_scrape.py"])

    site_scrape.main(limit=None, workers=1)

    assert calls == []  # resume recognized it as done -- no rescrape
    out = list(read_jsonl(tmp_path / "sites.jsonl"))
    assert len(out) == 1  # not duplicated either


def test_main_resume_distinguishes_two_idless_rows_by_domain(tmp_path, monkeypatch):
    # Two different, idless companies must not collide on resume just
    # because neither has a company_id -- row_key falls back to domain,
    # which differs here, so both get scraped independently.
    monkeypatch.setattr(config, "DATA", tmp_path)
    row_a = {"company_id": None, "name": "Acme Roofing", "domain": "acmeroofing.com",
             "website": "https://acmeroofing.com", "state": "TX"}
    row_b = {"company_id": None, "name": "Summit HVAC", "domain": "summithvac.com",
             "website": "https://summithvac.com", "state": "CO"}
    write_jsonl(tmp_path / "resolved.jsonl", [row_a, row_b])
    write_jsonl(tmp_path / "sites.jsonl", [row_a])  # only A already scraped

    calls = []
    monkeypatch.setattr(site_scrape, "scrape_row", lambda r: (calls.append(r["name"]) or r))
    monkeypatch.setattr(sys, "argv", ["site_scrape.py"])

    site_scrape.main(limit=None, workers=1)

    assert calls == ["Summit HVAC"]  # only the un-scraped one ran


# --- RULING C56: a successful site fetch is direct evidence a PPP-sourced
# company is still trading, giving a standalone PPP row (one that never
# merged with a Maps or current 7(a) record in dedupe.py) an actual path
# to liveness confirmation. Only a genuine successful fetch clears the
# flag; a failed fetch must leave it exactly as it was.

def _fake_scrape_result(pages_fetched: int) -> dict:
    return {"emails": [], "phone": None, "tech": [], "has_pricing_page": False,
            "has_careers_page": False, "pages_fetched": pages_fetched}


def test_scrape_row_clears_liveness_flag_on_a_successful_fetch(monkeypatch):
    monkeypatch.setattr(site_scrape, "scrape_domain", lambda url, domain: _fake_scrape_result(3))
    row = {"domain": "acmeroofing.com", "website": "https://acmeroofing.com",
           "signals": {"needs_liveness_check": True}}

    out = site_scrape.scrape_row(row)

    assert out["signals"]["needs_liveness_check"] is False


def test_scrape_row_keeps_liveness_flag_on_a_failed_fetch(monkeypatch):
    monkeypatch.setattr(site_scrape, "scrape_domain", lambda url, domain: _fake_scrape_result(0))
    row = {"domain": "deadcompany.test", "website": "https://deadcompany.test",
           "signals": {"needs_liveness_check": True}}

    out = site_scrape.scrape_row(row)

    assert out["signals"]["needs_liveness_check"] is True


def test_scrape_row_does_not_invent_a_liveness_key_on_a_row_that_never_had_one(monkeypatch):
    # A Maps-sourced row (or any row never flagged for liveness) must not
    # gain a needs_liveness_check key just because its site fetched fine
    # -- that key means something specific (a PPP row with no current
    # evidence) and must not be manufactured for rows that never asked.
    monkeypatch.setattr(site_scrape, "scrape_domain", lambda url, domain: _fake_scrape_result(2))
    row = {"domain": "mapsco.com", "website": "https://mapsco.com",
           "signals": {"reviews": 5}}

    out = site_scrape.scrape_row(row)

    assert "needs_liveness_check" not in out["signals"]
