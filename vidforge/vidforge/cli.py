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
from .prompts import load_prompt_file
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


def _submit(args: argparse.Namespace, prompts: list[str]) -> int:
    ctx = get_context()
    request = SubmitRequest(
        model_id=args.model,
        prompts=prompts,
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
def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    ctx = get_context()
    host = args.host or ctx.settings.host
    port = args.port or ctx.settings.port
    print(f"vidforge -> http://{host}:{port}   (home: {ctx.settings.home})")
    uvicorn.run("vidforge.api:app", host=host, port=port, log_level="info")
    return 0


def cmd_gen(args: argparse.Namespace) -> int:
    return _submit(args, [args.prompt])


def cmd_batch(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    prompts = load_prompt_file(path)
    if not prompts:
        print(f"error: no prompts found in {path}", file=sys.stderr)
        return 2
    print(f"loaded {len(prompts)} prompt(s) from {path}")
    return _submit(args, prompts)


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
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(func=cmd_serve)

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
    add_gen_flags(batch)
    batch.set_defaults(func=cmd_batch)

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
