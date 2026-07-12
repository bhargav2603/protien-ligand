"""CLI: `python -m qbind run` or the `qbind` console script.

    qbind run                         reference pilot -> ./qbind_out (graphs + REPORT.md)
    qbind run --config c.json --out o  run a configured study
    qbind init-config path.json        write a template config to edit
"""
from __future__ import annotations

import argparse

from .config import Config


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="qbind",
                                description="SQD-corrected drug rescoring pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("run", help="reference-mode study (synthetic; graphs + report)")
    pr.add_argument("--config", default=None, help="path to a JSON config")
    pr.add_argument("--out", default="./qbind_out", help="output directory")

    pm = sub.add_parser("molecular",
                        help="molecular-cluster study on real geometries + backends")
    pm.add_argument("--backend", default="analytic",
                    choices=["analytic", "dft", "casscf", "sqd"],
                    help="correlated solver (analytic=no-deps demo)")
    pm.add_argument("--out", default="./qbind_mol", help="output directory")

    pi = sub.add_parser("init-config", help="write a template config")
    pi.add_argument("path", help="where to write the JSON config")

    args = p.parse_args(argv)

    if args.command == "init-config":
        Config().save(args.path)
        print(f"wrote template config to {args.path}")
        return

    if args.command == "molecular":
        from . import run_molecular
        result, report, figs = run_molecular(args.out, backend=args.backend)
    else:
        from . import run as run_study
        cfg = Config.load(args.config) if args.config else Config()
        result, report, figs = run_study(args.out, cfg)

    print(f"\nVERDICT: {report.verdict}")
    print(f"figures: {len(figs)} written to {args.out}/figures")
    print(f"report:  {args.out}/results/REPORT.md")


if __name__ == "__main__":
    main()
