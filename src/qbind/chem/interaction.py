"""Supermolecular interaction energy of a fragment (A) with a ligand (B).

    E_int = E(AB) - E(A) - E(B)

computed with ONE backend so the method is consistent across the three pieces.
The classical baseline uses a DFT backend for all three; the corrected value
uses a correlated backend. Their difference is the quantum/correlated correction
to the interaction -- the only thing that changes between baseline and corrected.
"""
from __future__ import annotations

from dataclasses import dataclass

from .geometry import Geometry

HARTREE_TO_KCAL = 627.5094740631


@dataclass(frozen=True)
class InteractionJob:
    ligand_id: str
    complex_ab: Geometry           # fragment + ligand
    fragment_a: Geometry           # the (metal) fragment alone
    ligand_b: Geometry             # the ligand alone
    is_strongly_correlated: bool = True
    experimental_dg: float | None = None


def interaction_energy(backend, job: InteractionJob, unit: str = "kcal") -> float:
    e_ab = backend.energy(job.complex_ab)
    e_a = backend.energy(job.fragment_a)
    e_b = backend.energy(job.ligand_b)
    e_int = e_ab - e_a - e_b
    return e_int * HARTREE_TO_KCAL if unit == "kcal" else e_int
