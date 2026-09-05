"""Command line front end.

    vidforge serve
    vidforge gen "a neon-lit alley in the rain" --model wan-t2v --variants 4
    vidforge batch prompts.jsonl --model wan-t2v --variants 2
    vidforge models | jobs | wildcards | check "..." | consent ...

``gen`` and ``batch`` are the headless path for an external prompt generator:
pipe it a file of prompts and it renders the whole sweep.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .guardrails import GuardrailError, check as guard_check
from .prompts import load_prompt_items
from .schemas import GenParams, SubmitRequest
from .service import get_context


def _params(args: argparse.Namespace) -> GenParams:
    return GenParams(
        width=args.width,
        height=args.height,
        num_frames=args.frames,
        fps=args.fps,
        steps=args.steps,
        guidance_scale=args.cfg,
        negative_prompt=args.negative or "",
        init_image=args.init_image,
    )


def _watch(ctx, batch_id: str) -> int:
    """Block until every job in the batch is terminal; return an exit code."""
    ctx.start()
    done: set[str] = set()
    while True:
        jobs = ctx.db.list(batch_id=batch_id, limit=500)
        for job in jobs:
            if job.terminal and job.id not in done:
                done.add(job.id)
                if job.status == "done":
                    print(f"  [done]   {job.output_path}")
                else:
                    print(f"  [{job.status}] {job.prompt[:60]!r}: {job.error or ''}")
        if len(done) == len(jobs):
            break
        running = next((j for j in jobs if j.status == "running"), None)
        if running:
            bar = int(running.progress * 24)
            print(
                f"\r  rendering {'#' * bar}{'.' * (24 - bar)} {running.progress:5.0%}",
                end="", flush=True,
            )
        time.sleep(1.0)
    print()
    failed = sum(1 for j in ctx.db.list(batch_id=batch_id, limit=500) if j.status == "failed")
    print(f"batch {batch_id}: {len(done) - failed} rendered, {failed} failed")
    return 1 if failed else 0


def _submit(args: argparse.Namespace, prompts: list[str],
            items: list[dict] | None = None) -> int:
    ctx = get_context()
    request = SubmitRequest(
        model_id=args.model,
        prompts=prompts,
        items=items or [],
        params=_params(args),
        variants=args.variants,
        seeds=args.seed or [],
        expand_wildcards=not args.no_wildcards,
        identity_reference=args.identity_reference,
        consent_id=args.consent_id,
        label=args.label or "",
    )
    try:
        batch_id, jobs = ctx.submit(request)
    except GuardrailError as exc:
        print(f"refused: {exc.verdict.message}", file=sys.stderr)
        if exc.verdict.matched:
            print(f"  matched: {', '.join(exc.verdict.matched)}", file=sys.stderr)
        return 2
    except (KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"queued {len(jobs)} job(s) as batch {batch_id}")
    if args.no_wait:
        return 0
    return _watch(ctx, batch_id)


# --- commands --------------------------------------------------------------
def _local_ip() -> str:
    """The LAN address of this machine, for the link you open on a phone."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("10.255.255.255", 1))  # no packets sent; just picks a route
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def _announce(label: str, url: str, token: str, qr: bool) -> None:
    from .tunnel import qr_to_terminal

    link = f"{url}/?token={token}"
    print(f"\n  {label}\n  {link}")
    if qr:
        block = qr_to_terminal(link)
        if block:
            print(block)


def cmd_serve(args: argparse.Namespace) -> int:
    import threading

    import uvicorn

    ctx = get_context()
    host = args.host or ctx.settings.host
    port = args.port or ctx.settings.port
    # A tunnel is pointless if the app only listens on loopback for itself, but
    # cloudflared connects locally, so 127.0.0.1 is still correct there.
    if args.tunnel and not args.host:
        host = "127.0.0.1"

    tunnel = None
    if args.tunnel:
        from .tunnel import QuickTunnel, TunnelError, wait_for_server

        def _open_tunnel() -> None:
            nonlocal tunnel
            if not wait_for_server(f"http://127.0.0.1:{port}", timeout=45):
                print("vidforge: server did not come up; skipping tunnel")
                return
            try:
                tunnel = QuickTunnel(port=port, home=ctx.settings.home)
                url = tunnel.start()
            except TunnelError as exc:
                print(f"vidforge: tunnel unavailable: {exc}")
                return
            _announce("Public (phone, anywhere):", url, ctx.token, qr=not args.no_qr)

        threading.Thread(target=_open_tunnel, name="vidforge-tunnel", daemon=True).start()

    print(f"vidforge  home: {ctx.settings.home}")
    _announce("This machine:", f"http://127.0.0.1:{port}", ctx.token, qr=False)
    if host == "0.0.0.0":  # noqa: S104 - deliberate, and the token gates it
        _announce("Same wifi (phone):", f"http://{_local_ip()}:{port}", ctx.token,
                  qr=not args.no_qr)
    print(f"\n  access token: {ctx.token}\n")

    try:
        uvicorn.run("vidforge.api:app", host=host, port=port, log_level="warning")
    finally:
        if tunnel is not None:
            tunnel.stop()
    return 0


def cmd_token(args: argparse.Namespace) -> int:
    ctx = get_context()
    if args.reset:
        (ctx.settings.home / "token").unlink(missing_ok=True)
        from .auth import load_or_create_token

        print(load_or_create_token(ctx.settings.home))
        print("(restart `vidforge serve` to use it)")
        return 0
    print(ctx.token)
    return 0


def cmd_gen(args: argparse.Namespace) -> int:
    return _submit(args, [args.prompt])


def cmd_batch(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    items = load_prompt_items(path)
    if not items:
        print(f"error: no prompts found in {path}", file=sys.stderr)
        return 2

    # A file that already carries seeds and settings is a resolved batch:
    # render it exactly as composed rather than re-rolling it.
    resolved = [i for i in items if "seed" in i or i["params"]]
    if resolved and not args.expand:
        detail = f"{len(resolved)} with their own seed/settings"
        print(f"loaded {len(items)} clip(s) from {path} ({detail})")
        return _submit(args, [], items=items)

    print(f"loaded {len(items)} prompt(s) from {path}")
    return _submit(args, [i["prompt"] for i in items])


def cmd_models(_args: argparse.Namespace) -> int:
    ctx = get_context()
    if not ctx.settings.models:
        print("no models registered; edit", ctx.settings.models_file)
        return 0
    width = max(len(m.id) for m in ctx.settings.models.values())
    for spec in sorted(ctx.settings.models.values(), key=lambda s: s.id):
        print(f"{spec.id:<{width}}  {spec.backend:<9} {spec.kind:<4} {spec.repo or spec.workflow or ''}")
    return 0


def cmd_jobs(args: argparse.Namespace) -> int:
    ctx = get_context()
    for job in ctx.db.list(status=args.status, limit=args.limit):
        stamp = (job.created_at or "")[:19]
        print(f"{stamp}  {job.status:<9} {job.id[:8]}  seed={job.seed:<12} {job.prompt[:60]}")
    counts = ctx.db.counts()
    print("  ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "(no jobs)")
    return 0


def cmd_wildcards(_args: argparse.Namespace) -> int:
    ctx = get_context()
    table = ctx.wildcards()
    if not table:
        print(f"no wildcard files in {ctx.settings.wildcards_dir}")
        return 0
    for name, values in sorted(table.items()):
        print(f"__{name}__  {len(values)} entries")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    ctx = get_context()
    verdict = guard_check(
        args.prompt,
        identity_reference=args.identity_reference,
        consent_id=args.consent_id,
        consent_store=ctx.consent,
    )
    if verdict.allowed:
        print("allowed")
        return 0
    print(f"refused [{verdict.code}]: {verdict.message}")
    if verdict.matched:
        print(f"matched: {', '.join(verdict.matched)}")
    return 2


def cmd_consent(args: argparse.Namespace) -> int:
    ctx = get_context()
    if args.consent_cmd == "list":
        records = ctx.consent.list()
        if not records:
            print("no consent records")
        for record in records:
            print(f"{record['id']}  {record['subject']}  attested by {record['attested_by']} "
                  f"on {record['attested_at']}")
        return 0
    if args.consent_cmd == "add":
        record = ctx.consent.add(args.subject, args.attested_by, args.note or "")
        print(f"added {record['id']} for {record['subject']}")
        return 0
    if args.consent_cmd == "remove":
        ok = ctx.consent.remove(args.id)
        print("removed" if ok else "no such record")
        return 0 if ok else 2
    return 2


def cmd_doctor(args: argparse.Namespace) -> int:
    from .bootstrap import detect, doctor_json, report

    info = detect()
    if args.json:
        print(doctor_json(info))
    else:
        print("vidforge doctor\n")
        print(report(info))
        print()
        if not info.ready:
            print("  run `vidforge setup` to fix the above")
    return 0 if info.ready else 1


def cmd_setup(args: argparse.Namespace) -> int:
    from .bootstrap import detect, install, prefetch, recommend, report

    info = detect()
    print("vidforge setup\n")
    print(report(info))

    model_id = args.model or recommend(info)[0]
    if info.vendor == "none" and not args.force:
        print(
            "\n  No GPU here, so there is nothing worth installing: torch on CPU will\n"
            "  technically run a video model but a single clip takes hours. The mock\n"
            "  model already works. Re-run with --force to install anyway."
        )
        return 0

    print("\ninstalling")
    code = install(info, dry=args.dry_run)
    if code != 0:
        print("\n  install failed - see the output above")
        return code

    if not args.no_download:
        print(f"\nprefetching weights for {model_id}")
        prefetch(model_id, get_context().settings, dry=args.dry_run)

    print("\ndone. next:")
    print(f"  vidforge gen \"a rain-slicked alley at night\" --model {model_id}")
    print("  vidforge serve --tunnel        # phone link + QR code")
    return 0


def cmd_lora(args: argparse.Namespace) -> int:
    """Put a LoRA on disk and register a model that loads it."""
    from .fetch import DownloadError, download
    from .registry import clone_with_loras

    ctx = get_context()

    if args.lora_cmd == "list":
        stacked = [s for s in ctx.settings.models.values() if s.loras]
        if not stacked:
            print("no models stack a LoRA yet; add one with `vidforge lora add <file>`")
            return 0
        for spec in sorted(stacked, key=lambda s: s.id):
            names = ", ".join(
                f"{lora.get('name') or '?'}@{lora.get('weight', 1.0)}" for lora in spec.loras
            )
            print(f"{spec.id:<24} {names}")
        return 0

    source = args.source

    if source.startswith(("http://", "https://")):
        into = ctx.settings.home / "loras"
        print(f"downloading into {into}")
        try:
            path = download(source, into, api_key=args.api_key, filename=args.filename)
        except DownloadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        path = Path(source).expanduser().resolve()
        if not path.exists():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2

    name = args.name or path.stem.replace(" ", "-").lower()
    new_id = args.id or f"{args.base}-{name}"
    lora = {"repo": str(path), "weight": args.weight, "name": name}
    try:
        entry = clone_with_loras(ctx.settings.models_file, args.base, new_id,
                                 [lora], overwrite=args.force)
    except (KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"\nregistered {new_id}")
    print(f"  base    {args.base} ({entry.get('repo') or entry.get('workflow')})")
    print(f"  lora    {path.name} @ {args.weight}")
    print(f"\ntry it:\n  vidforge gen \"your prompt\" --model {new_id} --variants 4")
    return 0


def cmd_comfy(args: argparse.Namespace) -> int:
    ctx = get_context()

    if args.comfy_cmd == "status":
        from .backends import BackendUnavailable, get_backend

        backend = get_backend("comfyui", ctx.settings)
        try:
            backend.preflight()
        except BackendUnavailable as exc:
            print(f"not reachable: {exc}")
            return 1
        print(f"ComfyUI is up at {ctx.settings.comfy_url}")
        try:
            import httpx

            with httpx.Client(base_url=ctx.settings.comfy_url, timeout=20) as client:
                nodes = client.get("/object_info").json()
            print(f"  {len(nodes)} node types installed")
            for wanted in ("VHS_VideoCombine", "SaveAnimatedWEBP", "WanImageToVideo",
                           "EmptyHunyuanLatentVideo"):
                print(f"  {'yes' if wanted in nodes else 'no ':<4} {wanted}")
        except Exception as exc:  # a node listing failure is not fatal
            print(f"  (could not list nodes: {exc})")
        return 0

    if args.comfy_cmd == "import":
        from .comfy_import import ImportError_, import_workflow
        from .registry import add_model

        source = Path(args.file).expanduser()
        if not source.exists():
            print(f"error: no such file: {source}", file=sys.stderr)
            return 2
        destination = ctx.settings.home / "workflows" / f"{args.name}.json"
        try:
            report = import_workflow(source, destination)
        except ImportError_ as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(f"wrote {destination}\n")
        print("vidforge will now drive these fields:")
        for line in report.changes:
            print(line)
        for warning in report.warnings:
            print(f"\n  warning: {warning}")

        try:
            add_model(ctx.settings.models_file, args.name, {
                "backend": "comfyui", "kind": args.kind,
                "label": f"ComfyUI - {args.name}",
                "workflow": f"workflows/{args.name}.json",
                "defaults": {"width": 832, "height": 480, "num_frames": 81,
                             "fps": 16, "steps": 25, "guidance_scale": 6.0},
            }, overwrite=args.force)
        except ValueError as exc:
            print(f"\nnote: {exc}")
        else:
            print(f"\nregistered model {args.name}")
        print(f"\ntry it:\n  vidforge gen \"your prompt\" --model {args.name}")
        return 0 if not report.warnings else 1

    return 2


def cmd_config(_args: argparse.Namespace) -> int:
    ctx = get_context()
    print(json.dumps({
        "home": str(ctx.settings.home),
        "models_file": str(ctx.settings.models_file),
        "outputs": str(ctx.settings.outputs_dir),
        "wildcards": str(ctx.settings.wildcards_dir),
        "device": ctx.settings.device,
        "comfy_url": ctx.settings.comfy_url,
        "models": sorted(ctx.settings.models),
    }, indent=2))
    return 0


# --- parser ----------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vidforge", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the web UI and API")
    serve.add_argument("--host", help="0.0.0.0 to reach it from a phone on the same wifi")
    serve.add_argument("--port", type=int)
    serve.add_argument("--tunnel", action="store_true",
                       help="also expose a public HTTPS URL via a Cloudflare quick tunnel")
    serve.add_argument("--no-qr", action="store_true", help="do not print a QR code")
    serve.set_defaults(func=cmd_serve)

    token = sub.add_parser("token", help="print the access token")
    token.add_argument("--reset", action="store_true", help="generate a new one")
    token.set_defaults(func=cmd_token)

    def add_gen_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--model", default="mock")
        p.add_argument("--negative", default="")
        p.add_argument("--variants", type=int, default=1,
                       help="random seeds per prompt (ignored if --seed is given)")
        p.add_argument("--seed", type=int, action="append",
                       help="explicit seed; repeatable")
        p.add_argument("--width", type=int)
        p.add_argument("--height", type=int)
        p.add_argument("--frames", type=int)
        p.add_argument("--fps", type=int)
        p.add_argument("--steps", type=int)
        p.add_argument("--cfg", type=float, help="guidance scale")
        p.add_argument("--init-image", dest="init_image", help="file in VIDFORGE_HOME/uploads")
        p.add_argument("--no-wildcards", action="store_true")
        p.add_argument("--no-wait", action="store_true", help="queue and exit")
        p.add_argument("--label", default="")
        p.add_argument("--identity-reference", dest="identity_reference", action="store_true",
                       help="the init image is a real person's face (requires --consent-id)")
        p.add_argument("--consent-id", dest="consent_id")

    gen = sub.add_parser("gen", help="render one prompt (or a wildcard sweep of it)")
    gen.add_argument("prompt")
    add_gen_flags(gen)
    gen.set_defaults(func=cmd_gen)

    batch = sub.add_parser("batch", help="render a .txt/.json/.jsonl file of prompts")
    batch.add_argument("file")
    batch.add_argument("--expand", action="store_true",
                       help="treat the file as templates, ignoring any seeds it carries")
    add_gen_flags(batch)
    batch.set_defaults(func=cmd_batch)

    setup = sub.add_parser("setup", help="detect this machine and install what it needs")
    setup.add_argument("--model", help="model to prefetch (default: whatever fits)")
    setup.add_argument("--no-download", action="store_true", help="skip fetching weights")
    setup.add_argument("--dry-run", action="store_true", help="print commands, run nothing")
    setup.add_argument("--force", action="store_true", help="install even with no GPU")
    setup.set_defaults(func=cmd_setup)

    # `lora add` rather than a bare `lora <file>`, to match `consent add`.
    lora = sub.add_parser("lora", help="add a LoRA and register a model that uses it")
    lsub = lora.add_subparsers(dest="lora_cmd", required=True)
    add = lsub.add_parser("add", help="download or register a LoRA file")
    add.add_argument("source", help="a local .safetensors path, or a direct download URL")
    add.add_argument("--base", default="wan-1_3b", help="model to stack it on")
    add.add_argument("--weight", type=float, default=0.9)
    add.add_argument("--name", help="adapter name (default: the filename)")
    add.add_argument("--id", help="id for the new model (default: <base>-<name>)")
    add.add_argument("--filename", help="save the download under this name")
    add.add_argument("--api-key", dest="api_key",
                     help="site API key, for files behind a login")
    add.add_argument("--force", action="store_true", help="replace an existing entry")
    lsub.add_parser("list", help="show models that stack a LoRA")
    lora.set_defaults(func=cmd_lora)

    comfy = sub.add_parser("comfy", help="work with a running ComfyUI")
    csub = comfy.add_subparsers(dest="comfy_cmd", required=True)
    csub.add_parser("status", help="check the connection and the installed nodes")
    imp = csub.add_parser("import", help="turn a Save (API Format) export into a workflow")
    imp.add_argument("file")
    imp.add_argument("--name", default="comfy-wan", help="model id to register")
    imp.add_argument("--kind", default="t2v", choices=("t2v", "i2v"))
    imp.add_argument("--force", action="store_true")
    comfy.set_defaults(func=cmd_comfy)

    doctor = sub.add_parser("doctor", help="report what this machine can run")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    sub.add_parser("models", help="list the model registry").set_defaults(func=cmd_models)
    sub.add_parser("wildcards", help="list wildcard files").set_defaults(func=cmd_wildcards)
    sub.add_parser("config", help="show resolved configuration").set_defaults(func=cmd_config)

    jobs = sub.add_parser("jobs", help="list recent jobs")
    jobs.add_argument("--status")
    jobs.add_argument("--limit", type=int, default=20)
    jobs.set_defaults(func=cmd_jobs)

    check = sub.add_parser("check", help="dry-run the guardrails against a prompt")
    check.add_argument("prompt")
    check.add_argument("--identity-reference", dest="identity_reference", action="store_true")
    check.add_argument("--consent-id", dest="consent_id")
    check.set_defaults(func=cmd_check)

    consent = sub.add_parser("consent", help="manage likeness consent records")
    csub = consent.add_subparsers(dest="consent_cmd", required=True)
    csub.add_parser("list")
    add = csub.add_parser("add")
    add.add_argument("--subject", required=True)
    add.add_argument("--attested-by", dest="attested_by", required=True)
    add.add_argument("--note", default="")
    remove = csub.add_parser("remove")
    remove.add_argument("id")
    consent.set_defaults(func=cmd_consent)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
