"""qbind -- SQD-corrected rescoring of drugs against a metalloenzyme pocket.

Quick start (reference/pilot mode, no external tools):

    import qbind
    result, report, figs = qbind.run("./out")          # runs + graphs + REPORT.md
    print(report.verdict)

Real study: build a Config selecting vina/pyscf/sqd stages and a benchmark CSV,
then wire the adapters in classical/docking.py and qm/*.
"""
from __future__ import annotations

from .config import Config, ReferenceModel
from .runtime import Run


def run(outdir="./qbind_out", config=None):
    """Run a study end-to-end: scores, delta report, graphs, REPORT.md.

    Returns (StudyResult, DeltaReport, figure_paths).
    """
    from .pipeline import orchestrator, plots, report as report_mod

    cfg = config or Config()
    r = Run(outdir)
    result, delta_report = orchestrator.run_study(r, cfg)
    figs = plots.make_all(r, result, delta_report)
    report_mod.generate(r, result, delta_report, figs, reference_mode=cfg.is_reference)
    return result, delta_report, figs


__all__ = ["Config", "ReferenceModel", "Run", "run"]
