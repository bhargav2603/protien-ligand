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
    """Reference-mode study (synthetic): scores, delta report, graphs, REPORT.md.

    Returns (StudyResult, DeltaReport, figure_paths).
    """
    from .pipeline import orchestrator, plots, report as report_mod

    cfg = config or Config()
    r = Run(outdir)
    result, delta_report = orchestrator.run_study(r, cfg)
    figs = plots.make_all(r, result, delta_report)
    report_mod.generate(r, result, delta_report, figs, reference_mode=cfg.is_reference)
    return result, delta_report, figs


# Which (classical, correlated) backend pair each choice maps to.
def _backend_pair(backend: str):
    from .chem import backends as B
    b = backend.lower()
    if b == "analytic":       # dependency-free demo: correction = metal-coord term
        return B.AnalyticBackend(metal_pull=0.0), B.AnalyticBackend(
            name="analytic-correlated", metal_pull=0.01)
    if b == "dft":            # sanity: no correlated correction (should show ~no change)
        return B.DFTBackend(), B.DFTBackend()
    if b == "casscf":         # classical correlated solver -- the real first result
        return B.DFTBackend(), B.CASSCFBackend()
    if b == "sqd":            # quantum solver (reuses qadv); emulate then hardware
        return B.DFTBackend(), B.SQDBackend()
    raise ValueError(f"unknown backend '{backend}' (analytic|dft|casscf|sqd)")


def run_molecular(outdir="./qbind_mol", backend="analytic", jobs=None):
    """Molecular-cluster study on real geometries with real energy backends.

    `backend`: 'analytic' (no deps, demo) | 'dft' | 'casscf' | 'sqd'.
    `jobs`: list of chem.interaction.InteractionJob (defaults to the bundled
    Fe-ligand example clusters). Returns (StudyResult, DeltaReport, figure_paths).
    """
    from .chem import examples, study
    from .pipeline import plots, report as report_mod

    classical, correlated = _backend_pair(backend)
    r = Run(outdir)
    r.log(f"molecular mode: backend={backend}")
    job_list = jobs if jobs is not None else examples.example_jobs()
    result, delta_report = study.run_molecular_study(r, job_list, classical, correlated)
    figs = plots.make_all(r, result, delta_report)
    report_mod.generate(r, result, delta_report, figs, reference_mode=(backend == "analytic"))
    return result, delta_report, figs


__all__ = ["Config", "ReferenceModel", "Run", "run", "run_molecular"]
