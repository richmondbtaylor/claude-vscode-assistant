from seed_maps import fresh_only, place_to_record

PLACE = {
    "name": "Castillo Smart Services LLC",
    "phone": "+17863958578",
    "website": "https://castillosmart.com/",
    "address": "20350 S Dixie Hwy Suite 202, Cutler Bay, FL 33189",
    "category": "Tax preparation service",
    "rating": 5.0,
    "reviews": 64,
    "fid": "0x88d9c3bfcfd1779f:0xd76c7e2bc2664dd4",
}


def test_place_maps_to_canonical_record():
    out = place_to_record(PLACE, "bookkeeping service", "Miami FL")
    assert out["name"] == "Castillo Smart Services LLC"
    assert out["phone"] == "+17863958578"
    assert out["domain"] == "castillosmart.com"
    assert out["state"] == "FL"
    assert out["zip"] == "33189"
    assert out["signals"]["reviews"] == 64
    assert out["sources"] == ["maps"]


def test_place_without_phone_or_site_is_rejected():
    bare = dict(PLACE, phone=None, website=None)
    assert place_to_record(bare, "q", "Miami FL") is None


def test_social_url_does_not_become_domain():
    social = dict(PLACE, website="https://facebook.com/castillo")
    out = place_to_record(social, "q", "Miami FL")
    assert out["domain"] is None
    assert out["phone"] == "+17863958578"


def test_address_without_parseable_state_still_records():
    odd = dict(PLACE, address="20350 S Dixie Hwy")
    out = place_to_record(odd, "q", "Miami FL")
    assert out["state"] == "FL"  # falls back to the search city


def test_resume_skips_everything_already_seen():
    # A re-run of the same metro/category cell rediscovers the same
    # feature-ids; this is the sole gate that must empty out so the run
    # appends nothing for places already recorded (C14).
    links = {"fid1": {"href": "a"}, "fid2": {"href": "b"}}
    seen = {"fid1", "fid2"}
    assert fresh_only(links, seen) == {}


def test_resume_keeps_only_unseen_fids():
    links = {"fid1": {"href": "a"}, "fid2": {"href": "b"}}
    seen = {"fid1"}
    assert fresh_only(links, seen) == {"fid2": {"href": "b"}}
