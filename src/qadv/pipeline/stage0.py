"""Stage 0 -- Fe(II)-porphyrin, ~20 qubits. VALIDATION, never advantage.

Below 40 qubits exact FCI wins, so this can only validate the pipeline: SQD must
reproduce the CASCI anchor (Gate 0b) and DFT must be shown unreliable (Gate 0c).
"""
from __future__ import annotations

import math

from ..chem import active_space, dft, geometry, scf
from ..constants import STATEVECTOR_WALL_QUBITS
from ..quantum import ansatz, sampling, sqd
from ..runtime import Context
from . import plots
from .errors import GateFailure
from .results import Stage0Result


def run(ctx: Context) -> Stage0Result:
    s = ctx.settings
    ctx.log("==== STAGE 0: Fe(II)-porphyrin (VALIDATION, <40q => not advantage) ====")

    atoms = geometry.iron_porphine()
    ctx.decide("Stage0 geometry", "idealized D4h Fe-porphine",
               "not literature-pinned; idealized planar core. Comparability caveat.")

    # Quintet (2S=4) is the DMRG-reference ground state.
    mf = scf.run_rohf(ctx, scf.build_mol(atoms, spin=4, basis=s.basis), tag="fep_quintet")

    # Active space = Fe 3d + 4d double shell (sets the spin-state ordering).
    a = active_space.build(ctx, mf, ["Fe 3d", "Fe 4d"], spin=4, want_casci=True)
    if a.n_qubits < 20:
        raise GateFailure(f"Stage0 only {a.n_qubits}q; double shell not in the box.")
    if a.e_casci is None:
        raise GateFailure("CASCI anchor unavailable (Gate 0a).")
    ctx.log(f"GATE 0a PASSED: CASCI anchor = {a.e_casci:.8f} Ha")

    # --- Samplers (all share ffsim's JW convention) ---------------------- #
    circuit = ansatz.build_lucj(ctx, mf, a)
    quantum_is_fallback = False
    if circuit is not None and a.n_qubits <= STATEVECTOR_WALL_QUBITS:
        q_bits = sampling.statevector(ctx, circuit, s.shots, gpu=ctx.gpu_available())
    elif circuit is not None:
        q_bits = sampling.mps(ctx, circuit, s.shots)
    else:
        quantum_is_fallback = True
        q_bits = sampling.classical_wavefunction(ctx, a.ci, a.ncas, a.nelec, s.shots,
                                                 seed=s.seed)

    # Classical-sampling control (Stage 0.5): determinants from the CASCI vector.
    c_bits = sampling.classical_wavefunction(ctx, a.ci, a.ncas, a.nelec, s.shots,
                                             seed=s.seed)
    ctx.decide("classical control", "implemented (Stage 0)",
               "pre-empts the 'quantum is just a random determinant generator' critique")

    # --- Convergence sweeps (the curve is the result) -------------------- #
    q_curve = sqd.subspace_sweep(ctx, a, q_bits, s.stage0_sweep,
                                 s.sqd_num_batches, s.sqd_max_iterations, s.seed)
    c_curve = sqd.subspace_sweep(ctx, a, c_bits, s.stage0_sweep,
                                 s.sqd_num_batches, s.sqd_max_iterations, s.seed)
    e_sqd = min((e for _, e in q_curve), default=math.nan)

    result = Stage0Result(
        n_qubits=a.n_qubits, ncas=a.ncas, nelec=a.nelec, basis=s.basis,
        e_casci=a.e_casci, e_sqd_noiseless=e_sqd,
        quantum_curve=q_curve, classical_curve=c_curve,
        quantum_is_fallback=quantum_is_fallback,
    )

    # --- Gate 0b: SQD must reproduce CASCI within chemical accuracy ------- #
    if not math.isnan(e_sqd) and abs(e_sqd - a.e_casci) < s.chem_acc_ha:
        result.gate_0b_passed = True
        ctx.log(f"GATE 0b PASSED: SQD {e_sqd:.6f} vs CASCI {a.e_casci:.6f} "
                f"(dE={1000 * (e_sqd - a.e_casci):+.2f} mHa)")
    else:
        ctx.save("stage0_result", result)
        raise GateFailure(
            f"SQD ({e_sqd:.6f}) != CASCI ({a.e_casci:.6f}) beyond chemical accuracy. "
            "Bug in the quantum stack (ansatz/mapping/solver convention). "
            "DO NOT PROCEED TO HARDWARE.")

    plots.sqd_convergence(ctx, q_curve, c_curve, casci=a.e_casci,
                          title=f"Stage 0: SQD convergence (FeP, {a.n_qubits}q)",
                          fname="fig2_sqd_convergence.png")

    # --- DFT failure figure (Gate 0c): triplet vs quintet ---------------- #
    gaps = dft.spin_gap_scan(ctx, atoms, s.basis, spin_low=2, spin_high=4, tag="fep")
    result.dft_gaps = gaps
    if gaps:
        ctx.log(f"DFT spread across functionals = {result.dft_spread:.2f} kcal/mol")
        plots.dft_gap(ctx, gaps, "Fe(II)-porphyrin", "triplet", "quintet",
                      "fig1_dft_gap.png")
        from ..constants import HARTREE_TO_KCAL
        if result.dft_spread <= s.chem_acc_ha * HARTREE_TO_KCAL:
            ctx.save("stage0_result", result)
            raise GateFailure("DFT functionals agree -> no classical failure to exploit.")
        result.gate_0c_passed = True
        ctx.log("GATE 0c PASSED: DFT is demonstrably unreliable on this system.")

    ctx.save("stage0_result", result)
    ctx.log("==== STAGE 0 COMPLETE ====")
    return result
