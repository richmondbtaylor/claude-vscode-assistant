from site_scrape import classify_email, clean_emails, extract_jsonld_org, fingerprint_tech


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
