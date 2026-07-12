# qbind — SQD-corrected drug rescoring, with a quantified quantum-vs-classical delta

Rescore approved/clinical drugs against a metalloenzyme pocket by correcting the
**one strongly-correlated fragment** (metal center / radical) with a
correlated/quantum solver, and answer the actual research question:

> **did the quantum-computed correction change the ranking versus classical-only,
> and by how much — and toward experiment?**

That comparison, not the ranking itself, is the contribution at this stage.

The pipeline runs **end-to-end today in reference mode** (synthetic study, no
external tools) and produces all the graphs. Real target, docking, and QM
embedding plug in behind adapter interfaces. This is the pilot "vertical slice"
— prove the plumbing and the delta first, then swap in real components.

## Run it (30 seconds, produces graphs)

```bash
pip install -e .            # numpy/scipy/matplotlib/pandas only — no quantum stack
qbind run --out ./out       # reference pilot
# -> ./out/figures/*.png  and  ./out/results/REPORT.md
```

Or from Python:

```python
import qbind
result, report, figs = qbind.run("./out")
print(report.verdict)       # e.g. "Ranking changed AND moved toward experiment (+0.045)"
```

## Two run modes

**Reference mode** (`qbind run`) — synthetic study, no external tools. Validates
the plumbing + graphs. Not science.

**Molecular mode** (`qbind molecular`) — REAL interaction energies on small
metal-ligand CLUSTERS (a cluster model of the active site), so the real solvers
run without a protein:

```bash
qbind molecular --backend analytic --out ./mol   # no deps: plumbing demo
qbind molecular --backend casscf   --out ./mol   # REAL result, needs pyscf (no quantum computer)
qbind molecular --backend sqd      --out ./mol   # quantum solver, needs pyscf+qiskit+ffsim (reuses qadv)
```

| backend | classical baseline | correlated | needs | status |
|---|---|---|---|---|
| `analytic` | toy | toy+metal term | nothing | runs anywhere (demo) |
| `dft`    | UKS | UKS | `pyscf` | sanity (≈no change) |
| `casscf` | UKS | AVAS+CASSCF | `pyscf` | **real first result, no QC** |
| `sqd`    | UKS | SQD (qadv) | `pyscf,qiskit,ffsim` | quantum path |

Interaction energy is `E(AB) − E(A) − E(B)` with one backend; baseline uses DFT,
corrected uses the correlated backend, and only the strongly-correlated fragment
is re-treated — so the delta is a clean measurement of the correction.

## The graphs you get

| file | what it answers |
|---|---|
| `fig1_baseline_vs_expt.png`  | classical-only accuracy vs measured affinity |
| `fig2_corrected_vs_expt.png` | quantum-corrected accuracy vs measured affinity |
| `fig3_correlation_improvement.png` | **headline:** did agreement with experiment improve? |
| `fig4_ranking_change.png`    | slopegraph of baseline→corrected rank (Kendall-τ) |
| `fig5_per_ligand_delta.png`  | which ligands moved, and by how much (kcal/mol) |
| `fig6_fragment_diagnostic.png` | which fragment justified the quantum solver |

## Honesty is built in

- **The delta is a clean measurement.** Baseline and corrected differ ONLY by the
  strongly-correlated fragment's term; everything else cancels (enforced in
  `scoring/rescore.py`, tested in `tests/test_rescore_consistency.py`).
- **It won't manufacture a win.** The reference model has a `systematic_bias` knob:
  set it > 0 (DFT's known metal–ligand error) and the correction helps; set it 0
  and the report says "no improvement / not helping." Both are tested.
- **Ranking change alone is not the claim** — improvement *toward experiment* is.
  The verdict logic distinguishes them.

## Architecture (stage interfaces → swap reference for real tools)

```
src/qbind/
├── config.py / runtime.py / models.py / interfaces.py   core + Protocols
├── data/         reference.py (synthetic study), benchmark.py (CSV → Ligand)
├── classical/    docking.py (Vina adapter + reference), baseline.py (DFT + reference)
├── qm/           region.py, embedding.py (FMO/DMET), diagnostics.py, correlated.py
│                 (ReferenceCorrelatedSolver | CASSCFCorrelatedSolver | SQDCorrelatedSolver→qadv)
├── scoring/      delta.py (THE analysis), rescore.py (consistency), complementarity.py
└── pipeline/     orchestrator.py, plots.py (the graphs), report.py
configs/          reference.json (signal), reference_null.json (honest null)
tests/            delta, rescore-consistency, end-to-end reference (+ qadv tests)
src/qadv/         the SQD kernel (reused by SQDCorrelatedSolver)
```

## Phase status (what runs today vs what needs wiring)

| phase | piece | where | runs now? |
|---|---|---|---|
| 3 | classical DFT energies | `chem/backends.py::DFTBackend` | needs `pyscf` |
| 3 | **CASSCF correlated solver** | `chem/backends.py::CASSCFBackend` | needs `pyscf` |
| 5 | **SQD correlated solver** | `chem/backends.py::SQDBackend` (→`qadv`) | needs `pyscf,qiskit,ffsim` |
| 2 | cluster carving (mech. embedding) | `chem/cluster.py` | **yes** (pure) |
| 2 | full DMET/FMO embedding | `qm/embedding.py::DMETEmbedder` | stub (upgrade) |
| 1 | Vina docking | `classical/docking.py::VinaDockingEngine` | needs `vina` |
| — | analysis + graphs + report | `scoring/`, `pipeline/` | **yes** |

The molecular cluster path (`chem/`) is real, runnable chemistry that skips
docking + protein QM/MM — it is the honest way to get a first CASSCF/SQD result.
The protein path (Vina + full DMET) is the later scale-up.

## Going from cluster pilot to a full protein study

1. Pick a target where the correlated center is **in the pocket** (a P450, a
   Zn/Fe metalloenzyme). Assemble a benchmark CSV (`data/benchmark.py` schema).
2. Dock with `classical/docking.py::VinaDockingEngine` (needs `vina`).
3. Build a real region + DMET/FMO embedding (`qm/embedding.py::DMETEmbedder`) to
   replace the cluster carving with electrostatic embedding.
4. **Answer the question classically first** (`--backend casscf`). You do not need
   a quantum computer to learn whether the correction moves rankings.
5. Only when a fragment exceeds classical exact reach, switch to `--backend sqd`
   (reuses the `qadv` kernel; emulate first, hardware last).

The consistency rule holds throughout: change only the correlated fragment's
solver between baseline and corrected, or the delta stops meaning anything.

## Tests

```bash
pip install -e ".[dev]" && pytest      # 39 tests, none require the quantum-chem stack
```
