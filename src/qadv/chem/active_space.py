"""Active-space construction: AVAS selection + CASCI anchor + integrals.

This module is the SINGLE SOURCE OF TRUTH for the active-space Hamiltonian.
The integrals returned here (`h1`, `h2`, `ecore`) are exactly the ones CASCI
diagonalises, so feeding them to SQD makes Gate 0b a real test of the quantum
stack rather than an accidental integral-convention mismatch. This was the key
correctness bug in the first draft (two independent integral paths).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..runtime import Context


def split_nelec(nelec_total: int, spin: int) -> tuple[int, int]:
    """(n_alpha, n_beta) from total electrons and spin = 2S = na - nb."""
    if (nelec_total - spin) % 2 != 0:
        raise ValueError(
            f"electron/spin parity mismatch: nelec={nelec_total}, spin={spin}")
    na = (nelec_total + spin) // 2
    return int(na), int(nelec_total - na)


@dataclass
class ActiveSpace:
    ncas: int
    nelec: tuple[int, int]
    ncore: int
    mo: np.ndarray            # reference basis for BOTH integrals and ansatz
    h1: np.ndarray            # (ncas, ncas)
    h2: np.ndarray            # (ncas,)*4, chemist notation (pq|rs)
    ecore: float              # core (nuclear + inactive) energy constant
    e_casci: float | None     # anchor; None in the advantage regime (no FCI)
    ci: object | None         # CASCI CI vector (for the classical-sampling control)

    @property
    def n_qubits(self) -> int:
        return 2 * self.ncas

    @property
    def active_orbitals(self) -> list[int]:
        return list(range(self.ncore, self.ncore + self.ncas))


def _run_avas(mf, ao_labels, threshold: float):
    """AVAS across pyscf API variants (function vs class)."""
    from pyscf.mcscf import avas
    try:
        return avas.avas(mf, ao_labels, threshold=threshold, canonicalize=True)
    except TypeError:
        obj = avas.AVAS(mf, ao_labels, threshold=threshold)
        obj.canonicalize = True
        return obj.kernel()


def build(ctx: Context, mf, ao_labels, spin: int,
          want_casci: bool = True, threshold: float = 0.2) -> ActiveSpace:
    from pyscf import ao2mo, mcscf

    ncas, nelecas, mo = _run_avas(mf, ao_labels, threshold)
    ncas = int(ncas)
    na, nb = split_nelec(int(nelecas), spin)
    ncore = (mf.mol.nelectron - (na + nb)) // 2
    ctx.log(f"active space ({','.join(ao_labels)}): ncas={ncas} "
            f"nelec=({na},{nb}) ncore={ncore} qubits={2 * ncas}")

    mc = mcscf.CASCI(mf, ncas, (na, nb))
    # Integrals in the AVAS `mo` basis -- the exact CASCI Hamiltonian.
    h1, ecore = mc.get_h1eff(mo)
    h2 = ao2mo.restore(1, mc.get_h2eff(mo), ncas)

    e_casci: float | None = None
    ci = None
    if want_casci:
        mc.kernel(mo)
        e_casci = float(mc.e_tot)
        ci = mc.ci
        ctx.log(f"CASCI anchor E={e_casci:.8f} (correctness reference)")

    return ActiveSpace(ncas=ncas, nelec=(na, nb), ncore=ncore, mo=np.asarray(mo),
                       h1=np.asarray(h1), h2=np.asarray(h2), ecore=float(ecore),
                       e_casci=e_casci, ci=ci)
