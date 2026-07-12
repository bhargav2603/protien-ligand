"""Molecular study: run interaction energies for a set of fragment+ligand jobs
with a classical and a correlated backend, and reuse the existing delta / plots /
report machinery.

This is the real-chemistry analogue of the reference pipeline. In molecular mode
the ligand's "score" IS its interaction energy with the active-site fragment
(more negative = tighter). Baseline uses the classical backend; corrected uses
the correlated backend; only the strongly-correlated fragment is re-treated.
"""
from __future__ import annotations

from ..models import LigandScore, StudyResult
from ..runtime import Run
from ..scoring import delta
from ..scoring.delta import DeltaReport
from .interaction import InteractionJob, interaction_energy


def run_molecular_study(run: Run, jobs: list[InteractionJob],
                        classical_backend, correlated_backend,
                        target_name: str = "molecular-cluster",
                        pocket: str = "active-site-cluster"
                        ) -> tuple[StudyResult, DeltaReport]:
    run.log(f"molecular study: {len(jobs)} ligands; classical={classical_backend.name} "
            f"correlated={correlated_backend.name}")
    scores: list[LigandScore] = []
    coordinating: list[str] = []
    for job in jobs:
        baseline = interaction_energy(classical_backend, job)
        if job.is_strongly_correlated:
            corrected = interaction_energy(correlated_backend, job)
            coordinating.append(job.ligand_id)
        else:
            corrected = baseline
        scores.append(LigandScore(
            ligand_id=job.ligand_id, baseline_score=baseline,
            corrected_score=corrected, experimental_dg=job.experimental_dg))
        run.log(f"  {job.ligand_id}: baseline={baseline:.2f} corrected={corrected:.2f} "
                f"delta={corrected - baseline:+.2f} kcal/mol")

    report = delta.compute(scores)
    result = StudyResult(
        target_name=target_name, pocket=pocket, scores=scores, fragments=[],
        solver=correlated_backend.name, coordinating_ids=coordinating,
        notes=[f"Molecular cluster mode: interaction energies E(AB)-E(A)-E(B); "
               f"baseline={classical_backend.name}, corrected={correlated_backend.name}."])
    run.save("study_result", result)
    run.save("delta_report", report)
    run.log(f"VERDICT: {report.verdict}")
    return result, report
