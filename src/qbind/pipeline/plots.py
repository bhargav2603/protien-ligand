"""The graphs. Everything the run must show, answering:
'did the quantum-computed correction change the ranking versus classical-only,
and by how much -- and toward experiment?'

matplotlib (Agg). Each function saves a PNG under run.figures and returns its path.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ..models import StudyResult
from ..runtime import Run
from ..scoring import delta
from ..scoring.delta import DeltaReport

_BLUE, _ORANGE, _GREY = "#2c7fb8", "#e67e22", "#95a5a6"


def _save(run: Run, fig, name: str):
    path = run.figures / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    run.log(f"figure written: {path}")
    return path


def _split_colors(result: StudyResult):
    coord = set(result.coordinating_ids)
    return [_ORANGE if s.ligand_id in coord else _GREY for s in result.scores]


def scatter_vs_experiment(run: Run, result: StudyResult, which: str,
                          spearman, mae, fname: str):
    xs = [s.experimental_dg for s in result.scores]
    ys = [getattr(s, f"{which}_score") for s in result.scores]
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(xs, ys, c=_split_colors(result), s=60, edgecolor="k", linewidth=0.4, zorder=3)
    lims = [min(xs + ys) - 0.5, max(xs + ys) + 0.5]
    ax.plot(lims, lims, ls=":", c="k", lw=1, label="y = x")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("experimental dG  [kcal/mol]")
    ax.set_ylabel(f"{which} predicted dG  [kcal/mol]")
    title = f"{which.capitalize()} vs experiment"
    if spearman is not None:
        title += f"\nSpearman={spearman:.3f}"
    if mae is not None:
        title += f"  MAE={mae:.2f}"
    ax.set_title(title)
    ax.scatter([], [], c=_ORANGE, label="coordinates fragment")
    ax.scatter([], [], c=_GREY, label="does not")
    ax.legend(loc="upper left", fontsize=8)
    return _save(run, fig, fname)


def correlation_improvement(run: Run, report: DeltaReport, fname="fig3_correlation_improvement.png"):
    """The headline: agreement with experiment, baseline vs corrected."""
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    if report.spearman_baseline_expt is None:
        ax.text(0.5, 0.5, "no experimental data\n(cannot judge direction)",
                ha="center", va="center")
        ax.axis("off")
        return _save(run, fig, fname)
    vals = [report.spearman_baseline_expt, report.spearman_corrected_expt]
    bars = ax.bar(["classical\nbaseline", "quantum-\ncorrected"], vals,
                  color=[_GREY, _BLUE], edgecolor="k")
    ax.set_ylabel("Spearman vs experiment (higher = better)")
    imp = report.correlation_improvement
    ax.set_title(f"Agreement with experiment\nimprovement = {imp:+.3f} Spearman")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.3f}",
                ha="center", va="bottom" if v >= 0 else "top")
    ax.axhline(0, color="k", lw=0.6)
    return _save(run, fig, fname)


def ranking_change(run: Run, result: StudyResult, report: DeltaReport,
                   fname="fig4_ranking_change.png"):
    """Slopegraph: each ligand's baseline rank -> corrected rank (rank 1 = tightest)."""
    rows = delta.ranked_table(result.scores)
    coord = set(result.coordinating_ids)
    fig, ax = plt.subplots(figsize=(6, 7))
    for r in rows:
        c = _ORANGE if r["ligand_id"] in coord else _GREY
        moved = r["baseline_rank"] != r["corrected_rank"]
        ax.plot([0, 1], [r["baseline_rank"], r["corrected_rank"]],
                "-o", color=c, lw=2 if moved else 0.8,
                alpha=1.0 if moved else 0.5, markersize=5)
        ax.text(-0.03, r["baseline_rank"], r["ligand_id"], ha="right", va="center", fontsize=7)
        ax.text(1.03, r["corrected_rank"], r["ligand_id"], ha="left", va="center", fontsize=7)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["baseline\nrank", "corrected\nrank"])
    ax.invert_yaxis()
    ax.set_ylabel("rank (1 = tightest binder)")
    ax.set_title(f"Ranking change\nKendall tau={report.kendall_tau_rankings:.3f}, "
                 f"{report.n_rank_changes} ligands moved, max shift={report.max_rank_shift}")
    ax.set_xlim(-0.25, 1.25)
    return _save(run, fig, fname)


def per_ligand_delta(run: Run, result: StudyResult, fname="fig5_per_ligand_delta.png"):
    """How much the correlated correction moved each ligand's score (kcal/mol)."""
    ids = [s.ligand_id for s in result.scores]
    deltas = [s.delta for s in result.scores]
    order = np.argsort(deltas)
    ids = [ids[i] for i in order]; deltas = [deltas[i] for i in order]
    colors = [_ORANGE if i in set(result.coordinating_ids) else _GREY for i in ids]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(ids, deltas, color=colors, edgecolor="k", linewidth=0.4)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("corrected - baseline  [kcal/mol]")
    ax.set_title("Per-ligand quantum correction\n(orange = coordinates the correlated fragment)")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    return _save(run, fig, fname)


def fragment_diagnostic(run: Run, result: StudyResult, fname="fig6_fragment_diagnostic.png"):
    """Which fragment justified the quantum/correlated solver."""
    names = [f.name for f in result.fragments]
    scores = [f.multireference_score for f in result.fragments]
    colors = [_BLUE if f.is_strongly_correlated else _GREY for f in result.fragments]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(names, scores, color=colors, edgecolor="k")
    ax.axhline(0.25, color="r", ls="--", lw=1, label="selection threshold")
    ax.set_ylabel("multireference score\n(frac. NOs in 0.02-1.98)")
    ax.set_title("Fragment correlation diagnostic\n(blue = routed to the correlated solver)")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=20)
    return _save(run, fig, fname)


def make_all(run: Run, result: StudyResult, report: DeltaReport) -> list[str]:
    paths = []
    have_expt = report.spearman_baseline_expt is not None
    if have_expt:
        paths.append(scatter_vs_experiment(run, result, "baseline",
                     report.spearman_baseline_expt, report.mae_baseline,
                     "fig1_baseline_vs_expt.png"))
        paths.append(scatter_vs_experiment(run, result, "corrected",
                     report.spearman_corrected_expt, report.mae_corrected,
                     "fig2_corrected_vs_expt.png"))
    paths.append(correlation_improvement(run, report))
    paths.append(ranking_change(run, result, report))
    paths.append(per_ligand_delta(run, result))
    paths.append(fragment_diagnostic(run, result))
    return [str(p) for p in paths]
