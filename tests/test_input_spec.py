"""The single input.json workflow: load, validate, dispatch."""
import json
from pathlib import Path

import pytest

from qbind.input_spec import RunInput

_REPO = Path(__file__).parents[1]


def _write(tmp_path, doc):
    p = tmp_path / "input.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_load_defaults_and_validation(tmp_path):
    spec = RunInput.load(_write(tmp_path, {"mode": "reference"}))
    assert spec.mode == "reference"
    assert spec.output_dir == "./out"


def test_bad_mode_rejected(tmp_path):
    with pytest.raises(ValueError, match="mode must be"):
        RunInput.load(_write(tmp_path, {"mode": "nonsense"}))


def test_bad_backend_rejected(tmp_path):
    with pytest.raises(ValueError, match="backend must be"):
        RunInput.load(_write(tmp_path, {"mode": "molecular", "backend": "xyz"}))


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        RunInput.load(tmp_path / "nope.json")


def test_study_path_resolves_relative_to_input(tmp_path):
    (tmp_path / "s.json").write_text("{}", encoding="utf-8")
    spec = RunInput.load(_write(tmp_path, {"mode": "molecular", "study_file": "s.json"}))
    assert Path(spec._resolved_study()) == tmp_path / "s.json"


def test_execute_reference(tmp_path):
    doc = {"mode": "reference", "output_dir": str(tmp_path / "o"),
           "reference": {"n_ligands": 6, "seed": 1}}
    result, report, figs = RunInput.load(_write(tmp_path, doc)).execute()
    assert len(result.scores) == 6
    assert (tmp_path / "o" / "results" / "REPORT.md").exists()


def test_execute_molecular_with_shipped_study(tmp_path):
    doc = {"mode": "molecular", "backend": "analytic",
           "output_dir": str(tmp_path / "o"),
           "study_file": str(_REPO / "examples" / "study_fe_ligands" / "study.json")}
    result, report, figs = RunInput.load(_write(tmp_path, doc)).execute()
    assert [s.ligand_id for s in result.scores] == ["CO", "NH3", "H2O"]
    assert len(figs) == 5


def test_repo_input_json_is_valid():
    # The shipped input.json must always load and validate.
    spec = RunInput.load(_REPO / "input.json")
    assert spec.mode in ("reference", "molecular")
