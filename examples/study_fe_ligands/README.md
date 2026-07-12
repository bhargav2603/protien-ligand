# Example study: Fe + small ligands (ILLUSTRATIVE)

A runnable `study.json` template for the molecular-cluster pipeline. **Not
science** — idealized geometries, a single fixed spin state (quintet Fe), and
placeholder `experimental_dg` values. Replace the `.xyz` files, charges/spins,
and affinities with your real active-site clusters and measured data.

## Run it

```bash
# no dependencies (plumbing demo):
qbind molecular --study examples/study_fe_ligands/study.json --backend analytic --out ./out

# real DFT-vs-CASSCF result (needs pyscf):
qbind molecular --study examples/study_fe_ligands/study.json --backend casscf --out ./out
```

## study.json fields

- `chemistry.ao_labels` — AVAS labels selecting the correlated fragment's active
  orbitals (e.g. `["Fe 3d","Fe 4d"]`, or `["Zn 3d"]` for a different metal).
- per ligand:
  - `complex_xyz` — geometry of fragment + ligand together (or inline `atoms`).
  - `fragment_atoms` — 0-based indices of the correlated fragment (metal + shell).
  - `ligand_atoms` — indices of the ligand; `null` = everything else.
  - `charges` / `spins` — for `fragment`, `ligand`, `complex` (`spin` = 2S).
  - `experimental_dg` — measured binding dG in kcal/mol (optional; enables the
    vs-experiment graphs).

The loader validates electron/spin **parity** only. Correct spin states and
CASSCF convergence are your responsibility — expect to tune these on real metals.
