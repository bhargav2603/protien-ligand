"""Stage 1 -- P450 Compound I, >=40 qubits. HARDWARE / MPS ONLY. The result.

Beyond exact diagonalisation (no CASCI anchor -- that is the point) and beyond
statevector simulation. Samples come from IBM hardware (async) or, for pipeline
validation only, an MPS surrogate that is explicitly NOT an advantage result.
"""
from __future__ import annotations

import numpy as np

from ..chem import active_space, geometry, scf
from ..constants import EXACT_DIAG_WALL_QUBITS, STATEVECTOR_WALL_QUBITS
from ..quantum import ansatz, hardware, sampling, sqd
from ..runtime import Context
from . import plots
from .errors import GateFailure
from .results import Stage1Result

# AVAS targets: Fe double shell + oxo 2p + thiolate 3p + porphyrin pi (N 2pz).
# This yields the >=40-qubit advantage-regime active space.
AO_LABELS = ["Fe 3d", "Fe 4d", "O 2p", "S 3p", "N 2pz"]


def run(ctx: Context, use_hardware: bool = True, allow_mps: bool = True) -> Stage1Result:
    s = ctx.settings
    ctx.log("==== STAGE 1: P450 Compound I (>=40q => advantage regime) ====")

    atoms = geometry.compound_i()
    ctx.decide("Stage1 geometry", "idealized Cpd I (porphine+oxo+SH)",
               "not literature-pinned; Fe=O 1.63, Fe-S 2.50. Replace for publication.")

    # Doublet (2S=1) reference for the active-space Hamiltonian.
    mf = scf.run_rohf(ctx, scf.build_mol(atoms, spin=1, basis=s.basis), tag="cpd1_doublet")
    a = active_space.build(ctx, mf, AO_LABELS, spin=1, want_casci=False)

    # --- The two physical walls: HALT conditions, not opinions ----------- #
    if a.n_qubits < EXACT_DIAG_WALL_QUBITS:
        result = Stage1Result(n_qubits=a.n_qubits, ncas=a.ncas, basis=s.basis,
                              status="HALTED", nelec=a.nelec)
        ctx.save("stage1_result", result)
        raise GateFailure(
            f"{a.n_qubits}q < {EXACT_DIAG_WALL_QUBITS}q: exact FCI solves this. "
            "No advantage claim. Enlarge the active space or abandon.")
    ctx.log(f"{a.n_qubits}q: BEYOND exact diagonalisation. Advantage claim available.")
    if a.n_qubits <= STATEVECTOR_WALL_QUBITS:
        raise GateFailure(f"{a.n_qubits}q is statevector-simulable => not an advantage claim.")
    ctx.log(f"{a.n_qubits}q CANNOT be statevector-simulated. Hardware or MPS only.")

    result = Stage1Result(n_qubits=a.n_qubits, ncas=a.ncas, basis=s.basis,
                          status="PENDING_HARDWARE", nelec=a.nelec)

    circuit = ansatz.build_lucj(ctx, mf, a, heavy_hex_local=True)

    # --- Acquire samples: hardware (async) preferred; MPS as labelled surrogate.
    bit_array = None
    source = None
    if use_hardware and circuit is not None:
        service = hardware.get_service(ctx)
        if service is not None:
            bit_array = hardware.retrieve(ctx, service, job_tag="cpd1")
            if bit_array is None:
                hardware.submit(ctx, service, circuit, s.shots, a.n_qubits, "cpd1")
                ctx.save("stage1_result", result)
                ctx.log("Stage 1 hardware job submitted; re-run later to retrieve.")
                return result
            source = "hardware"

    if bit_array is None and allow_mps and circuit is not None:
        bit_array = sampling.mps(ctx, circuit, s.shots)
        source = "mps (NOT advantage)"

    if bit_array is None:
        ctx.save("stage1_result", result)
        ctx.log("No samples available. Marked PENDING_HARDWARE.", "WARNING")
        return result

    # --- Subspace sweep = the result. Checkpoint every iteration. -------- #
    def _persist(curve):
        np.save(s.results / "cpd1_sqd_sweep.npy", np.array(curve))

    curve = sqd.subspace_sweep(ctx, a, bit_array, s.stage1_sweep,
                               s.sqd_num_batches, s.sqd_max_iterations, s.seed,
                               on_iteration=_persist)
    result.sweep = curve
    result.sample_source = source
    result.status = "COMPLETE"

    # --- Integrity check (B3): hardware vs a noiseless MPS reference ----- #
    if source == "hardware" and circuit is not None and curve:
        noiseless = sampling.mps(ctx, circuit, s.shots)
        e_noiseless = sqd.diagonalize(ctx, a, noiseless, s.stage1_sweep[0],
                                      s.sqd_num_batches, s.sqd_max_iterations, s.seed)
        result.integrity_clean = hardware.integrity_check(ctx, curve[0][1], e_noiseless)

    if curve:
        plots.sqd_convergence(ctx, curve, None, None,
                              title=f"Stage 1: P450 Cpd I bound ({a.n_qubits}q, {source})",
                              fname="fig2b_cpd1_convergence.png")

    ctx.save("stage1_result", result)
    ctx.log("==== STAGE 1 COMPLETE ====")
    return result
