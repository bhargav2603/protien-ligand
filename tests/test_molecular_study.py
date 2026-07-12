"""End-to-end molecular pipeline with the analytic backend (no pyscf needed)."""
from qbind import run_molecular
from qbind.chem import examples
from qbind.chem.backends import AnalyticBackend
from qbind.chem.interaction import interaction_energy


def test_example_jobs_shape():
    jobs = examples.example_jobs()
    assert len(jobs) == 8
    for j in jobs:
        # AB must contain fragment + ligand atoms
        assert len(j.complex_ab.atoms) == len(j.fragment_a.atoms) + len(j.ligand_b.atoms)
        assert j.experimental_dg is not None


def test_interaction_energy_units():
    b = AnalyticBackend(metal_pull=1.0)
    job = examples.example_jobs()[0]
    kcal = interaction_energy(b, job, unit="kcal")
    ha = interaction_energy(b, job, unit="ha")
    assert abs(kcal - ha * 627.5094740631) < 1e-6


def test_molecular_run_produces_graphs_and_report(tmp_path):
    result, report, figs = run_molecular(tmp_path, backend="analytic")
    assert len(result.scores) == 8
    assert (tmp_path / "results" / "REPORT.md").exists()
    # correlation-improvement + ranking + per-ligand-delta + 2 scatter = 5 (no fragment fig)
    assert len(figs) == 5
    assert report.correlation_improvement is not None    # illustrative expt present


def test_correlated_backend_moves_coordinating_ligands(tmp_path):
    # analytic-correlated adds a metal-coordination stabilisation -> nonzero deltas
    result, report, _ = run_molecular(tmp_path, backend="analytic")
    assert any(abs(s.delta) > 1e-6 for s in result.scores)
    assert report.quantum_changed_ranking
