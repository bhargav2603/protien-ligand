"""The delta analysis is the research contribution -- test it hardest."""
import numpy as np

from qbind.models import LigandScore
from qbind.scoring import delta


def _scores(base, corr, expt=None):
    expt = expt or [None] * len(base)
    return [LigandScore(f"L{i}", b, c, e) for i, (b, c, e) in enumerate(zip(base, corr, expt))]


def test_no_change_when_identical():
    s = _scores([-8, -9, -10], [-8, -9, -10])
    r = delta.compute(s)
    assert r.n_rank_changes == 0
    assert r.kendall_tau_rankings == 1.0
    assert not r.quantum_changed_ranking


def test_detects_a_swap():
    # baseline order L0<L1<L2 ; corrected swaps the two tightest
    s = _scores([-8, -9, -10], [-8, -10.5, -9.5])
    r = delta.compute(s)
    assert r.n_rank_changes > 0
    assert r.max_rank_shift >= 1


def test_correction_toward_experiment_is_positive():
    expt = [-6, -8, -10, -12]
    baseline = [-6, -8, -7, -7]          # gets the two tightest wrong
    corrected = [-6, -8, -10, -12]       # fixes them exactly
    r = delta.compute(_scores(baseline, corrected, expt))
    assert r.correlation_improvement is not None
    assert r.correlation_improvement > 0
    assert r.mae_corrected < r.mae_baseline
    assert "toward experiment" in r.verdict


def test_correction_away_from_experiment_is_negative():
    expt = [-6, -8, -10, -12]
    baseline = [-6, -8, -10, -12]        # already perfect
    corrected = [-6, -8, -7, -7]         # correction makes it worse
    r = delta.compute(_scores(baseline, corrected, expt))
    assert r.correlation_improvement < 0
    assert "AWAY from experiment" in r.verdict


def test_ranked_table_orders_by_corrected():
    s = _scores([-8, -9, -10], [-8, -10.5, -9.5])
    rows = delta.ranked_table(s)
    assert rows[0]["corrected_rank"] == 1
    assert rows[0]["corrected_score"] == min(x.corrected_score for x in s)
