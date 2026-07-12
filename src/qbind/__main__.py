"""CLI: `python -m qbind <command>` or the `qbind` console script.

    qbind input [--file input.json]    THE MAIN ENTRY: run whatever input.json says
    qbind run    [--config c.json]     reference-mode study (synthetic)
    qbind molecular [--study s.json]   molecular-cluster study (real geometries)
    qbind init-config path.json        write a template reference config

`qbind input` is the one-file workflow: edit input.json, rerun. The others are
direct shortcuts for the same underlying study modes.
"""
from __future__ import annotations

import argparse

from .config import Config


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="qbind",
                                description="SQD-corrected drug rescoring pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    pin = sub.add_parser("input", help="run the study described by input.json (main entry)")
    pin.add_argument("--file", default="input.json", help="path to the input file")
    pin.add_argument("--out", default=None, help="override output_dir from the input file")

    pr = sub.add_parser("run", help="reference-mode study (synthetic; graphs + report)")
    pr.add_argument("--config", default=None, help="path to a JSON config")
    pr.add_argument("--out", default="./qbind_out", help="output directory")

    pm = sub.add_parser("molecular",
                        help="molecular-cluster study on real geometries + backends")
    pm.add_argument("--backend", default="analytic",
                    choices=["analytic", "dft", "casscf", "sqd"],
                    help="correlated solver (analytic=no-deps demo)")
    pm.add_argument("--study", default=None,
                    help="path to a study.json (real inputs); omit for bundled examples")
    pm.add_argument("--out", default="./qbind_mol", help="output directory")

    pi = sub.add_parser("init-config", help="write a template reference config")
    pi.add_argument("path", help="where to write the JSON config")

    args = p.parse_args(argv)

    if args.command == "init-config":
        Config().save(args.path)
        print(f"wrote template config to {args.path}")
        return

    if args.command == "input":
        from .input_spec import RunInput
        spec = RunInput.load(args.file)
        if args.out:
            spec.output_dir = args.out
        out = spec.output_dir
        result, report, figs = spec.execute()
    elif args.command == "molecular":
        from . import run_molecular
        out = args.out
        result, report, figs = run_molecular(out, backend=args.backend,
                                             study_file=args.study)
    else:
        from . import run as run_study
        out = args.out
        cfg = Config.load(args.config) if args.config else Config()
        result, report, figs = run_study(out, cfg)

    print(f"\nVERDICT: {report.verdict}")
    print(f"figures: {len(figs)} written to {out}/figures")
    print(f"report:  {out}/results/REPORT.md")


if __name__ == "__main__":
    main()
