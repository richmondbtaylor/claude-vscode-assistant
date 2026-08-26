import json

import seed_maps
from lib.records import read_jsonl
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


# --- end-to-end resume check: a second run() of the same cell must append
# nothing, given the seen_ids.json a clean first run() left behind (C14). ---

_FEED = {
    "0xAAA:0x111": {"href": "https://maps.example/place/a", "name": "A Roofing"},
    "0xBBB:0x222": {"href": "https://maps.example/place/b", "name": "B Roofing"},
}

_PLACES_BY_HREF = {
    "https://maps.example/place/a": {
        "name": "A Roofing", "phone": "+13055551201",
        "website": "https://aroofing.com/",
        "address": "1 Main St, Miami, FL 33101",
        "category": "Roofing contractor", "rating": 4.8, "reviews": 20,
    },
    "https://maps.example/place/b": {
        "name": "B Roofing", "phone": "+13055551202",
        "website": "https://broofing.com/",
        "address": "2 Main St, Miami, FL 33101",
        "category": "Roofing contractor", "rating": 4.2, "reviews": 5,
    },
}


class _FakePage:
    def goto(self, *a, **k):
        pass

    def wait_for_selector(self, *a, **k):
        pass


class _FakeContext:
    def new_page(self):
        return _FakePage()


class _FakeBrowser:
    def new_context(self, **k):
        return _FakeContext()

    def close(self):
        pass


class _FakeChromium:
    def launch(self, **k):
        return _FakeBrowser()


class _FakeSyncPlaywright:
    chromium = _FakeChromium()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_rerun_of_same_cell_appends_nothing_once_seen(tmp_path, monkeypatch):
    out = tmp_path / "seed_maps.jsonl"
    seen_path = tmp_path / "seen_ids.json"
    monkeypatch.setattr(seed_maps, "OUT", out)
    monkeypatch.setattr(seed_maps, "SEEN_PATH", seen_path)
    monkeypatch.setattr(seed_maps, "sync_playwright", lambda: _FakeSyncPlaywright())
    monkeypatch.setattr(seed_maps, "scroll_feed", lambda page, max_scrolls=10: dict(_FEED))
    monkeypatch.setattr(seed_maps, "scrape_place",
                         lambda page, href: dict(_PLACES_BY_HREF[href]))
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)

    seed_maps.run(["roofing contractor"], ["Miami FL"])
    first_records = list(read_jsonl(out))
    first_seen = json.loads(seen_path.read_text())
    assert len(first_records) == 2
    assert len(first_seen) == 2

    # Second run of the identical cell: scroll_feed rediscovers the same
    # feed, but seen_ids.json (written by the first run) already covers
    # both feature-ids, so nothing new should be scraped or appended.
    seed_maps.run(["roofing contractor"], ["Miami FL"])
    second_records = list(read_jsonl(out))
    assert second_records == first_records  # file did not grow or duplicate
