"""Bitstring samplers. All return a qiskit `BitArray` in ffsim's JW convention.

Routing every sampler (quantum statevector, MPS, classical wavefunction) through
the same ffsim/qiskit convention is what makes the quantum result and the
classical-sampling control directly comparable at matched subspace dimension.
"""
from __future__ import annotations

import numpy as np

from ..constants import STATEVECTOR_WALL_QUBITS
from ..runtime import Context


def statevector(ctx: Context, circuit, shots: int, gpu: bool = False):
    """Noiseless statevector sampling. Refuses to run past the simulation wall."""
    n = circuit.num_qubits
    if n > STATEVECTOR_WALL_QUBITS:
        raise RuntimeError(
            f"{n} qubits exceeds the statevector wall ({STATEVECTOR_WALL_QUBITS}); "
            "dense statevector is physically impossible here -- use MPS or hardware.")
    from qiskit import transpile
    from qiskit.primitives import BitArray
    from qiskit_aer import AerSimulator

    sim = AerSimulator(method="statevector")
    if gpu:
        try:
            sim.set_options(device="GPU")
            ctx.log("Aer statevector on GPU")
        except Exception:
            ctx.log("GPU requested but unavailable; using CPU", "WARNING")
    counts = sim.run(transpile(circuit, sim), shots=shots).result().get_counts()
    return BitArray.from_counts(counts, num_bits=n)


def mps(ctx: Context, circuit, shots: int, bond_dim: int | None = None):
    """Matrix-product-state sampling: the >32-qubit escape hatch (debugging only).

    Auto-logs the caveat: an easy MPS run implies a tensor-network method (DMRG)
    could treat the system too. MPS is never reported as quantum advantage.
    """
    from qiskit import transpile
    from qiskit.primitives import BitArray
    from qiskit_aer import AerSimulator

    opts = {"method": "matrix_product_state"}
    if bond_dim:
        opts["matrix_product_state_max_bond_dimension"] = int(bond_dim)
    sim = AerSimulator(**opts)
    counts = sim.run(transpile(circuit, sim), shots=shots).result().get_counts()
    ctx.decide("MPS simulation", "debugging surrogate",
               "tensor-network method; a clean MPS run implies DMRG feasibility. "
               "NOT reported as quantum advantage.")
    return BitArray.from_counts(counts, num_bits=circuit.num_qubits)


def classical_wavefunction(ctx: Context, civector, norb: int,
                           nelec: tuple[int, int], shots: int, seed: int = 0):
    """Sample determinants from a classical CI vector (Stage 0.5 control + fallback).

    Feasible only where the dense CI vector exists (Stage 0). At 42 qubits the
    vector would be 2**42 long -- which is exactly why the advantage regime is
    not classically simulable.
    """
    import ffsim
    from qiskit.primitives import BitArray

    vec = np.asarray(civector).reshape(-1).astype(complex)
    norm = np.linalg.norm(vec)
    if norm == 0:
        raise ValueError("empty CI vector for classical control")
    vec = vec / norm
    strings = ffsim.sample_state_vector(vec, norb=norb, nelec=nelec,
                                        shots=int(shots), seed=seed)
    return BitArray.from_samples(strings, num_bits=2 * norb)
