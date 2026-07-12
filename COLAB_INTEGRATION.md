# Running the pilot in Google Colab

Two installable packages live in `src/`:
- **`qbind`** — the drug-rescoring pipeline + graphs (the thing you run).
- **`qadv`** — the SQD kernel, reused by `qbind`'s `SQDCorrelatedSolver`.

The pilot (`qbind`) needs only numpy/scipy/matplotlib/pandas, so it runs and
produces graphs immediately — no quantum-chemistry stack required. Colab is a
thin driver: get the code, install, run.

## Cell 1 — get the code + install

Upload option: zip the project folder (the one with `pyproject.toml` and `src/`).

```python
from google.colab import files
up = files.upload()                         # pick your qbind.zip
import zipfile, io, glob, os
name = next(iter(up))
with zipfile.ZipFile(io.BytesIO(up[name])) as z:
    z.extractall('/content/code')
root = os.path.dirname(glob.glob('/content/code/**/pyproject.toml', recursive=True)[0])
%pip install -q -e "{root}"                 # pilot deps only
```

Git option:

```python
!git clone https://github.com/<you>/<your-repo>.git /content/code
%pip install -q -e /content/code
```

## Cell 2 — edit ONE input file, then run it

Edit `/content/code/input.json` (or write it from the notebook), then run. Change
values here and rerun — nothing else to touch.

```python
import json, os
inp = {
    "mode": "molecular",          # "reference" | "molecular"
    "output_dir": "/content/out",
    "backend": "analytic",        # analytic (no deps) | dft | casscf | sqd
    "study_file": "/content/code/examples/study_fe_ligands/study.json",
    "reference": {"n_ligands": 18, "systematic_bias": 1.8, "seed": 7},
}
json.dump(inp, open("/content/code/input.json", "w"), indent=2)

from qbind.input_spec import run_from_input
result, report, figs = run_from_input("/content/code/input.json")
print("VERDICT:", report.verdict)
```

## Cell 2b — the interactive dashboard (self-contained HTML)

Every run writes `results/dashboard.html`. Show it inline, or download it to
share:

```python
from IPython.display import IFrame, HTML
html = open("/content/out/results/dashboard.html", encoding="utf-8").read()
display(HTML(html))                       # renders inline (theme toggle, hover, sweep)
# or download:
from google.colab import files; files.download("/content/out/results/dashboard.html")
```

## Cell 2c — LIVE sliders (reference mode; recomputes in real time)

```python
from qbind.viz.explorer import reference_explorer
reference_explorer()      # drag DFT-bias / noise / #ligands / seed and watch it update
```

Live recompute works only for the synthetic path (milliseconds). For real
CASSCF/SQD, precompute a grid instead: `qbind.sweep(biases=[0,1,2,3])`.

## Cell 3 — view the static graphs inline

```python
from IPython.display import Image, display
for f in figs:
    display(Image(filename=f))
```

## Cell 4 — see both designed behaviours

```python
from qbind import Config, ReferenceModel, run
# signal: DFT has a systematic metal-ligand error the correction removes
run("/content/out_signal", Config(reference=ReferenceModel(systematic_bias=2.0)))
# honest null: nothing to fix -> report says so
run("/content/out_null",   Config(reference=ReferenceModel(systematic_bias=0.0,
                                   classical_noise=0.5, correlated_noise=0.5)))
```

## Cell 5 — molecular mode: REAL interaction energies (small clusters, no protein)

The `analytic` backend runs with no extra deps. For a real result install the
science extra and use `casscf` (no quantum computer needed):

```python
import qbind
# no-deps demo:
qbind.run_molecular("/content/mol_demo", backend="analytic")

# real correlated result (needs pyscf):
%pip install -q -e "{root}[science]"
qbind.run_molecular("/content/mol_casscf", backend="casscf")   # DFT vs CASSCF on Fe-ligand clusters
# quantum path (needs pyscf+qiskit+ffsim; reuses qadv SQD kernel):
# qbind.run_molecular("/content/mol_sqd", backend="sqd")
```

Each writes the same graph set + `REPORT.md`. Zip/download as in the earlier cell
(point it at the chosen out dir).

---

## Real result on your own clusters (needs pyscf)

Install the science extra, point `study_file` at your own `study.json` (see
`examples/study_fe_ligands/`), set `"backend": "casscf"` in `input.json`, rerun:

```python
%pip install -q -e "{root}[science]"        # pyscf (+ qiskit,qiskit-addon-sqd,ffsim for sqd)
```

`casscf` answers the research question with no quantum computer; `sqd` is the
quantum path (reuses `qadv`; emulate first, hardware last). Expect to tune
spin/charge/active space and SCF convergence on real metal clusters.

## Full protein study (later, needs Vina + DMET)

The docking (`src/qbind/classical/docking.py::VinaDockingEngine`) and DMET
embedding (`src/qbind/qm/embedding.py`) adapters are the scale-up from clusters
to a full pocket. They are the later step; the cluster path above is the first
real result.

## Outputs (under the out dir you pass)

```
out/
├── figures/    fig1..fig6 PNGs
├── results/    REPORT.md, delta_report.json, ranked_candidates.json
├── checkpoints/ study_result.pkl, delta_report.pkl
├── run.log
└── DECISIONS.md
```
