"""Cluster carving: turn a full structure + atom selections into an InteractionJob.

This is a *cluster / mechanical embedding* of the active site -- the honest,
runnable Phase-2 for the pilot. You give it the combined geometry and which atoms
are the (metal) fragment vs the ligand; it returns the AB / A / B pieces for the
interaction-energy calculation. Full DMET/FMO embedding (electrostatic + bath) is
the later upgrade in qm/embedding.py; this cluster model is what runs today.
"""
from __future__ import annotations

from .geometry import Geometry
from .interaction import InteractionJob


def carve(combined: Geometry, fragment_indices, ligand_indices,
          fragment_charge: int, fragment_spin: int,
          ligand_charge: int, ligand_spin: int,
          ligand_id: str, complex_spin: int | None = None,
          experimental_dg: float | None = None) -> InteractionJob:
    frag_idx = list(fragment_indices)
    lig_idx = list(ligand_indices)
    overlap = set(frag_idx) & set(lig_idx)
    if overlap:
        raise ValueError(f"fragment and ligand share atoms: {sorted(overlap)}")

    fragment = combined.subset(frag_idx, fragment_charge, fragment_spin, "fragment")
    ligand = combined.subset(lig_idx, ligand_charge, ligand_spin, ligand_id)
    ab = combined.subset(frag_idx + lig_idx, fragment_charge + ligand_charge,
                         complex_spin if complex_spin is not None else fragment_spin,
                         f"{ligand_id}-complex")
    return InteractionJob(
        ligand_id=ligand_id, complex_ab=ab, fragment_a=fragment, ligand_b=ligand,
        is_strongly_correlated=True, experimental_dg=experimental_dg)


def carve_by_distance(combined: Geometry, metal_index: int, radius: float = 3.0,
                      ligand_indices=None, **kw) -> InteractionJob:
    """Fragment = metal + atoms within `radius`; ligand = the given ligand atoms.

    Convenience for the common case: the correlated fragment is the metal plus its
    first coordination shell, and the ligand is passed explicitly.
    """
    import math
    mx = combined.atoms[metal_index][1]
    frag = [i for i, (_, r) in enumerate(combined.atoms)
            if math.dist(r, mx) <= radius and i not in set(ligand_indices or [])]
    if metal_index not in frag:
        frag.append(metal_index)
    return carve(combined, frag, list(ligand_indices or []), **kw)
