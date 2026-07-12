"""Fragmentation of the QM region (FMO / DMET-EWF) (Embedder protocol).

Reference implementation replays the study's fragments. The DMET adapter is a
stub wired to the shape of a real embedding: it would return each fragment's
embedded Hamiltonian for the classical/correlated solvers.
"""
from __future__ import annotations

from ..data.reference import ReferenceStudy
from ..models import FragmentSpec


class ReferenceEmbedder:
    def __init__(self, study: ReferenceStudy):
        self._study = study

    def fragments(self) -> list[FragmentSpec]:
        return list(self._study.fragments)


class DMETEmbedder:  # pragma: no cover - needs pyscf + a real region
    """Density matrix embedding of the QM region into fragments.

    Real implementation: run a low-level (HF/DFT) calculation on the whole QM
    region, build the DMET bath for each fragment, and expose each fragment's
    embedded one-/two-body integrals. The strongly-correlated fragment's
    integrals feed the CorrelatedSolver; the rest feed the ClassicalSolver.
    """

    def __init__(self, region, low_level: str = "b3lyp", basis: str = "def2-SVP"):
        self.region = region
        self.low_level = low_level
        self.basis = basis

    def fragments(self) -> list[FragmentSpec]:
        raise NotImplementedError(
            "DMETEmbedder needs a QMRegion with geometry and pyscf. Use "
            "embedding='reference' for the pilot, then implement the DMET bath here.")
