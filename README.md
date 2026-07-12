# Quantum Advantage on Drug-Relevant Metalloenzymes (SQD pipeline)

Autonomous sample-based quantum diagonalization (SQD) pipeline targeting
cytochrome P450 **Compound I** — the intermediate behind most human drug
metabolism — with Fe(II)-porphyrin as the validation system.

An installable Python package, so it runs anywhere. Colab is only a thin driver:
see **[COLAB_INTEGRATION.md](COLAB_INTEGRATION.md)**.

## Architecture

Layered, with side effects isolated in a `Context` that every stage receives
(no global state), and the version-fragile third-party calls behind adapters.

```
src/qadv/
├── constants.py        physical walls + tolerances (not tunable)
├── settings.py         Settings: frozen dataclass of run config
├── runtime.py          Context: logging, DECISIONS journal, RAM guard, checkpoints
├── chem/
│   ├── geometry.py     pure idealized geometries (bond-length checked)
│   ├── scf.py          ROHF convergence-escalation ladder
│   ├── active_space.py AVAS + CASCI + integrals  ← single source of truth
│   └── dft.py          functional scan (Figure 1)
├── quantum/
│   ├── ansatz.py       LUCJ (consistent reference, then CCSD seed)
│   ├── sampling.py     statevector / MPS / classical samplers (one JW convention)
│   ├── sqd.py          diagonalisation adapter + subspace sweep
│   └── hardware.py     IBM async submit/retrieve + integrity check
└── pipeline/
    ├── results.py      typed Stage0Result / Stage1Result
    ├── stage0.py       validation
    ├── stage1.py       advantage attempt
    ├── plots.py        figures
    └── report.py       REPORT.md (mandatory disclaimers, actual qubit count)
tests/                  pure-logic tests (run without the science stack)
```

## Design decisions worth knowing (what changed from the first draft)

- **Single source of truth for integrals.** The SQD Hamiltonian and the CASCI
  anchor now come from the *same* `mcscf.CASCI` integrals (`active_space.build`).
  Previously they used two independent paths, so Gate 0b could fail on an
  integral-convention mismatch rather than a real quantum-stack bug.
- **Consistent MO reference for the ansatz.** `ansatz._prepare_reference` builds
  a mean-field copy whose `mo_coeff`/`mo_energy`/`mo_occ` all match the AVAS
  orbitals, instead of leaving stale post-SCF metadata on a mutated `mf`.
- **No global state.** `Context`/`Settings` are injected, making the pipeline
  unit-testable against a tmp directory.
- **Typed results + honest reporting.** The report reads the *actual* qubit count
  and withholds the headline claim until a ≥40-qubit Stage 1 result exists.
- **Adapters** isolate `qiskit-addon-sqd` and `ffsim` so a version bump touches
  one function each.

## The four physics constraints (enforced in code)

1. **40-qubit wall** — Stage 1 asserts `n_qubits >= 40`, else HALT (validation
   only, never advantage).
2. **Simulation wall** — `sampling.statevector` refuses above 32 qubits.
3. **Noise-cancellation trap** — `hardware.integrity_check` red-flags hardware
   beating the noiseless reference.
4. **We do not beat DMRG** — stated unprompted in every generated report.

## Quick start (local, no hardware)

```bash
pip install -e ".[science]"
qadv stage0 --proj ./out
qadv report --proj ./out
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The tests cover geometry, helpers, Context I/O, and report generation — none
require the quantum-chemistry stack.

## Honest limitations (logged to DECISIONS.md at runtime)

- Geometries are **idealized**, not literature-pinned. Replace `chem/geometry.py`
  outputs with SI/optimized coordinates for publication.
- Stage 1's active space is selected by AVAS to land in the ≥40-qubit regime; the
  exact orbital set is environment-dependent and logged.
- If the LUCJ ansatz fails to build, sampling falls back to the classical
  wavefunction and the report says so — the energy is unaffected because it comes
  from the CASCI-consistent integrals, not the ansatz.
