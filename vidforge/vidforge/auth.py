"""Token auth.

The moment vidforge is reachable from a phone it is reachable from whatever
else is on that network - or, with a tunnel, from the internet. So the server
is never open: a token is generated on first run and every request needs it.

Three ways to present it, in the order a client would:

* ``?token=...``      - the link you scan or paste; sets a cookie and redirects
* ``X-Vidforge-Token`` - API clients and cross-origin callers
* ``vidforge_token`` cookie - the browser, after that first visit
"""

from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path

COOKIE_NAME = "vidforge_token"
HEADER_NAME = "x-vidforge-token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Reachable without a token: a liveness probe that reveals nothing, and the
# handful of static assets the login redirect itself needs.
PUBLIC_PATHS = frozenset({"/healthz"})


def load_or_create_token(home: Path) -> str:
    """Read ``$VIDFORGE_HOME/token``, creating it on first run.

    ``VIDFORGE_TOKEN`` overrides, so a deployment can inject its own.
    """
    override = os.environ.get("VIDFORGE_TOKEN", "").strip()
    if override:
        return override

    path = home / "token"
    if path.exists():
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    token = secrets.token_urlsafe(24)
    home.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass  # windows / odd filesystems
    return token


def matches(candidate: str | None, token: str) -> bool:
    """Constant-time compare, so the token cannot be guessed a byte at a time."""
    if not candidate:
        return False
    return hmac.compare_digest(candidate, token)


def presented_token(request) -> str | None:  # noqa: ANN001 - starlette Request
    """Pull a token out of a request, whichever way it was presented."""
    header = request.headers.get(HEADER_NAME)
    if header:
        return header.strip()

    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    query = request.query_params.get("token")
    if query:
        return query.strip()

    return request.cookies.get(COOKIE_NAME)
