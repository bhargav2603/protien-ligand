"""Electrostatic / ESP complementarity between a ligand and the pocket surface.

Real implementation compares the ligand's DFT ESP against the pocket's
complementary surface (Hirshfeld-surface overlap or electrostatic-complementarity
metric) -- NOT a direct density-vs-density comparison, since a small ligand and a
protein pocket are different kinds of object. Provided here as an interface with
a reference implementation; a `pyscf`-backed version slots in behind the same
ComplementarityScorer protocol.
"""
from __future__ import annotations

import numpy as np

from ..models import Ligand


class ReferenceComplementarity:
    """Deterministic surrogate keyed on the ligand id. Contributes an identical
    additive term to baseline and corrected, so it cancels in the delta (its role
    here is to exercise the interface, not to bias the comparison)."""

    def __init__(self, scale: float = 0.5):
        self.scale = scale

    def score(self, ligand: Ligand) -> float:
        h = abs(hash(ligand.ligand_id)) % 1000 / 1000.0
        return -self.scale * h    # small favourable contribution (kcal/mol)
