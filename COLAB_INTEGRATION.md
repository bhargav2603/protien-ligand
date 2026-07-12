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

## Cell 2 — run the pilot (produces the graphs)

```python
import qbind
result, report, figs = qbind.run("/content/out")
print("VERDICT:", report.verdict)
```

## Cell 3 — view the graphs inline

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

## Moving from cluster pilot to a full protein study (later, needs Vina + DMET)

Install the extra and swap stages via a config:

```python
%pip install -q -e "{root}[science]"        # pyscf, qiskit, qiskit-addon-sqd, ffsim
```

Then wire `docking="vina"`, a real `embedding`, and `correlated_solver="casscf"`
(answer the question classically first) or `"sqd"` (reuses `qadv`; emulate first,
hardware last). The adapters and their plug points are in
`src/qbind/classical/docking.py` and `src/qbind/qm/`.

## Outputs (under the out dir you pass)

```
out/
├── figures/    fig1..fig6 PNGs
├── results/    REPORT.md, delta_report.json, ranked_candidates.json
├── checkpoints/ study_result.pkl, delta_report.pkl
├── run.log
└── DECISIONS.md
```
