"""Write results/REPORT.md: the ranked list + the quantified quantum-vs-classical
delta (the actual research deliverable), with honest framing of mode/limits.
"""
from __future__ import annotations

import os

from ..models import StudyResult
from ..runtime import Run
from ..scoring import delta
from ..scoring.delta import DeltaReport


def generate(run: Run, result: StudyResult, report: DeltaReport,
             figures: list[str], reference_mode: bool) -> str:
    L: list[str] = []
    w = L.append

    w(f"# Binding-affinity rescoring -- {result.target_name} / {result.pocket}\n")
    if reference_mode:
        w("> **REFERENCE MODE (synthetic data).** This validates the pipeline and "
          "graphs end-to-end. It is NOT a scientific result. Swap in a real target, "
          "docking, and QM embedding to produce a meaningful ranking.\n")

    w("## Headline: did the quantum-computed correction change the ranking?\n")
    w(f"**{report.verdict}**\n")
    w(f"- ligands: {report.n_ligands}; correlated solver: `{result.solver}`")
    w(f"- ranking change vs baseline: Kendall tau = {report.kendall_tau_rankings:.3f}, "
      f"{report.n_rank_changes} ligands moved (max shift {report.max_rank_shift})")
    if report.spearman_baseline_expt is not None:
        w(f"- agreement with experiment (Spearman): baseline "
          f"{report.spearman_baseline_expt:.3f} -> corrected "
          f"{report.spearman_corrected_expt:.3f} "
          f"(**{report.correlation_improvement:+.3f}**)")
        w(f"- error vs experiment (MAE, kcal/mol): baseline {report.mae_baseline:.2f} "
          f"-> corrected {report.mae_corrected:.2f}")
    w(f"- correction magnitude: mean |dG| = {report.mean_abs_delta:.2f}, "
      f"max = {report.max_abs_delta:.2f} kcal/mol\n")

    w("## Ranked candidates (by quantum-corrected dG, tightest first)\n")
    w("| rank | ligand | corrected dG | baseline dG | delta | exp dG | rank move |")
    w("|---:|:--|---:|---:|---:|---:|---:|")
    for r in delta.ranked_table(result.scores):
        move = r["rank_move"]
        arrow = "=" if move == 0 else (f"+{move}" if move > 0 else str(move))
        exp = "" if r["experimental_dg"] is None else f"{r['experimental_dg']:.2f}"
        w(f"| {r['corrected_rank']} | {r['ligand_id']} | {r['corrected_score']:.2f} | "
          f"{r['baseline_score']:.2f} | {r['delta']:+.2f} | {exp} | {arrow} |")
    w("")

    w("## How to read this\n")
    w("- *Ranking change alone is not a win.* The result is whether the corrected "
      "ranking agrees with experiment BETTER than the classical baseline.")
    w("- The correction is applied ONLY to the strongly-correlated fragment; every "
      "other term is identical between baseline and corrected, so the delta measures "
      "the quantum correction and nothing else.\n")

    for note in result.notes:
        w(f"> {note}\n")

    w("## Figures\n")
    for f in figures:
        w(f"- figures/{os.path.basename(f)}")

    path = run.results / "REPORT.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    run.write_json("delta_report.json", report.__dict__)
    run.write_json("ranked_candidates.json", delta.ranked_table(result.scores))
    run.log(f"report written: {path}")
    return str(path)
