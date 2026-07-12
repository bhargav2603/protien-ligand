"""The research contribution: quantify how the correlated correction changed the
ranking versus the classical-only baseline, and whether it moved toward experiment.

Pure functions over LigandScore lists. No I/O. Fully unit-tested.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from ..models import LigandScore


@dataclass
class DeltaReport:
    n_ligands: int
    # Ranking change (baseline order vs corrected order).
    kendall_tau_rankings: float
    spearman_rankings: float
    n_rank_changes: int
    max_rank_shift: int
    # Agreement with experiment (only if experimental dG is available).
    spearman_baseline_expt: float | None
    spearman_corrected_expt: float | None
    pearson_baseline_expt: float | None
    pearson_corrected_expt: float | None
    correlation_improvement: float | None   # corrected - baseline (Spearman)
    mae_baseline: float | None              # kcal/mol vs experiment
    mae_corrected: float | None
    # Per-ligand correction magnitude.
    mean_abs_delta: float
    max_abs_delta: float

    @property
    def quantum_changed_ranking(self) -> bool:
        return self.n_rank_changes > 0

    @property
    def verdict(self) -> str:
        if self.correlation_improvement is None:
            return ("Ranking changed" if self.quantum_changed_ranking
                    else "No ranking change") + " (no experimental data to judge direction)"
        if not self.quantum_changed_ranking:
            return "No ranking change: the correlated correction did not move any ligand's rank."
        if self.correlation_improvement > 0.02:
            return (f"Ranking changed AND moved toward experiment "
                    f"(Spearman +{self.correlation_improvement:.3f}). A real, positive result.")
        if self.correlation_improvement < -0.02:
            return (f"Ranking changed but AWAY from experiment "
                    f"(Spearman {self.correlation_improvement:.3f}). Correction is not helping.")
        return ("Ranking changed but agreement with experiment is essentially "
                "unchanged -- perturbation without improvement.")


def _ranks(values: list[float]) -> np.ndarray:
    """Ordinal ranks; rank 1 = tightest binder (most negative dG). Ties broken
    deterministically so baseline and corrected rankings stay comparable."""
    return stats.rankdata(values, method="ordinal").astype(int)


def _stat(result) -> float:
    """Correlation coefficient across scipy versions (>=1.9 objects, older tuples)."""
    if hasattr(result, "statistic"):
        return float(result.statistic)
    if hasattr(result, "correlation"):
        return float(result.correlation)
    return float(result[0])


def _safe_spearman(a, b) -> float | None:
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return None
    return _stat(stats.spearmanr(a, b))


def _safe_pearson(a, b) -> float | None:
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return None
    return _stat(stats.pearsonr(a, b))


def compute(scores: list[LigandScore]) -> DeltaReport:
    base = [s.baseline_score for s in scores]
    corr = [s.corrected_score for s in scores]
    base_rank = _ranks(base)
    corr_rank = _ranks(corr)

    rank_shift = np.abs(base_rank - corr_rank)
    kt = _stat(stats.kendalltau(base_rank, corr_rank)) if len(scores) > 1 else 1.0
    sr = _safe_spearman(base_rank, corr_rank)

    have_expt = all(s.experimental_dg is not None for s in scores) and len(scores) >= 3
    sb = sc = pb = pc = mae_b = mae_c = improve = None
    if have_expt:
        expt = [s.experimental_dg for s in scores]
        sb = _safe_spearman(base, expt)
        sc = _safe_spearman(corr, expt)
        pb = _safe_pearson(base, expt)
        pc = _safe_pearson(corr, expt)
        mae_b = float(np.mean(np.abs(np.array(base) - np.array(expt))))
        mae_c = float(np.mean(np.abs(np.array(corr) - np.array(expt))))
        if sb is not None and sc is not None:
            improve = sc - sb

    deltas = np.abs([s.delta for s in scores])
    return DeltaReport(
        n_ligands=len(scores),
        kendall_tau_rankings=kt,
        spearman_rankings=sr if sr is not None else 1.0,
        n_rank_changes=int(np.count_nonzero(rank_shift)),
        max_rank_shift=int(rank_shift.max()) if len(scores) else 0,
        spearman_baseline_expt=sb, spearman_corrected_expt=sc,
        pearson_baseline_expt=pb, pearson_corrected_expt=pc,
        correlation_improvement=improve,
        mae_baseline=mae_b, mae_corrected=mae_c,
        mean_abs_delta=float(deltas.mean()) if len(deltas) else 0.0,
        max_abs_delta=float(deltas.max()) if len(deltas) else 0.0,
    )


def ranked_table(scores: list[LigandScore]) -> list[dict]:
    """Ligands ranked by corrected score (tightest first), with rank movement."""
    base_rank = {s.ligand_id: r for s, r in zip(scores, _ranks([s.baseline_score for s in scores]))}
    corr_rank = {s.ligand_id: r for s, r in zip(scores, _ranks([s.corrected_score for s in scores]))}
    rows = []
    for s in sorted(scores, key=lambda x: x.corrected_score):
        rows.append(dict(
            ligand_id=s.ligand_id,
            corrected_rank=corr_rank[s.ligand_id],
            baseline_rank=base_rank[s.ligand_id],
            rank_move=base_rank[s.ligand_id] - corr_rank[s.ligand_id],
            baseline_score=round(s.baseline_score, 3),
            corrected_score=round(s.corrected_score, 3),
            delta=round(s.delta, 3),
            experimental_dg=(round(s.experimental_dg, 3)
                             if s.experimental_dg is not None else None),
        ))
    return rows
