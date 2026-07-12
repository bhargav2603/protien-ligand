# The two study targets — real drugs, structures, and data recipe

We run two metalloenzyme active sites:

- **Primary — Cytochrome P450 (heme Fe) + azoles.** Fe is genuinely correlated
  (the doublet/quartet spin-state near-degeneracy is a canonical DFT failure).
  Azole drugs bind by coordinating the heme Fe through a ring nitrogen, so the
  binding event sits **on** the correlated centre. This is where the quantum
  correction can have a real signal.
- **Control — Carbonic anhydrase II (Zn) + sulfonamides.** Zn²⁺ is d¹⁰
  closed-shell → essentially no static correlation. The method should report
  **≈ no correlated effect** here. That negative control is what makes the
  primary result credible.

## What ships in this repo (idealized starter models)

`examples/p450_azoles/` and `examples/ca2_sulfonamides/` contain runnable
`study.json` + `.xyz` **idealized** cluster models:

- P450: Fe-porphine + axial thiolate (SH⁻, a Cys proxy) + a 6th-site N-donor.
  Encoded spin crossover: fragment 5-coordinate **high-spin S=5/2**, complex
  6-coordinate **low-spin S=1/2**.
- CA-II: Zn²⁺ + 3 NH₃ (a His₃ proxy) + a coordinating inhibitor; all closed shell.

The ligands shipped are **minimal N-donor / sulfonamide proxies** (ammonia,
methylamine, pyridine; ammonia, methylamine, methanesulfonamide) so the pipeline
runs today. `experimental_dg` is `null` — **we do not ship fabricated affinities.**

## The real drugs to use (replace the proxies)

**P450 azoles (N coordinates Fe):** fluconazole, voriconazole, itraconazole,
posaconazole (antifungals, CYP51), and ketoconazole / clotrimazole. For a
human drug-metabolism CYP (CYP3A4, CYP2C9), use an azole inhibitor congeneric
series from one assay.

**CA-II sulfonamides (deprotonated N coordinates Zn):** acetazolamide,
methazolamide, ethoxzolamide, dorzolamide, brinzolamide, benzolamide, plus a
plain benzenesulfonamide series (Supuran datasets are unusually consistent).

## How to make these into a *real* study (3 steps)

1. **Geometry (existing structure → your optimization).** Pull the bound pose
   from the PDB complex (e.g. CYP51 human `3LD6`; CYP3A4 apo `1TQN` and its
   ketoconazole/ritonavir complexes; CA-II apo `2CBA`/`1CA2` and inhibitor
   complexes such as acetazolamide and dorzolamide). Carve the cluster (metal +
   first shell + inhibitor), cap dangling bonds with H, and **DFT-optimize**
   (B3LYP/def2-SVP). Save each complex as an `.xyz` and point `complex_xyz` at it.
2. **Affinities (already-taken).** Pull measured Kᵢ/Kd/IC50 for that exact
   pocket from **ChEMBL** or **BindingDB**, prefer one assay/lab, convert to dG
   (`qbind.data.benchmark.ki_to_dg`), and write it into each ligand's
   `experimental_dg` (kcal/mol).
3. **Fragment / spin / charge.** In `study.json`, `fragment_atoms` = the metal +
   its first coordination shell; set `charges`/`spins` per piece. For P450 keep
   the high-spin fragment / low-spin complex crossover; for CA-II everything is
   spin 0. The loader validates electron/spin parity and will flag mistakes.

## Running

```bash
# idealized demo (no deps):
qbind input --file input_p450.json          # or input_ca2.json
# real result once geometries + affinities are in (needs pyscf):
#   set "backend": "casscf" in the input file, then:
qbind input --file input_p450.json
# quantum path (needs pyscf+qiskit+ffsim):  set "backend": "sqd"
```

## Honest caveats

- Shipped geometries are **idealized**, not literature coordinates — optimize
  before any production number.
- Shipped `experimental_dg` is **null** — fill from ChEMBL/BindingDB.
- Minimal ligand proxies are **not** the real drugs — swap them in.
- CASSCF/SQD on the open-shell Fe site will need active-space and SCF
  convergence tuning; the spin-crossover makes E(AB)−E(A)−E(B) spin-state
  dependent (that is the physics, not a bug).
