"""Study-file loader: JSON+xyz -> InteractionJobs, with parity validation."""
import json

import pytest

from qbind.chem.loader import load_study


def _write_study(tmp_path, spins_complex=4, extra=None):
    (tmp_path / "Fe-CO.xyz").write_text(
        "3\nFe-CO\nFe 0 0 0\nC 0 0 2.0\nO 0 0 3.13\n", encoding="utf-8")
    lig = {
        "ligand_id": "CO",
        "complex_xyz": "Fe-CO.xyz",
        "fragment_atoms": [0],
        "ligand_atoms": None,
        "charges": {"fragment": 0, "ligand": 0, "complex": 0},
        "spins": {"fragment": 4, "ligand": 0, "complex": spins_complex},
        "experimental_dg": -12.0,
    }
    if extra:
        lig.update(extra)
    doc = {
        "target_name": "T", "pocket": "P",
        "chemistry": {"basis": "def2-SVP", "xc": "wb97x-d", "ao_labels": ["Fe 3d"]},
        "ligands": [lig],
    }
    p = tmp_path / "study.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_load_study_builds_jobs(tmp_path):
    spec = load_study(_write_study(tmp_path))
    assert spec.target_name == "T"
    assert spec.ao_labels == ["Fe 3d"]
    assert len(spec.jobs) == 1
    job = spec.jobs[0]
    assert job.fragment_a.elements == ("Fe",)          # fragment_atoms=[0]
    assert job.ligand_b.elements == ("C", "O")         # ligand = complement
    assert job.complex_ab.elements == ("Fe", "C", "O")
    assert job.experimental_dg == -12.0


def test_explicit_ligand_atoms(tmp_path):
    p = _write_study(tmp_path, extra={"ligand_atoms": [1, 2]})
    job = load_study(p).jobs[0]
    assert job.ligand_b.elements == ("C", "O")


def test_parity_validation_rejects_bad_spin(tmp_path):
    # Fe-CO complex has 40 electrons; spin=3 (odd) is impossible.
    p = _write_study(tmp_path, spins_complex=3)
    with pytest.raises(ValueError, match="impossible spin"):
        load_study(p)


def test_inline_atoms(tmp_path):
    doc = {
        "chemistry": {"ao_labels": ["Fe 3d"]},
        "ligands": [{
            "ligand_id": "X", "atoms": [["Fe", [0, 0, 0]], ["O", [0, 0, 2.0]]],
            "fragment_atoms": [0],
            "spins": {"fragment": 4, "ligand": 0, "complex": 4},
        }],
    }
    p = tmp_path / "s.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    job = load_study(p).jobs[0]
    assert job.complex_ab.elements == ("Fe", "O")
