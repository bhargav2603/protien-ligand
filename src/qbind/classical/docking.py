"""Docking engines (DockingEngine protocol).

Poses are SEARCHED classically; we only reuse the resulting best pose + its
score, then rescore with quantum-corrected energies. We never use a quantum
method to search poses.
"""
from __future__ import annotations

from ..data.reference import ReferenceStudy
from ..models import Ligand


class ReferenceDockingEngine:
    """Returns the pre-generated reference docking score."""

    def __init__(self, study: ReferenceStudy):
        self._study = study

    def dock(self, ligand: Ligand) -> float:
        return self._study.docking[ligand.ligand_id]


class VinaDockingEngine:
    """AutoDock Vina adapter (real). Lazily imports so the package works without it.

    Expects a prepared receptor pdbqt and per-ligand pdbqt files; wire your own
    file resolution in `_ligand_pdbqt`. Returns Vina's best affinity (kcal/mol).
    """

    def __init__(self, receptor_pdbqt: str, ligand_dir: str,
                 center: tuple[float, float, float], box: tuple[float, float, float]):
        self.receptor_pdbqt = receptor_pdbqt
        self.ligand_dir = ligand_dir
        self.center = center
        self.box = box

    def _ligand_pdbqt(self, ligand: Ligand) -> str:
        return f"{self.ligand_dir}/{ligand.ligand_id}.pdbqt"

    def dock(self, ligand: Ligand) -> float:
        try:
            from vina import Vina
        except Exception as e:  # pragma: no cover - needs external tool
            raise RuntimeError(
                "AutoDock Vina not installed. `pip install vina`, or use "
                "docking='reference'.") from e
        v = Vina(sf_name="vina")
        v.set_receptor(self.receptor_pdbqt)
        v.set_ligand_from_file(self._ligand_pdbqt(ligand))
        v.compute_vina_maps(center=list(self.center), box_size=list(self.box))
        v.dock(exhaustiveness=8, n_poses=5)
        return float(v.energies(n_poses=1)[0][0])   # best pose total (kcal/mol)
