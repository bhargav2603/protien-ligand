"""Synthetic reference study for PLUMBING VALIDATION ONLY.

This is not a scientific result. It is a transparent model that lets the whole
pipeline run end-to-end and emit the graphs with no external tools, and lets you
see both possible outcomes:

* With `systematic_bias > 0`: DFT makes a *systematic* error on ligands that
  coordinate the strongly-correlated fragment (a real, known failure mode of
  DFT on metal-ligand bonds). The correlated solver removes it, so the corrected
  ranking moves toward experiment -- the effect the real pipeline hopes to find.
* With `systematic_bias = 0` and matched noise: the correction changes nothing.
  That is the honest null, and the delta report will say so.

Everything shared between baseline and corrected (docking, complementarity, weak
fragments) cancels in the delta, exactly as it must in the real pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import ReferenceModel
from ..models import FragmentSpec, Ligand

STRONG_FRAGMENT = "metal-center"
WEAK_FRAGMENTS = ("axial-ligand", "backbone")


@dataclass
class ReferenceStudy:
    ligands: list[Ligand]
    docking: dict[str, float]
    fragments: list[FragmentSpec]
    classical_terms: dict[tuple[str, str], float]
    correlated_terms: dict[tuple[str, str], float]
    meta: dict = field(default_factory=dict)


def build(model: ReferenceModel) -> ReferenceStudy:
    rng = np.random.default_rng(model.seed)
    n = model.n_ligands
    n_coord = max(1, round(n * model.fraction_coordinating))
    coord_flags = np.array([True] * n_coord + [False] * (n - n_coord))
    rng.shuffle(coord_flags)

    ligands: list[Ligand] = []
    docking: dict[str, float] = {}
    classical_terms: dict[tuple[str, str], float] = {}
    correlated_terms: dict[tuple[str, str], float] = {}

    for i in range(n):
        lid = f"LIG{i:02d}"
        expt = float(rng.uniform(-11.0, -6.0))          # measured dG (truth)
        coord = bool(coord_flags[i])
        ligands.append(Ligand(ligand_id=lid, name=lid, smiles="",
                              experimental_dg=expt, coordinates_fragment=coord))

        # Docking backbone: a crude but shared predictor (same in both scores).
        docking[lid] = expt + float(rng.normal(0, model.classical_noise))

        # Weak fragments: identical classical/correlated => cancel in the delta.
        for wf in WEAK_FRAGMENTS:
            v = float(rng.normal(0, 0.2))
            classical_terms[(lid, wf)] = v
            correlated_terms[(lid, wf)] = v

        # Strong fragment: only coordinating ligands actually contact it.
        if coord:
            k = model.systematic_bias + float(rng.normal(0, model.classical_noise * 0.5))
            q = float(rng.normal(0, model.correlated_noise))   # bias removed by correlation
        else:
            k = 0.0
            q = 0.0
        classical_terms[(lid, STRONG_FRAGMENT)] = k
        correlated_terms[(lid, STRONG_FRAGMENT)] = q

    fragments = [
        FragmentSpec(STRONG_FRAGMENT, atom_indices=(0, 1, 2, 3, 4, 5),
                     is_strongly_correlated=True,
                     no_occupations=(1.98, 1.72, 1.31, 0.69, 0.28, 0.02)),
        FragmentSpec("axial-ligand", atom_indices=(6, 7, 8),
                     no_occupations=(1.99, 0.01)),
        FragmentSpec("backbone", atom_indices=(9, 10, 11, 12),
                     no_occupations=(2.0, 0.0)),
    ]
    return ReferenceStudy(
        ligands=ligands, docking=docking, fragments=fragments,
        classical_terms=classical_terms, correlated_terms=correlated_terms,
        meta=dict(n_coordinating=int(coord_flags.sum()),
                  systematic_bias=model.systematic_bias),
    )
