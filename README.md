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

## Going from pilot to a real study

1. Pick a target where the correlated center is **in the pocket** (a P450, a
   Zn/Fe metalloenzyme). Assemble a benchmark CSV (`data/benchmark.py` schema).
2. Set `docking="vina"` and wire `classical/docking.py::VinaDockingEngine`.
3. Set `embedding` to a real DMET/FMO build (`qm/embedding.py::DMETEmbedder`) that
   exposes each fragment's embedded integrals.
4. **Answer the question classically first:** `correlated_solver="casscf"`. You do
   not need a quantum computer to learn whether the correction moves rankings.
5. Only when a fragment exceeds classical exact reach, switch to
   `correlated_solver="sqd"` (reuses the `qadv` kernel; emulated first, hardware last).

The consistency rule holds throughout: change only the correlated fragment's
solver between baseline and corrected, or the delta stops meaning anything.

## Tests

```bash
pip install -e ".[dev]" && pytest      # 26 tests, none require the quantum-chem stack
```
