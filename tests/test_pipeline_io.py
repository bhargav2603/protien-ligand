"""Context I/O + report generation, exercised without any quantum-chem deps."""
from qadv import make_context
from qadv.pipeline import report
from qadv.pipeline.results import Stage0Result, Stage1Result


def _ctx(tmp_path):
    return make_context(tmp_path)


def test_context_checkpoint_roundtrip(tmp_path):
    ctx = _ctx(tmp_path)
    ctx.save("thing", {"a": 1})
    assert ctx.load("thing") == {"a": 1}
    assert ctx.load("missing") is None


def test_decisions_journal_written(tmp_path):
    ctx = _ctx(tmp_path)
    ctx.decide("basis", "cc-pVDZ", "default")
    assert ctx.settings.decisions_file.exists()
    assert "basis" in ctx.settings.decisions_file.read_text(encoding="utf-8")


def test_report_with_empty_checkpoints(tmp_path):
    ctx = _ctx(tmp_path)
    path = report.generate(ctx)
    text = open(path, encoding="utf-8").read()
    assert "Stage 0 not yet run" in text
    assert "Headline claim withheld" in text     # no overclaim without a result
    assert "We do not beat DMRG" in text          # disclaimer always present


def test_report_uses_actual_qubit_count(tmp_path):
    ctx = _ctx(tmp_path)
    ctx.save("stage0_result", Stage0Result(
        n_qubits=20, ncas=10, nelec=(6, 2), basis="cc-pvdz",
        e_casci=-1.5, e_sqd_noiseless=-1.4991, gate_0b_passed=True))
    ctx.save("stage1_result", Stage1Result(
        n_qubits=44, ncas=22, basis="cc-pvdz", status="COMPLETE",
        sample_source="mps (NOT advantage)", sweep=[(1000, -2.0)]))
    text = open(report.generate(ctx), encoding="utf-8").read()
    assert "44-qubit active space" in text         # not the hardcoded 42
    assert "44 qubits" in text
