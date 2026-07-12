"""Stage interfaces (typing.Protocol). Each has a reference implementation and a
real one. The orchestrator depends only on these protocols, so swapping the
reference solver for genuine SQD/PySCF is a one-line config change and cannot
ripple through the rest of the pipeline.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import FragmentInteraction, FragmentSpec, Ligand


@runtime_checkable
class DockingEngine(Protocol):
    """Generate a best pose + a classical docking score per ligand (kcal/mol)."""
    def dock(self, ligand: Ligand) -> float: ...


@runtime_checkable
class Embedder(Protocol):
    """Partition the QM region into fragments and flag the correlated one(s)."""
    def fragments(self) -> list[FragmentSpec]: ...


@runtime_checkable
class ClassicalSolver(Protocol):
    """Classical (HF/DFT/MP2) interaction energy of a fragment with a ligand."""
    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float: ...


@runtime_checkable
class CorrelatedSolver(Protocol):
    """Correlated (SQD/CASSCF/DMRG) interaction energy of the strong fragment.

    Must reduce to the classical value in the weakly-correlated limit -- that is
    the consistency guarantee that makes the baseline-vs-corrected delta meaningful.
    """
    name: str
    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float: ...


@runtime_checkable
class ComplementarityScorer(Protocol):
    """ESP / electrostatic complementarity between ligand and pocket surface."""
    def score(self, ligand: Ligand) -> float: ...
