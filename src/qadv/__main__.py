"""CLI entry point: `python -m qadv <command>` or the `qadv` console script.

    qadv stage0            validation (FeP, ~20q)
    qadv stage1            advantage attempt (Cpd I, >=40q)
    qadv report            regenerate REPORT.md from checkpoints
    qadv all               stage0 -> stage1 -> report

Gate/kill-criterion HALTs are caught and logged; a partial report is still
written so a stopped run still produces deliverables.
"""
from __future__ import annotations

import argparse

from . import make_context
from .pipeline import report, stage0, stage1
from .pipeline.errors import GateFailure


def _guarded(ctx, fn, name):
    try:
        fn()
    except GateFailure as g:
        ctx.log(f"GATE/KILL-CRITERION HALT in {name}: {g}", "CRITICAL")
    except Exception as e:  # never crash the whole run
        ctx.log(f"UNEXPECTED ERROR in {name}: {e}", "ERROR")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="qadv",
                                description="Autonomous SQD metalloenzyme pipeline")
    p.add_argument("command", choices=["stage0", "stage1", "report", "all"])
    p.add_argument("--proj", default=None, help="output dir (overrides $QADV_PROJ)")
    p.add_argument("--basis", default="cc-pvdz")
    p.add_argument("--no-hardware", action="store_true",
                   help="skip IBM submission; use the MPS surrogate for Stage 1")
    args = p.parse_args(argv)

    ctx = make_context(args.proj, basis=args.basis)

    if args.command in ("stage0", "all"):
        _guarded(ctx, lambda: stage0.run(ctx), "stage0")
    if args.command in ("stage1", "all"):
        _guarded(ctx, lambda: stage1.run(ctx, use_hardware=not args.no_hardware), "stage1")
    report.generate(ctx)


if __name__ == "__main__":
    main()
