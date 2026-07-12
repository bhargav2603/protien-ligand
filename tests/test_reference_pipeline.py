"""End-to-end reference run: produces scores, a delta report, graphs, and a report.
Also checks the two designed behaviours (signal vs honest null)."""
from qbind import Config, ReferenceModel, run
from qbind.data import reference as refdata
from qbind.models import Ligand


def test_reference_run_produces_everything(tmp_path):
    result, report, figs = run(tmp_path, Config())
    assert len(result.scores) == 18
    assert (tmp_path / "results" / "REPORT.md").exists()
    assert len(figs) == 6                                   # all graphs written
    for f in figs:
        assert f.endswith(".png")
    assert (tmp_path / "results" / "ranked_candidates.json").exists()


def test_bias_gives_improvement_toward_experiment(tmp_path):
    cfg = Config(reference=ReferenceModel(systematic_bias=2.0, seed=1))
    _, report, _ = run(tmp_path, cfg)
    assert report.correlation_improvement is not None
    assert report.correlation_improvement > 0             # quantum helped
    assert report.quantum_changed_ranking


def test_zero_bias_is_the_honest_null(tmp_path):
    cfg = Config(reference=ReferenceModel(systematic_bias=0.0,
                                          classical_noise=0.5,
                                          correlated_noise=0.5, seed=1))
    _, report, _ = run(tmp_path, cfg)
    # With no systematic error to remove, agreement should not meaningfully improve.
    assert report.correlation_improvement is None or report.correlation_improvement < 0.05


def test_only_coordinating_ligands_are_corrected(tmp_path):
    _, report, _ = run(tmp_path, Config(reference=ReferenceModel(seed=3)))
    study = refdata.build(ReferenceModel(seed=3))
    coord = {l.ligand_id for l in study.ligands if l.coordinates_fragment}
    # Non-coordinating ligands must have zero correction (delta == 0).
    result = run(tmp_path, Config(reference=ReferenceModel(seed=3)))[0]
    for s in result.scores:
        if s.ligand_id not in coord:
            assert abs(s.delta) < 1e-9
