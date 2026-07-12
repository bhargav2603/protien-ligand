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
    # Interactive dashboard (self-contained HTML) with a sensitivity sweep.
    from .viz import build_dashboard, sweep_reference
    swp = sweep_reference(seed=cfg.reference.seed, n_ligands=cfg.reference.n_ligands,
                          classical_noise=cfg.reference.classical_noise,
                          correlated_noise=cfg.reference.correlated_noise)
    build_dashboard(result, delta_report, r.results / "dashboard.html",
                    reference_mode=cfg.is_reference, sweep=swp)
    r.log(f"dashboard: {r.results / 'dashboard.html'}")
    return result, delta_report, figs


# Which (classical, correlated) backend pair each choice maps to. The chemistry
# settings (ao_labels/basis/xc) come from the study file and only matter to the
# real dft/casscf/sqd backends; analytic ignores them.
def _backend_pair(backend: str, *, ao_labels=("Fe 3d", "Fe 4d"),
                  basis="def2-SVP", xc="wb97x-d"):
    from .chem import backends as B
    b = backend.lower()
    if b == "analytic":       # dependency-free demo: correction = metal-coord term
        return B.AnalyticBackend(metal_pull=0.0), B.AnalyticBackend(
            name="analytic-correlated", metal_pull=0.01)
    if b == "dft":            # sanity: no correlated correction (should show ~no change)
        return B.DFTBackend(xc=xc, basis=basis), B.DFTBackend(xc=xc, basis=basis)
    if b == "casscf":         # classical correlated solver -- the real first result
        return (B.DFTBackend(xc=xc, basis=basis),
                B.CASSCFBackend(ao_labels=ao_labels, basis=basis, xc=xc))
    if b == "sqd":            # quantum solver (reuses qadv); emulate then hardware
        return (B.DFTBackend(xc=xc, basis=basis),
                B.SQDBackend(ao_labels=ao_labels, basis=basis, xc=xc))
    raise ValueError(f"unknown backend '{backend}' (analytic|dft|casscf|sqd)")


def run_molecular(outdir="./qbind_mol", backend="analytic", jobs=None, study_file=None):
    """Molecular-cluster study on real geometries with real energy backends.

    `backend`: 'analytic' (no deps, demo) | 'dft' | 'casscf' | 'sqd'.
    `study_file`: path to a study.json (real inputs). If given, it supplies the
    jobs and the chemistry (ao_labels/basis/xc). Otherwise `jobs` (or the bundled
    Fe-ligand examples) are used with default chemistry.
    Returns (StudyResult, DeltaReport, figure_paths).
    """
    from .chem import examples, study
    from .pipeline import plots, report as report_mod

    target_name, pocket = "molecular-cluster", "active-site-cluster"
    chem_kw = {}
    if study_file is not None:
        from .chem.loader import load_study
        spec = load_study(study_file)
        job_list = spec.jobs
        target_name, pocket = spec.target_name, spec.pocket
        chem_kw = dict(ao_labels=spec.ao_labels, basis=spec.basis, xc=spec.xc)
    else:
        job_list = jobs if jobs is not None else examples.example_jobs()

    classical, correlated = _backend_pair(backend, **chem_kw)
    r = Run(outdir)
    r.log(f"molecular mode: backend={backend}"
          + (f" study={study_file}" if study_file else " (bundled examples)"))
    result, delta_report = study.run_molecular_study(
        r, job_list, classical, correlated, target_name=target_name, pocket=pocket)
    figs = plots.make_all(r, result, delta_report)
    ref = (backend == "analytic")
    report_mod.generate(r, result, delta_report, figs, reference_mode=ref)
    from .viz import build_dashboard
    build_dashboard(result, delta_report, r.results / "dashboard.html", reference_mode=ref)
    r.log(f"dashboard: {r.results / 'dashboard.html'}")
    return result, delta_report, figs


def dashboard(result, report, out_path, *, reference_mode=False, sweep=None, title=None):
    """Write a self-contained interactive HTML dashboard for a study result."""
    from .viz import build_dashboard
    return build_dashboard(result, report, out_path, reference_mode=reference_mode,
                           sweep=sweep, title=title)


def sweep(biases=None, **kw):
    """Sensitivity sweep of the correlation improvement vs the reference DFT bias."""
    from .viz import sweep_reference
    return sweep_reference(**({"biases": biases} if biases else {}), **kw)


__all__ = ["Config", "ReferenceModel", "Run", "run", "run_molecular",
           "dashboard", "sweep"]
