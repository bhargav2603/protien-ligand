"""Wire the stages into a study and produce scores + the delta report.

The orchestrator depends only on the stage protocols. In reference mode it wires
the reference implementations; swapping in Vina/PySCF/SQD is a config change.
Consistency guarantee enforced here: baseline and corrected differ ONLY by the
correlated fragment term.
"""
from __future__ import annotations

from ..config import Config
from ..data import reference as refdata
from ..models import FragmentInteraction, LigandScore, StudyResult
from ..runtime import Run
from ..scoring import delta, rescore
from ..scoring.complementarity import ReferenceComplementarity
from ..qm import diagnostics


def _build_reference_stages(cfg: Config):
    from ..classical.baseline import ReferenceClassicalSolver
    from ..classical.docking import ReferenceDockingEngine
    from ..qm.correlated import ReferenceCorrelatedSolver
    from ..qm.embedding import ReferenceEmbedder

    study = refdata.build(cfg.reference)
    return dict(
        ligands=study.ligands,
        docking=ReferenceDockingEngine(study),
        embedder=ReferenceEmbedder(study),
        classical=ReferenceClassicalSolver(study),
        correlated=ReferenceCorrelatedSolver(study),
        complementarity=ReferenceComplementarity(),
    )


def score_ligands(stages, fragments, strong_names) -> list[LigandScore]:
    """Pure scoring loop (no I/O). Reused by run_study and the sensitivity sweep."""
    scores: list[LigandScore] = []
    for lig in stages["ligands"]:
        dock = stages["docking"].dock(lig)
        comp = stages["complementarity"].score(lig)
        interactions: list[FragmentInteraction] = []
        for frag in fragments:
            k = stages["classical"].interaction(lig, frag)
            q = (stages["correlated"].interaction(lig, frag)
                 if frag.name in strong_names else None)
            interactions.append(FragmentInteraction(
                ligand_id=lig.ligand_id, fragment_name=frag.name,
                classical_term=k, correlated_term=q))
        scores.append(rescore.build_score(lig, dock, comp, interactions))
    return scores


def run_study(run: Run, cfg: Config) -> tuple[StudyResult, delta.DeltaReport]:
    if not cfg.is_reference:
        raise NotImplementedError(
            "Non-reference stages (vina/pyscf/sqd) are adapters you wire to your "
            "environment; the orchestrator's reference path is the runnable pilot. "
            "See qm/correlated.py and classical/docking.py for the plug points.")

    run.log(f"study: target={cfg.target_name} pocket={cfg.pocket} (reference mode)")
    stages = _build_reference_stages(cfg)
    ligands = stages["ligands"]
    fragments = stages["embedder"].fragments()

    strong = diagnostics.select_strong_fragments(fragments)
    run.decide("correlated fragments",
               ",".join(f.name for f in strong) or "none",
               "selected by natural-orbital multireference diagnostic; only these "
               "spend the quantum/correlated budget")

    scores = score_ligands(stages, fragments, {f.name for f in strong})
    report = delta.compute(scores)
    result = StudyResult(
        target_name=cfg.target_name, pocket=cfg.pocket, scores=scores,
        fragments=fragments, solver=stages["correlated"].name,
        coordinating_ids=[l.ligand_id for l in ligands if l.coordinates_fragment],
        notes=[f"REFERENCE MODE (synthetic): {refdata.STRONG_FRAGMENT} carries a "
               f"systematic DFT bias of {cfg.reference.systematic_bias} kcal/mol "
               "that the correlated solver removes."],
    )
    run.save("study_result", result)
    run.save("delta_report", report)
    run.log(f"VERDICT: {report.verdict}")
    return result, report
