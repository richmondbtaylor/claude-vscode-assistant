"""Editing models.toml, and the download guard rails."""

from __future__ import annotations

import tomllib

import pytest

from vidforge.fetch import DownloadError, _name_from, download
from vidforge.registry import add_model, clone_with_loras, remove_model

HEADER = "# vidforge model registry\n# edit this, not the code\n\n"


def seeded(tmp_path):
    path = tmp_path / "models.toml"
    path.write_text(
        HEADER
        + '[model.wan-1_3b]\nbackend = "diffusers"\nkind = "t2v"\n'
        'label = "Wan 2.1 T2V 1.3B"\nrepo = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"\n'
        'pipeline_class = "WanPipeline"\n\n'
        "[model.wan-1_3b.defaults]\nwidth = 832\nheight = 480\n"
    )
    return path


# --- registry --------------------------------------------------------------
def test_adding_a_model_keeps_the_existing_ones(tmp_path):
    path = seeded(tmp_path)
    add_model(path, "ltx", {"backend": "diffusers", "kind": "t2v", "repo": "Lightricks/LTX-Video"})
    data = tomllib.loads(path.read_text())
    assert set(data["model"]) == {"wan-1_3b", "ltx"}
    assert data["model"]["wan-1_3b"]["defaults"]["width"] == 832


def test_the_header_comments_survive_a_write(tmp_path):
    path = seeded(tmp_path)
    add_model(path, "ltx", {"backend": "mock"})
    assert path.read_text().startswith("# vidforge model registry")


def test_a_backup_is_kept(tmp_path):
    path = seeded(tmp_path)
    add_model(path, "ltx", {"backend": "mock"})
    assert (tmp_path / "models.toml.bak").exists()


def test_adding_over_an_existing_id_is_refused_unless_forced(tmp_path):
    path = seeded(tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        add_model(path, "wan-1_3b", {"backend": "mock"})
    add_model(path, "wan-1_3b", {"backend": "mock"}, overwrite=True)
    assert tomllib.loads(path.read_text())["model"]["wan-1_3b"]["backend"] == "mock"


def test_removing_a_model(tmp_path):
    path = seeded(tmp_path)
    assert remove_model(path, "wan-1_3b") is True
    assert remove_model(path, "wan-1_3b") is False


# --- LoRA stacking ---------------------------------------------------------
def test_stacking_a_lora_leaves_the_base_untouched(tmp_path):
    path = seeded(tmp_path)
    clone_with_loras(path, "wan-1_3b", "wan-style",
                     [{"repo": "/loras/style.safetensors", "weight": 0.8, "name": "style"}])
    models = tomllib.loads(path.read_text())["model"]
    assert "loras" not in models["wan-1_3b"]          # the plain model still exists
    assert models["wan-style"]["repo"] == models["wan-1_3b"]["repo"]
    assert models["wan-style"]["loras"][0]["weight"] == 0.8
    assert "style" in models["wan-style"]["label"]


def test_stacking_onto_an_entry_that_already_has_loras_appends(tmp_path):
    path = seeded(tmp_path)
    clone_with_loras(path, "wan-1_3b", "one",
                     [{"repo": "/a.safetensors", "weight": 1.0, "name": "a"}])
    clone_with_loras(path, "one", "two",
                     [{"repo": "/b.safetensors", "weight": 0.5, "name": "b"}])
    loras = tomllib.loads(path.read_text())["model"]["two"]["loras"]
    assert [lora["name"] for lora in loras] == ["a", "b"]


def test_stacking_onto_a_missing_base_names_what_is_available(tmp_path):
    path = seeded(tmp_path)
    with pytest.raises(KeyError, match="wan-1_3b"):
        clone_with_loras(path, "nope", "x", [{"repo": "/a.safetensors"}])


# --- downloads -------------------------------------------------------------
class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


def test_filename_comes_from_content_disposition():
    class R:
        headers = FakeHeaders({"content-disposition": 'attachment; filename="style_v2.safetensors"'})
    assert _name_from(R(), "https://x/api/download/models/123") == "style_v2.safetensors"


def test_filename_falls_back_to_the_url_tail():
    class R:
        headers = FakeHeaders({})
    assert _name_from(R(), "https://x/files/thing.safetensors") == "thing.safetensors"


def test_a_web_page_is_not_saved_as_a_model(tmp_path, monkeypatch):
    # Pasting the Civitai page URL instead of the download link is the most
    # likely mistake; saving 40 KB of HTML as a .safetensors would fail later
    # and much more confusingly.
    import io
    import urllib.request

    class Response(io.BytesIO):
        status = 200
        headers = FakeHeaders({"content-disposition": 'filename="model-page.html"'})
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Response(b"<html>"))
    with pytest.raises(DownloadError, match="direct download link"):
        download("https://civitai.com/models/123", tmp_path, quiet=True)


def test_a_model_file_is_written_atomically(tmp_path, monkeypatch):
    import io
    import urllib.request

    payload = b"\x00" * 4096

    class Response(io.BytesIO):
        status = 200
        headers = FakeHeaders({"content-disposition": 'filename="good.safetensors"',
                               "content-length": str(len(payload))})
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Response(payload))
    written = download("https://x/d", tmp_path, quiet=True)
    assert written.name == "good.safetensors"
    assert written.read_bytes() == payload
    assert not list(tmp_path.glob("*.part"))  # no half-file left behind


def test_an_api_key_is_attached_to_the_url(tmp_path, monkeypatch):
    import io
    import urllib.request

    seen = {}

    class Response(io.BytesIO):
        status = 200
        headers = FakeHeaders({"content-disposition": 'filename="k.safetensors"'})
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(request, **kwargs):
        seen["url"] = request.full_url
        return Response(b"x")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    download("https://civitai.com/api/download/models/9", tmp_path,
             api_key="secret", quiet=True)
    assert "token=secret" in seen["url"]
