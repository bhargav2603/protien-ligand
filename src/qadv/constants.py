"""Physical facts and numerical tolerances. These are not tunable opinions.

The three "wall" constants encode constraints from physics (see the project
brief, Part B). They are enforced by assertions in the pipeline and must never
be relaxed to make a result look better.
"""
from __future__ import annotations

# Unit conversions.
HARTREE_TO_KCAL = 627.5094740631

# Chemical accuracy: the SQD-vs-CASCI tolerance for Gate 0b (~1 kcal/mol).
CHEM_ACC_HA = 1.6e-3

# --- Physical walls (Part B) ---------------------------------------------- #
# Below this qubit count, exact FCI solves the active space; any result is a
# reproduction, never a quantum-advantage claim.
EXACT_DIAG_WALL_QUBITS = 40

# Above this qubit count, a dense statevector is not representable anywhere
# (2**42 amplitudes ~ 70 TB). Never attempt statevector simulation past here.
STATEVECTOR_WALL_QUBITS = 32
