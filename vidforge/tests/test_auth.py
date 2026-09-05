import pytest
from fastapi.testclient import TestClient

from vidforge.api import app
from vidforge.auth import COOKIE_NAME, load_or_create_token, matches
from vidforge.service import get_context


@pytest.fixture(scope="module")
def token():
    with TestClient(app):
        return get_context().token


@pytest.fixture
def client():
    # follow_redirects off so the ?token= -> cookie hand-off is observable
    with TestClient(app, follow_redirects=False) as c:
        yield c


def test_token_is_persisted_and_stable(tmp_path):
    first = load_or_create_token(tmp_path)
    assert first and load_or_create_token(tmp_path) == first
    assert (tmp_path / "token").read_text().strip() == first


def test_env_token_overrides_the_file(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDFORGE_TOKEN", "from-the-environment")
    assert load_or_create_token(tmp_path) == "from-the-environment"


def test_matches_rejects_empty_and_wrong():
    assert matches("abc", "abc")
    assert not matches("abd", "abc")
    assert not matches("", "abc")
    assert not matches(None, "abc")


def test_api_is_closed_without_a_token(client):
    response = client.get("/api/status")
    assert response.status_code == 401
    assert response.json()["error"]


def test_browser_gets_a_login_page_not_a_json_error(client):
    response = client.get("/", headers={"accept": "text/html"})
    assert response.status_code == 401
    assert "access token" in response.text


def test_health_check_stays_open(client):
    assert client.get("/healthz").json()["ok"] is True


def test_header_token_is_accepted(client, token):
    response = client.get("/api/status", headers={"x-vidforge-token": token})
    assert response.status_code == 200


def test_bearer_token_is_accepted(client, token):
    response = client.get("/api/status", headers={"authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_query_token_redirects_and_sets_a_cookie(client, token):
    response = client.get(f"/api/status?token={token}")
    # the token is swapped for a cookie and dropped from the URL
    assert response.status_code == 303
    assert "token=" not in response.headers["location"]
    assert response.cookies.get(COOKIE_NAME) == token

    client.cookies.set(COOKIE_NAME, token)
    assert client.get("/api/status").status_code == 200


def test_wrong_token_is_rejected(client):
    assert client.get("/api/status?token=nope").status_code == 401
    assert client.get("/api/status", headers={"x-vidforge-token": "nope"}).status_code == 401


def test_generate_is_closed_too(client):
    response = client.post("/api/generate", json={"model_id": "mock", "prompt": "x"})
    assert response.status_code == 401


def test_preflight_is_answered_for_cross_origin_callers(client):
    response = client.options(
        "/api/generate",
        headers={
            "origin": "https://example.invalid",
            "access-control-request-method": "POST",
            "access-control-request-headers": "x-vidforge-token,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
