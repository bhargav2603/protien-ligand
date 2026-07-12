"""QM/MM region selection: carve a quantum-tractable region around the POCKET
(not the whole protein). Interface + reference no-op + a real adapter stub.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QMRegion:
    atom_indices: tuple[int, ...]
    charge: int
    spin: int
    description: str = ""


class ReferenceRegionBuilder:
    def build(self) -> QMRegion:
        return QMRegion(atom_indices=tuple(range(13)), charge=0, spin=0,
                        description="reference pocket region (synthetic)")


class DistanceRegionBuilder:  # pragma: no cover - needs a real structure
    """Select residues/atoms within `radius` of the ligand-contacting pocket.

    Real implementation reads the prepared structure, includes the metal + first
    coordination shell + pocket residues within `radius`, caps dangling bonds
    (hydrogen link atoms), and returns the QM region for embedding.
    """

    def __init__(self, structure_pdb: str, pocket_selection: str, radius: float = 5.0):
        self.structure_pdb = structure_pdb
        self.pocket_selection = pocket_selection
        self.radius = radius

    def build(self) -> QMRegion:
        raise NotImplementedError(
            "DistanceRegionBuilder needs a prepared structure and a QM/MM tool "
            "(pyscf.qmmm or an external driver). Use region via embedding='reference' "
            "for the pilot.")
