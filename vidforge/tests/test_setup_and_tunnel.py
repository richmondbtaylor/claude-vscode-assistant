"""Machine detection, install-command selection, and tunnel plumbing.

Nothing here touches the network or installs anything; the pieces that would
are exercised through their pure inputs and outputs.
"""

from __future__ import annotations

import pytest

from vidforge.bootstrap import Machine, doctor_json, recommend, report, torch_install
from vidforge.tunnel import QuickTunnel, TunnelError, _URL_RE, _asset_name, find_or_fetch


def machine(**kwargs) -> Machine:
    base = {"system": "Linux", "machine": "x86_64", "python": "3.11.0"}
    base.update(kwargs)
    return Machine(**base)


# --- install selection -----------------------------------------------------
def test_nvidia_gets_the_cuda_wheel_index():
    args = torch_install(machine(vendor="nvidia"))
    assert "download.pytorch.org/whl/cu124" in " ".join(args)


def test_amd_gets_rocm():
    assert "rocm" in " ".join(torch_install(machine(vendor="amd")))


def test_apple_uses_the_default_wheel():
    # MPS support ships in the PyPI build; an index override would break it.
    assert torch_install(machine(vendor="apple")) == ["torch"]


def test_no_accelerator_gets_the_cpu_wheel():
    assert "whl/cpu" in " ".join(torch_install(machine()))


# --- model recommendation --------------------------------------------------
@pytest.mark.parametrize(
    "vram,expected",
    [(24, "wan-14b"), (16, "wan-i2v"), (12, "ltx"), (8, "wan-1_3b")],
)
def test_recommendation_follows_available_vram(vram, expected):
    assert recommend(machine(vendor="nvidia", vram_gb=vram))[0] == expected


def test_a_card_too_small_for_anything_falls_back_to_mock():
    assert recommend(machine(vendor="nvidia", vram_gb=4))[0] == "mock"


def test_no_gpu_falls_back_to_mock():
    assert recommend(machine())[0] == "mock"


# --- reporting -------------------------------------------------------------
def test_report_flags_a_cpu_only_torch_on_a_gpu_box():
    info = machine(vendor="nvidia", device_name="RTX 4090", vram_gb=24,
                   torch_version="2.5.0+cpu", torch_accelerated=False,
                   notes=["a nvidia device is present but torch cannot see it"])
    text = report(info)
    assert "RTX 4090" in text and "24 GB" in text
    assert "torch cannot see it" in text
    assert not info.ready


def test_a_working_gpu_box_reports_ready():
    assert machine(vendor="nvidia", vram_gb=24, torch_version="2.5.0+cu124",
                   torch_accelerated=True).ready


def test_a_cpu_box_with_torch_is_ready_too():
    # No accelerator to miss, so nothing is broken - mock still renders.
    assert machine(torch_version="2.5.0+cpu").ready


def test_doctor_json_is_machine_readable():
    import json

    payload = json.loads(doctor_json(machine(vendor="nvidia", vram_gb=24)))
    assert payload["suggested_model"] == "wan-14b"
    assert payload["vendor"] == "nvidia"


# --- tunnel ----------------------------------------------------------------
def test_quick_tunnel_url_is_recognised_in_cloudflared_output():
    line = "2026-01-01 INF |  https://odd-forest-1234.trycloudflare.com  |"
    assert _URL_RE.search(line).group(0) == "https://odd-forest-1234.trycloudflare.com"


def test_unrelated_urls_are_not_mistaken_for_the_tunnel():
    assert _URL_RE.search("visit https://example.com/trycloudflare") is None


@pytest.mark.parametrize(
    "system,machine_name,expected",
    [
        ("linux", "x86_64", "cloudflared-linux-amd64"),
        ("linux", "aarch64", "cloudflared-linux-arm64"),
        ("windows", "AMD64", "cloudflared-windows-amd64.exe"),
        ("darwin", "arm64", None),  # ships as a tgz; we point at brew instead
    ],
)
def test_asset_name_per_platform(monkeypatch, system, machine_name, expected):
    monkeypatch.setattr("platform.system", lambda: system)
    monkeypatch.setattr("platform.machine", lambda: machine_name)
    assert _asset_name() == expected


def test_find_or_fetch_explains_itself_rather_than_downloading_blindly(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: None)
    with pytest.raises(TunnelError, match="cloudflared"):
        find_or_fetch(tmp_path, download=False)


def test_find_or_fetch_prefers_an_installed_binary(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/local/bin/cloudflared")
    assert str(find_or_fetch(tmp_path)) == "/usr/local/bin/cloudflared"


def test_a_tunnel_binary_that_dies_on_startup_reports_why(tmp_path, monkeypatch):
    # /bin/true exits immediately without printing a URL - the same shape as a
    # cloudflared that cannot bind, cannot reach the edge, or is the wrong arch.
    monkeypatch.setattr("shutil.which", lambda _name: "/bin/true")
    tunnel = QuickTunnel(port=1, home=tmp_path)
    with pytest.raises(TunnelError, match="exited early"):
        tunnel.start(timeout=5.0)
    assert not tunnel.alive


def test_a_tunnel_that_hangs_without_a_url_times_out(tmp_path, monkeypatch):
    import stat

    stalled = tmp_path / "stalled-cloudflared"
    stalled.write_text("#!/bin/sh\necho 'connecting...'\nsleep 30\n")
    stalled.chmod(stalled.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr("shutil.which", lambda _name: str(stalled))

    tunnel = QuickTunnel(port=1, home=tmp_path)
    with pytest.raises(TunnelError, match="did not report a URL"):
        tunnel.start(timeout=1.5)
    assert not tunnel.alive
