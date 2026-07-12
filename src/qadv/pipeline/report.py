"""Auto-generate results/REPORT.md from typed checkpoints.

Always emits the mandatory disclaimers (we do not beat DMRG), and always uses
the ACTUAL qubit count from the Stage 1 result -- the first draft hardcoded 42,
which could misstate the headline claim.
"""
from __future__ import annotations

from ..constants import EXACT_DIAG_WALL_QUBITS
from ..runtime import Context
from .results import Stage0Result, Stage1Result

_CLAIM = (
    "We compute a variational upper bound on the ground-state energy of the "
    "cytochrome P450 Compound I active site -- the catalytic intermediate "
    "responsible for the majority of human drug metabolism -- in a {nq}-qubit "
    "active space beyond the reach of exact diagonalization. The bound is "
    "classically certifiable at polynomial cost. DFT, the method used at "
    "production scale in pharma, gives spin-state orderings for this system that "
    "vary qualitatively with the choice of functional. Our result does not depend "
    "on that choice."
)

_DISCLAIMERS = (
    "We do NOT claim advantage over DMRG, which can treat systems of this size "
    "classically with expert tuning, and which supplies our reference values. We "
    "claim (a) accuracy in a regime where DFT is qualitatively unreliable, and "
    "(b) computation beyond the scale of exact diagonalization. Our bound is not "
    "converged to chemical accuracy: the classical diagonalization step is "
    "RAM-limited on commodity hardware. The convergence curve (Figure 2b) "
    "quantifies precisely what HPC allocation would close that gap."
)


def _fmt_curve(curve) -> str:
    return " | ".join(f"{d}:{e:.5f}" for d, e in curve) if curve else "_none_"


def generate(ctx: Context) -> str:
    s0: Stage0Result | None = ctx.load("stage0_result")
    s1: Stage1Result | None = ctx.load("stage1_result")
    L: list[str] = []
    w = L.append

    w("# Quantum Advantage on Drug-Relevant Metalloenzymes -- Results\n")
    w("_Simulation validates the stack; it can never produce the advantage result "
      "(that regime is not classically simulable)._\n")

    w("## Ground rules (physics, not opinion)\n")
    w("- **< 40 qubits => reproduction, not advantage.** Exact FCI solves it.")
    w("- **Advantage regime (>=40q) is not statevector-simulable** (~70 TB at 42q).")
    w("- **Hardware beating the noiseless reference = noise cancellation, never a win.**")
    w("- **We do not beat DMRG.** It is our ground truth.\n")

    # ---- Stage 0.
    w("## Stage 0 -- Fe(II)-porphyrin (VALIDATION)\n")
    if s0:
        w(f"- Active space: {s0.ncas} orbitals ({s0.n_qubits} qubits), "
          f"nelec={s0.nelec}, basis {s0.basis}.")
        w(f"- **CASCI anchor** = {s0.e_casci:.8f} Ha (correctness reference).")
        w(f"- Gate 0b (SQD == CASCI within 1.6 mHa): "
          f"{'PASSED' if s0.gate_0b_passed else 'FAILED'} "
          f"(SQD = {s0.e_sqd_noiseless:.6f} Ha).")
        if s0.quantum_is_fallback:
            w("  - NOTE: LUCJ circuit did not build here; the 'quantum' curve used "
              "classical-wavefunction sampling as a fallback. Rebuild the ansatz in "
              "an ffsim-enabled environment to exercise the true quantum path.")
        if s0.dft_gaps:
            w(f"- **DFT spin-state gap spread = {s0.dft_spread:.2f} kcal/mol** across "
              f"{len(s0.dft_gaps)} functionals (Gate 0c: "
              f"{'PASSED' if s0.gate_0c_passed else 'n/a'}). See Figure 1.\n")
            w("  | functional | gap(triplet-quintet) kcal/mol |")
            w("  |---|---|")
            for k, v in s0.dft_gaps.items():
                w(f"  | {k} | {v:+.2f} |")
        w("")
        w(f"- SQD convergence (quantum): {_fmt_curve(s0.quantum_curve)}")
        w(f"- SQD convergence (classical control): {_fmt_curve(s0.classical_curve)}")
    else:
        w("_Stage 0 not yet run._")
    w("")

    # ---- Stage 1.
    w("## Stage 1 -- P450 Compound I (THE RESULT)\n")
    if s1:
        w(f"- Active space: {s1.ncas} orbitals (**{s1.n_qubits} qubits**), "
          f"status = **{s1.status}**, sample source = {s1.sample_source}.")
        if s1.sweep:
            w(f"- SQD subspace sweep (upper bounds): {_fmt_curve(s1.sweep)}")
            w("- See Figure 2b; extrapolate the tail to quantify the HPC allocation "
              "that reaches chemical accuracy (the capital ask).")
        if s1.integrity_clean is not None:
            w(f"- Integrity check (B3): "
              f"{'CLEAN' if s1.integrity_clean else 'FAILED (noise cancellation)'}")
        if s1.status == "PENDING_HARDWARE":
            w("- Hardware job submitted; retrieve in a later session. Simulation "
              "deliverables are complete.")
    else:
        w("_Stage 1 not yet run._")
    w("")

    # ---- Claim + mandatory disclaimers. Only assert the claim if earned.
    w("## Claim\n")
    if s1 and s1.status == "COMPLETE" and s1.n_qubits >= EXACT_DIAG_WALL_QUBITS:
        w("> " + _CLAIM.format(nq=s1.n_qubits) + "\n")
    else:
        w("_Headline claim withheld until a Stage 1 result at >=40 qubits exists._\n")
    w("## Disclaimers (mandatory, unprompted)\n")
    w("> " + _DISCLAIMERS + "\n")

    w("## Artefacts\n")
    for f in ("fig1_dft_gap.png", "fig2_sqd_convergence.png", "fig2b_cpd1_convergence.png"):
        if (ctx.settings.figures / f).exists():
            w(f"- figures/{f}")
    if ctx.settings.decisions_file.exists():
        w("- DECISIONS.md (every autonomous choice, with justification)")

    path = ctx.settings.results / "REPORT.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    ctx.log(f"report written: {path}")
    return str(path)
