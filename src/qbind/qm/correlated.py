"""Correlated solvers for the strongly-correlated fragment (CorrelatedSolver).

Reference implementation replays study terms. The SQD implementation reuses the
`qadv` kernel (AVAS + CASCI-consistent integrals + SQD subspace sweep); the
CASSCF implementation is the classical correlated stand-in you should use FIRST
(the research question is answerable without a quantum computer -- see the
project notes). All must reduce to the classical value in the weakly-correlated
limit so the delta stays a clean measurement.
"""
from __future__ import annotations

from ..data.reference import ReferenceStudy
from ..models import FragmentSpec, Ligand


class ReferenceCorrelatedSolver:
    name = "reference"

    def __init__(self, study: ReferenceStudy):
        self._study = study

    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float:
        return self._study.correlated_terms[(ligand.ligand_id, fragment.name)]


class CASSCFCorrelatedSolver:  # pragma: no cover - needs pyscf + integrals
    """Classical correlated solver (CASSCF/NEVPT2 or DMRG). Use this to answer the
    research question before touching quantum hardware."""

    name = "casscf"

    def __init__(self, ncas: int, nelecas: int, basis: str = "def2-SVP"):
        self.ncas = ncas
        self.nelecas = nelecas
        self.basis = basis

    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float:
        raise NotImplementedError(
            "CASSCFCorrelatedSolver needs the fragment's embedded integrals from "
            "the DMET/FMO stage. Wire embedding to pyscf, then run mcscf.CASSCF.")


class SQDCorrelatedSolver:  # pragma: no cover - needs qadv[science]
    """Quantum solver via the qadv SQD kernel. Only warranted when the fragment
    exceeds classical exact reach (>= ~40 qubits); otherwise CASSCF/DMRG suffices.
    """

    name = "sqd"

    def __init__(self, ao_labels, spin: int, basis: str = "def2-SVP"):
        self.ao_labels = ao_labels
        self.spin = spin
        self.basis = basis

    def interaction(self, ligand: Ligand, fragment: FragmentSpec) -> float:
        # Sketch of the real reuse of qadv on a per-ligand embedded fragment:
        #   from qadv.runtime import Context
        #   from qadv.chem import active_space
        #   from qadv.quantum import ansatz, sampling, sqd
        #   a = active_space.build(ctx, mf_fragment, self.ao_labels, self.spin,
        #                          want_casci=(fragment n_qubits < 40))
        #   circ = ansatz.build_lucj(ctx, mf_fragment, a)
        #   bits = sampling.mps(ctx, circ, shots)   # or hardware
        #   E_complex = sqd.diagonalize(ctx, a, bits, subspace_dim)
        #   ...repeat for isolated fragment/ligand, return E_AB - E_A - E_B
        raise NotImplementedError(
            "SQDCorrelatedSolver needs per-ligand embedded fragment Hamiltonians "
            "(build them in the embedding stage) and qadv[science] installed. The "
            "reuse pattern is sketched in the source above.")
