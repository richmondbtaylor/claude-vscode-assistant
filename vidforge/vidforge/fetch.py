"""Downloading model files.

Kept deliberately dumb: a URL in, a file on disk out, with a progress line and
an atomic rename so an interrupted download never leaves a half-file that
looks loadable.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB
_FILENAME_RE = re.compile(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', re.I)


class DownloadError(RuntimeError):
    pass


def _name_from(response, url: str) -> str:
    disposition = response.headers.get("content-disposition", "")
    match = _FILENAME_RE.search(disposition)
    if match:
        return urllib.parse.unquote(match.group(1)).strip()
    tail = Path(urllib.parse.urlparse(url).path).name
    return tail or "download.safetensors"


def _bar(done: int, total: int, name: str) -> None:
    if total <= 0:
        sys.stdout.write(f"\r  {name}  {done / 1e6:.0f} MB")
    else:
        filled = int(24 * done / total)
        sys.stdout.write(
            f"\r  {name}  {'#' * filled}{'.' * (24 - filled)} "
            f"{done / 1e6:6.0f} / {total / 1e6:.0f} MB"
        )
    sys.stdout.flush()


def download(url: str, into: Path, *, api_key: str | None = None,
             filename: str | None = None, quiet: bool = False) -> Path:
    """Fetch ``url`` into the directory ``into``. Returns the file written."""
    if api_key:
        # Civitai and friends take the key as a query parameter on the
        # download URL rather than a header.
        parts = urllib.parse.urlparse(url)
        query = dict(urllib.parse.parse_qsl(parts.query))
        query["token"] = api_key
        url = urllib.parse.urlunparse(parts._replace(query=urllib.parse.urlencode(query)))

    into.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "vidforge"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status >= 400:
                raise DownloadError(f"{url} returned HTTP {response.status}")
            name = filename or _name_from(response, url)
            target = into / name
            if target.suffix.lower() not in (".safetensors", ".ckpt", ".pt", ".bin"):
                raise DownloadError(
                    f"refusing to save {name!r}: expected a model file "
                    "(.safetensors, .ckpt, .pt, .bin). Check the URL is the direct "
                    "download link and not the web page."
                )
            total = int(response.headers.get("content-length") or 0)
            partial = target.with_suffix(target.suffix + ".part")
            done = 0
            with partial.open("wb") as out:
                while chunk := response.read(_CHUNK):
                    out.write(chunk)
                    done += len(chunk)
                    if not quiet:
                        _bar(done, total, name)
            if not quiet:
                sys.stdout.write("\n")
    except urllib.error.HTTPError as exc:
        hint = ""
        if exc.code in (401, 403):
            hint = (" - this file needs an account. Create an API key on the site "
                    "and pass it with --api-key.")
        raise DownloadError(f"HTTP {exc.code} fetching the file{hint}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise DownloadError(f"could not fetch {url}: {exc}") from exc

    partial.replace(target)  # atomic: no half-file ever looks complete
    return target
