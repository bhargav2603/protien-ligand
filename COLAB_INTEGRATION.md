# Running this pipeline in Google Colab

The pipeline is a proper installable package (`src/qadv`). Colab is just a thin
driver: **install the package + its science extra → call it.** Nothing
scientific is duplicated in the notebook, so the same code runs on Colab, a
workstation, or an HPC node.

Pick **one** "get the code" option (A or B), then run the cells below it.

---

## Cell 1 — get the code + install (upload, option A)

Zip the project folder on your machine (the folder containing `pyproject.toml`
and `src/`), then:

```python
from google.colab import files
up = files.upload()                         # pick your qadv.zip
import zipfile, io, glob, os
name = next(iter(up))
with zipfile.ZipFile(io.BytesIO(up[name])) as z:
    z.extractall('/content/code')
root = os.path.dirname(glob.glob('/content/code/**/pyproject.toml', recursive=True)[0])
%pip install -q -e "{root}[science]"        # installs qadv + pyscf/qiskit/ffsim/...
```

## Cell 1 — get the code + install (git, option B)

```python
!git clone https://github.com/<you>/<your-repo>.git /content/code
%pip install -q -e "/content/code[science]"
```

> GPU runtime recommended (Runtime → Change runtime type → GPU). On a GPU
> runtime also run `%pip install -q qiskit-aer-gpu`.

## Cell 2 — mount Drive (checkpoints/results survive disconnects)

```python
from google.colab import drive
drive.mount('/content/drive')
PROJ = '/content/drive/MyDrive/qchem_advantage'
```

## Cell 3 — (optional) IBM Quantum credentials

Skip to run the simulation path only; Stage 1 hardware phases are then marked
`PENDING_HARDWARE`.

```python
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform", token="YOUR_TOKEN", overwrite=True)
```

---

## Cell 4 — run

```python
import qadv
ctx = qadv.make_context(PROJ)     # one object carries all config + I/O

qadv.run_stage0(ctx)              # validation: FeP ~20q, CASCI anchor, DFT figure
qadv.build_report(ctx)            # writes results/REPORT.md
```

Then Stage 1 (advantage regime). Without IBM access it uses the MPS surrogate
(clearly labelled NOT advantage); with access it submits an async job and
returns — re-run the same cell later to retrieve:

```python
qadv.run_stage1(ctx, use_hardware=True)   # or use_hardware=False to force MPS
qadv.build_report(ctx)
```

Equivalent from a shell cell (the console script is installed):

```python
!QADV_PROJ="{PROJ}" qadv all --no-hardware
# or:  !python -m qadv stage0 --proj "{PROJ}"
```

---

## What lands in your Drive folder (`PROJ`)

```
qchem_advantage/
├── checkpoints/    *.pkl (typed results) + job_id_*.txt   (resume points)
├── results/        REPORT.md, cpd1_sqd_sweep.npy
├── figures/        fig1_dft_gap.png, fig2_sqd_convergence.png, fig2b_cpd1_convergence.png
├── logs/run.log
└── DECISIONS.md    every autonomous decision, with justification
```

## Resuming after a disconnect

Re-run the install + `make_context` cells and call the same `run_stageN(ctx)`.
Completed phases load from checkpoints; a submitted hardware job is retrieved by
its saved `job_id`. Never re-runs completed work.

## If a package version breaks an API call

Only two functions are version-sensitive:
`qadv.quantum.sqd._diagonalize_once` (the `qiskit-addon-sqd` call) and
`qadv.quantum.ansatz.build_lucj` (the `ffsim` LUCJ call). They target
`ffsim >= 0.0.55` and `qiskit-addon-sqd >= 0.10`. Everything else (SCF, AVAS,
CASCI, DFT, reporting) is unaffected. Gate 0b will catch a wrong integral
convention before any hardware credits are spent.
