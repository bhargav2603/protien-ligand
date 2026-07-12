"""Classical (HF/DFT/MP2) fragment interaction energies (ClassicalSolver protocol).

The reference implementation replays pre-generated terms. The pyscf-backed
implementation computes a real DFT interaction energy per fragment; it is the
"majority of fragments" path in the FMO/DMET picture.
"""
from __future__ import annotations

from ..data.reference import ReferenceStudy
from ..models import FragmentSpec, Ligand


class ReferenceClassicalSolver:
    def __init__(self, study: ReferenceStudy):
        self._study = study

    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float:
        return self._study.classical_terms[(ligand.ligand_id, fragment.name)]


class PyscfClassicalSolver:  # pragma: no cover - needs pyscf + geometries
    """Real DFT interaction energy of a fragment with a ligand pose.

    Placeholder for the geometry-driven implementation: build the fragment+ligand
    supersystem and the isolated parts, run DFT, return E_AB - E_A - E_B with BSSE
    correction. Requires per-pose geometries from the embedding stage.
    """

    def __init__(self, xc: str = "wb97x-d", basis: str = "def2-SVP"):
        self.xc = xc
        self.basis = basis

    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float:
        raise NotImplementedError(
            "PyscfClassicalSolver needs per-pose fragment/ligand geometries from "
            "the embedding stage. Provide them, or use correlated_solver='reference'.")
