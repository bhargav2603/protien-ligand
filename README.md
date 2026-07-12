# qbind — SQD-corrected drug rescoring, with a quantified quantum-vs-classical delta

Rescore approved/clinical drugs against a metalloenzyme pocket by correcting the
**one strongly-correlated fragment** (metal center / radical) with a
correlated/quantum solver, and answer the actual research question:

> **did the quantum-computed correction change the ranking versus classical-only,
> and by how much — and toward experiment?**

That comparison, not the ranking itself, is the contribution at this stage.

You drive everything from **one file, `input.json`**. Two modes: `reference`
(synthetic, no external tools — validates the plumbing + graphs) and `molecular`
(REAL interaction energies on small metal-ligand clusters via DFT/CASSCF/SQD).
Both run end-to-end today and produce all the graphs. The full protein path
(Vina docking + DMET embedding) plugs in behind adapter interfaces as the
scale-up.

## Run it — edit ONE file, then one command

`input.json` at the repo root is the only file you edit. Change values, rerun,
outputs change — no code edits.

```bash
pip install -e .      # numpy/scipy/matplotlib/pandas only — no quantum stack
qbind input           # reads ./input.json -> ./out/figures/*.png + ./out/results/REPORT.md
```

```json
// input.json
{
  "mode": "molecular",        // "reference" (synthetic) | "molecular" (real geometries)
  "output_dir": "./out",
  "backend": "analytic",      // analytic (no deps) | dft | casscf | sqd
  "study_file": "examples/study_fe_ligands/study.json",
  "reference": { "n_ligands": 18, "systematic_bias": 1.8, "seed": 7 }
}
```

Physics constants (the 40-qubit wall, chemical-accuracy threshold, …) are
deliberately NOT in `input.json` — they live in `src/qbind/constants.py` because
they are invariants, not inputs.

From Python, or the direct subcommands, if you prefer:

```python
import qbind
from qbind.input_spec import run_from_input
run_from_input("input.json")                       # same as `qbind input`
qbind.run_molecular("./out", backend="casscf", study_file="…/study.json")
```
```bash
qbind run --out ./out                               # reference-mode shortcut
qbind molecular --study …/study.json --backend casscf --out ./out
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

Every run also writes **`results/dashboard.html`** — a single self-contained
interactive page (KPIs, hover tooltips, ranking slopegraph, per-ligand
correction, ranked table, and a sensitivity sweep), light/dark aware, no external
assets. Open it, download it, or share it. Build one for any result:

```python
import qbind
res, rep, figs = qbind.run("./out")                 # dashboard.html emitted automatically
qbind.dashboard(res, rep, "./out/results/dashboard.html", reference_mode=True)

# sensitivity sweep (the honest antidote to slider cherry-picking):
qbind.sweep(biases=[0, 0.5, 1, 1.5, 2, 2.5, 3])     # improvement vs DFT error

# live sliders in Colab/Jupyter (reference mode only — it's cheap enough to recompute):
from qbind.viz.explorer import reference_explorer
reference_explorer()
```

Live sliders work only for the fast synthetic/analytic path. Real CASSCF/SQD is
too slow to recompute behind a slider — for that, precompute a grid with
`qbind.sweep` and scrub the cache.

## Honesty is built in

- **The delta is a clean measurement.** Baseline and corrected differ ONLY by the
  strongly-correlated fragment's term; everything else cancels (enforced in
  `scoring/rescore.py`, tested in `tests/test_rescore_consistency.py`).
- **It won't manufacture a win.** The reference model has a `systematic_bias` knob:
  set it > 0 (DFT's known metal–ligand error) and the correction helps; set it 0
  and the report says "no improvement / not helping." Both are tested.
- **Ranking change alone is not the claim** — improvement *toward experiment* is.
  The verdict logic distinguishes them.

## Architecture (one input file → typed objects → injected everywhere)

```
input.json        THE file you edit (run params only; NOT physics constants)
src/qbind/
├── input_spec.py  RunInput: load+validate input.json, dispatch to a study
├── constants.py   physics invariants (walls, chemical accuracy) — not user-tunable
├── config.py / runtime.py / models.py / interfaces.py   core + Protocols
├── chem/          RUNNABLE molecular path:
│                  geometry.py, cluster.py (carve), interaction.py (E_AB−E_A−E_B),
│                  backends.py (Analytic|DFT|CASSCF|SQD energies), loader.py (study.json),
│                  study.py (driver), examples.py (bundled clusters)
├── data/          reference.py (synthetic study), benchmark.py (CSV → Ligand)
├── classical/     docking.py (Vina adapter + reference), baseline.py
├── qm/            protein/DMET path (upgrade): region.py, embedding.py, diagnostics.py,
│                  correlated.py  (integral-driven; runnable solvers are in chem/backends.py)
├── scoring/       delta.py (THE analysis), rescore.py (consistency), complementarity.py
├── pipeline/      orchestrator.py, plots.py (static PNGs), report.py
└── viz/           self-contained interactive dashboard (theme.py design system,
                   svg.py charts, dashboard.py, sweep.py, explorer.py live sliders)
examples/study_fe_ligands/   study.json + xyz template (real-input format)
configs/          reference.json (signal), reference_null.json (honest null)
src/qadv/         the SQD kernel (reused by chem/backends.py::SQDBackend)
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
pip install -e ".[dev]" && pytest      # 59 tests, none require the quantum-chem stack
```
