"""Assemble per-ligand scores from the pieces.

The ONLY difference between baseline and corrected must be the treatment of the
strongly-correlated fragment. Everything else (docking, other fragments,
complementarity) is identical and cancels in the delta -- that is what makes the
comparison a clean measurement of the quantum correction rather than of tool
mismatch.

    baseline_score  = docking + complementarity + sum(classical fragment terms)
    corrected_score = baseline_score
                      - classical_term(strong fragment)
                      + correlated_term(strong fragment)
"""
from __future__ import annotations

from ..models import FragmentInteraction, Ligand, LigandScore


def build_score(ligand: Ligand,
                docking_score: float,
                complementarity: float,
                fragment_interactions: list[FragmentInteraction]) -> LigandScore:
    classical_total = sum(fi.classical_term for fi in fragment_interactions)
    baseline = docking_score + complementarity + classical_total

    corrected = baseline
    for fi in fragment_interactions:
        if fi.correlated_term is not None:
            corrected += (fi.correlated_term - fi.classical_term)

    return LigandScore(
        ligand_id=ligand.ligand_id,
        baseline_score=baseline,
        corrected_score=corrected,
        experimental_dg=ligand.experimental_dg,
    )
