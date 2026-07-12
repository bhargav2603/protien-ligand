"""Active-site cluster models: parity, spins, and end-to-end study generation."""
from pathlib import Path

import pytest

from qbind import run_molecular
from qbind.chem.loader import _n_electrons, load_study
from qbind.targets import builders as B
from qbind.targets.export import write_study

_REPO = Path(__file__).parents[1]


def _parity_ok(geom):
    ne = _n_electrons(geom)
    return 0 <= geom.spin <= ne and (ne - geom.spin) % 2 == 0


@pytest.mark.parametrize("lid", ["ammonia", "methylamine", "pyridine"])
def test_p450_jobs_valid(lid):
    j = B.p450_job(lid, expt_dg=-9.0)
    assert j.fragment_a.spin == 5 and j.complex_ab.spin == 1     # spin crossover
    for g in (j.complex_ab, j.fragment_a, j.ligand_b):
        assert _parity_ok(g)


@pytest.mark.parametrize("lid", ["ammonia", "methylamine", "methanesulfonamide"])
def test_ca2_jobs_valid(lid):
    j = B.ca2_job(lid, expt_dg=-9.0)
    assert j.fragment_a.spin == 0 and j.complex_ab.spin == 0     # closed shell
    assert j.fragment_a.charge == 2
    for g in (j.complex_ab, j.fragment_a, j.ligand_b):
        assert _parity_ok(g)


def test_write_and_load_study(tmp_path):
    p = write_study("p450_azoles", tmp_path)
    spec = load_study(p)
    assert spec.ao_labels == ["Fe 3d", "Fe 4d"]
    assert len(spec.jobs) == 3
    assert (tmp_path / "pyridine.xyz").exists()


def test_run_shipped_target_studies(tmp_path):
    for key in ("p450_azoles", "ca2_sulfonamides"):
        res, rep, figs = run_molecular(tmp_path / key, backend="analytic",
                                       study_file=str(_REPO / "examples" / key / "study.json"))
        assert len(res.scores) == 3
        assert (tmp_path / key / "results" / "dashboard.html").exists()
