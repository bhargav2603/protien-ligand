"""Bundled illustrative metal-ligand clusters for the molecular pipeline.

ILLUSTRATIVE ONLY. The geometries are idealized (metal at origin, ligand along
+z at a nominal binding distance) and the spin/charge are set to a single simple
state; the `experimental_dg` values are placeholders, NOT measured affinities.
They exist so the real DFT/CASSCF/SQD backends have something to run on without a
protein, and so the demo produces all six graphs. Replace with real active-site
clusters and real affinities for science.
"""
from __future__ import annotations

from .geometry import Geometry
from .interaction import InteractionJob

_FE_SPIN = 4          # illustrative quintet Fe centre
_FE_D = 2.0           # nominal Fe-ligand distance (Angstrom)


def _fe() -> Geometry:
    return Geometry(atoms=(("Fe", (0.0, 0.0, 0.0)),), charge=0, spin=_FE_SPIN, name="Fe")


# ligand -> (atoms placed with coordinating atom at z=_FE_D, charge, illustrative dG)
_LIGANDS = {
    "CO":  ([("C", (0, 0, _FE_D)), ("O", (0, 0, _FE_D + 1.13))], 0, -12.0),
    "CN":  ([("C", (0, 0, _FE_D)), ("N", (0, 0, _FE_D + 1.16))], -1, -11.5),
    "HCN": ([("N", (0, 0, _FE_D)), ("C", (0, 0, _FE_D + 1.16)),
             ("H", (0, 0, _FE_D + 2.22))], 0, -10.0),
    "NH3": ([("N", (0, 0, _FE_D)), ("H", (0.94, 0, _FE_D + 0.33)),
             ("H", (-0.47, 0.82, _FE_D + 0.33)), ("H", (-0.47, -0.82, _FE_D + 0.33))], 0, -9.0),
    "N2":  ([("N", (0, 0, _FE_D)), ("N", (0, 0, _FE_D + 1.10))], 0, -8.5),
    "H2S": ([("S", (0, 0, _FE_D)), ("H", (0.96, 0, _FE_D + 0.75)),
             ("H", (-0.96, 0, _FE_D + 0.75))], 0, -7.5),
    "H2O": ([("O", (0, 0, _FE_D)), ("H", (0.76, 0, _FE_D + 0.59)),
             ("H", (-0.76, 0, _FE_D + 0.59))], 0, -7.0),
    "CO2": ([("O", (0, 0, _FE_D)), ("C", (0, 0, _FE_D + 1.16)),
             ("O", (0, 0, _FE_D + 2.32))], 0, -6.0),
}


def example_jobs(with_experimental: bool = True) -> list[InteractionJob]:
    """Fe + small-ligand clusters as interaction jobs (A=Fe, B=ligand, AB=both)."""
    fe = _fe()
    jobs: list[InteractionJob] = []
    for name, (atoms, charge, dg) in _LIGANDS.items():
        ligand = Geometry(atoms=tuple(atoms), charge=charge, spin=0, name=name)
        complex_ab = Geometry(atoms=fe.atoms + ligand.atoms, charge=charge,
                              spin=_FE_SPIN, name=f"Fe-{name}")
        jobs.append(InteractionJob(
            ligand_id=name, complex_ab=complex_ab, fragment_a=fe, ligand_b=ligand,
            is_strongly_correlated=True,
            experimental_dg=(dg if with_experimental else None)))
    return jobs
