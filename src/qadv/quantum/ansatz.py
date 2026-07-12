"""LUCJ ansatz construction (ffsim), seeded from active-space CCSD amplitudes.

Correctness fix vs the first draft: we build a *consistent* mean-field reference
(`_prepare_reference`) with MO coefficients, orbital energies and occupations
that all correspond to the AVAS orbitals, instead of leaving stale post-SCF
metadata attached to a mutated `mf`. The ansatz shares the AVAS `mo` basis with
the SQD integrals, so sampled bitstrings and the Hamiltonian speak the same
orbital language.

The ansatz only affects *sampling quality*, never the energy (that comes from
the CASCI-consistent integrals). So a poor or failed ansatz cannot corrupt the
result -- it just needs a larger subspace, and on failure we fall back cleanly.
"""
from __future__ import annotations

import numpy as np

from ..chem.active_space import ActiveSpace
from ..runtime import Context


def _prepare_reference(mf, a: ActiveSpace):
    """A copy of `mf` whose mo_coeff/mo_energy/mo_occ all match the AVAS orbitals."""
    mf2 = mf.copy()
    mf2.mo_coeff = a.mo
    fock = mf.get_fock()
    mf2.mo_energy = np.einsum("pi,pq,qi->i", a.mo, fock, a.mo)
    nmo = a.mo.shape[1]
    occ = np.zeros(nmo)
    occ[:a.ncore] = 2.0
    na, nb = a.nelec
    lo = a.ncore
    occ[lo:lo + nb] = 2.0
    occ[lo + nb:lo + na] = 1.0
    mf2.mo_occ = occ
    return mf2


def build_lucj(ctx: Context, mf, a: ActiveSpace, n_reps=None,
               heavy_hex_local: bool = False):
    """Return a measured LUCJ QuantumCircuit, or None (caller falls back)."""
    try:
        import ffsim
        from pyscf import cc
        from qiskit import QuantumCircuit, QuantumRegister

        norb, nelec = a.ncas, a.nelec
        mf2 = _prepare_reference(mf, a)
        frozen = [i for i in range(a.mo.shape[1]) if i not in set(a.active_orbitals)]

        mycc = cc.CCSD(mf2, frozen=frozen)
        mycc.verbose = 0
        mycc.kernel()
        t1, t2 = mycc.t1, mycc.t2

        pairs = None
        if heavy_hex_local:
            # Hardware-friendly LUCJ: same-spin nearest-neighbour + diagonal
            # opposite-spin coupler keeps the circuit shallow on heavy-hex.
            pairs = ([(p, p + 1) for p in range(norb - 1)],
                     [(p, p) for p in range(norb)])

        unbalanced = isinstance(t1, (tuple, list))
        if unbalanced:
            op = ffsim.UCJOpSpinUnbalanced.from_t_amplitudes(
                t2, t1=t1, n_reps=n_reps, interaction_pairs=pairs)
            gate = ffsim.qiskit.UCJOpSpinUnbalancedJW(op)
        else:
            op = ffsim.UCJOpSpinBalanced.from_t_amplitudes(
                t2, t1=t1, n_reps=n_reps, interaction_pairs=pairs)
            gate = ffsim.qiskit.UCJOpSpinBalancedJW(op)

        qr = QuantumRegister(2 * norb, "q")
        qc = QuantumCircuit(qr)
        qc.append(ffsim.qiskit.PrepareHartreeFockJW(norb, nelec), qr)
        qc.append(gate, qr)
        qc.measure_all()
        ctx.log(f"LUCJ built: {2 * norb}q "
                f"({'unbalanced' if unbalanced else 'balanced'} UCJ)")
        return qc
    except Exception as e:
        ctx.decide("LUCJ ansatz", "fallback to classical sampling",
                   f"circuit construction failed ({str(e)[:120]})")
        return None
