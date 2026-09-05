"""Public HTTPS for a server on your desk, via a Cloudflare quick tunnel.

No Cloudflare account, no DNS, no port forwarding: cloudflared dials out and
Cloudflare hands back a throwaway ``*.trycloudflare.com`` hostname pointed at
the local port. The binary is a single file, so if it is missing vidforge
fetches it into ``$VIDFORGE_HOME/bin`` rather than making you go and get it.

The tunnel URL is unguessable but public - which is exactly why the server
refuses every request without a token.
"""

from __future__ import annotations

import platform
import re
import shutil
import stat
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
_RELEASE = "https://github.com/cloudflare/cloudflared/releases/latest/download"
_STARTUP_TIMEOUT = 60.0


class TunnelError(RuntimeError):
    pass


def _asset_name() -> str | None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = (
        "arm64" if machine in ("arm64", "aarch64")
        else "amd64" if machine in ("x86_64", "amd64")
        else "386" if machine in ("i386", "i686", "x86")
        else None
    )
    if arch is None:
        return None
    if system == "linux":
        return f"cloudflared-linux-{arch}"
    if system == "windows":
        return f"cloudflared-windows-{arch}.exe"
    return None  # macOS ships a .tgz; handled by the message in find_or_fetch


def find_or_fetch(home: Path, *, download: bool = True) -> Path:
    """Locate cloudflared, downloading it into ``$VIDFORGE_HOME/bin`` if needed."""
    found = shutil.which("cloudflared")
    if found:
        return Path(found)

    bindir = home / "bin"
    suffix = ".exe" if platform.system().lower() == "windows" else ""
    local = bindir / f"cloudflared{suffix}"
    if local.exists():
        return local

    asset = _asset_name()
    if not download or asset is None:
        raise TunnelError(
            "cloudflared is not installed and cannot be fetched automatically for "
            f"{platform.system()}/{platform.machine()}. Install it "
            "(macOS: `brew install cloudflared`) and run again."
        )

    bindir.mkdir(parents=True, exist_ok=True)
    tmp = local.with_suffix(local.suffix + ".part")
    print(f"vidforge: downloading cloudflared ({asset}) ...")
    try:
        with urllib.request.urlopen(f"{_RELEASE}/{asset}", timeout=120) as response:
            tmp.write_bytes(response.read())
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise TunnelError(f"could not download cloudflared: {exc}") from exc
    tmp.replace(local)
    local.chmod(local.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return local


class QuickTunnel:
    """A running ``cloudflared tunnel --url`` child process."""

    def __init__(self, port: int, home: Path, host: str = "127.0.0.1") -> None:
        self.port = port
        self.host = host
        self.home = home
        self.url: str | None = None
        self._proc: subprocess.Popen | None = None
        self._ready = threading.Event()
        self._log: list[str] = []

    def start(self, timeout: float = _STARTUP_TIMEOUT) -> str:
        binary = find_or_fetch(self.home)
        self._proc = subprocess.Popen(
            [
                str(binary), "tunnel", "--no-autoupdate",
                "--url", f"http://{self.host}:{self.port}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._pump, name="cloudflared", daemon=True).start()

        # _ready also fires when cloudflared exits, so a wait that returns
        # True still has to be checked: a binary that dies on startup (port in
        # use, egress blocked, wrong arch) must surface its log, not an
        # AssertionError.
        timed_out = not self._ready.wait(timeout)
        if self.url is None:
            self.stop()
            tail = "\n".join(self._log[-15:]) or "(cloudflared produced no output)"
            reason = f"did not report a URL within {timeout:.0f}s" if timed_out else "exited early"
            raise TunnelError(f"cloudflared {reason}:\n{tail}")
        return self.url

    def _pump(self) -> None:
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:
            self._log.append(line.rstrip())
            if self.url is None:
                match = _URL_RE.search(line)
                if match:
                    self.url = match.group(0)
                    self._ready.set()
        # cloudflared exited; unblock anyone still waiting on startup
        self._ready.set()

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def stop(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None


def qr_to_terminal(url: str) -> str | None:
    """Render a scannable QR block, or None if segno is unavailable."""
    try:
        import io

        import segno
    except ImportError:
        return None
    buffer = io.StringIO()
    segno.make(url, error="m").terminal(out=buffer, compact=True, border=2)
    return buffer.getvalue()


def wait_for_server(url: str, timeout: float = 30.0) -> bool:
    """Poll ``/healthz`` until the app answers, so we never print a dead link."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/healthz", timeout=3) as response:
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(0.4)
    return False
