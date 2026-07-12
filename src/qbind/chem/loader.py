"""Load a molecular study from a self-contained JSON file.

`study.json` describes a whole cluster study; each ligand entry references a
complex `.xyz` (fragment + ligand together) plus which atoms are the correlated
fragment. Every ligand becomes one `InteractionJob` via `cluster.carve`, so the
rest of the pipeline is unchanged. See examples/study_fe_ligands/ for a template.

Only electron/spin PARITY is validated here (a fast, dependency-free sanity gate);
chemical sanity (convergence, correct spin state) is the user's responsibility and
surfaces as pyscf errors at run time.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .cluster import carve
from .geometry import Geometry, parse_xyz
from .interaction import InteractionJob

# Atomic numbers for the elements likely to appear in a metalloenzyme cluster.
# Extend if a study uses something not listed (parity validation needs it).
_Z = {
    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9,
    "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15, "S": 16, "Cl": 17,
    "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22, "V": 23, "Cr": 24, "Mn": 25,
    "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30, "Se": 34, "Br": 35,
    "Mo": 42, "Ru": 44, "I": 53,
}


@dataclass
class StudySpec:
    target_name: str
    pocket: str
    basis: str
    xc: str
    ao_labels: list[str]
    jobs: list[InteractionJob] = field(default_factory=list)


def _n_electrons(geom: Geometry) -> int:
    total = 0
    for el, _ in geom.atoms:
        if el not in _Z:
            raise ValueError(
                f"element '{el}' not in the atomic-number table; add it to "
                "qbind/chem/loader.py::_Z to enable parity validation")
        total += _Z[el]
    return total - geom.charge


def _validate_parity(geom: Geometry, ligand_id: str, piece: str) -> None:
    n_e = _n_electrons(geom)
    if geom.spin < 0 or geom.spin > n_e or (n_e - geom.spin) % 2 != 0:
        raise ValueError(
            f"{ligand_id}/{piece}: impossible spin={geom.spin} for {n_e} electrons "
            f"(charge={geom.charge}). Need 0 <= spin <= {n_e} and "
            f"(electrons - spin) even.")


def _geometry_from_entry(entry: dict, base: Path) -> Geometry:
    """Read the combined complex geometry: inline 'atoms' or a 'complex_xyz' path."""
    if entry.get("atoms"):
        atoms = tuple((a[0], (float(a[1][0]), float(a[1][1]), float(a[1][2])))
                      for a in entry["atoms"])
        return Geometry(atoms=atoms, name=entry.get("ligand_id", ""))
    xyz_path = base / entry["complex_xyz"]
    return parse_xyz(xyz_path.read_text(encoding="utf-8"),
                     name=entry.get("ligand_id", ""))


def load_study(path: str | Path) -> StudySpec:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    base = path.parent
    chem = data.get("chemistry", {})
    ao_labels = list(chem.get("ao_labels", ["Fe 3d", "Fe 4d"]))

    jobs: list[InteractionJob] = []
    for entry in data["ligands"]:
        lid = entry["ligand_id"]
        combined = _geometry_from_entry(entry, base)
        n_atoms = len(combined.atoms)

        frag_idx = list(entry["fragment_atoms"])
        lig_idx = entry.get("ligand_atoms")
        if lig_idx is None:                      # default: everything not in fragment
            lig_idx = [i for i in range(n_atoms) if i not in set(frag_idx)]

        charges = entry.get("charges", {})
        spins = entry.get("spins", {})
        job = carve(
            combined, frag_idx, lig_idx,
            fragment_charge=int(charges.get("fragment", 0)),
            fragment_spin=int(spins.get("fragment", 0)),
            ligand_charge=int(charges.get("ligand", 0)),
            ligand_spin=int(spins.get("ligand", 0)),
            ligand_id=lid,
            complex_spin=int(spins["complex"]) if "complex" in spins else None,
            experimental_dg=entry.get("experimental_dg"),
        )
        # complex charge may differ from fragment+ligand if the user overrides it.
        if "complex" in charges:
            job = InteractionJob(
                ligand_id=job.ligand_id,
                complex_ab=Geometry(job.complex_ab.atoms, int(charges["complex"]),
                                    job.complex_ab.spin, job.complex_ab.name),
                fragment_a=job.fragment_a, ligand_b=job.ligand_b,
                is_strongly_correlated=job.is_strongly_correlated,
                experimental_dg=job.experimental_dg)

        for geom, piece in ((job.complex_ab, "complex"),
                            (job.fragment_a, "fragment"), (job.ligand_b, "ligand")):
            _validate_parity(geom, lid, piece)
        jobs.append(job)

    return StudySpec(
        target_name=data.get("target_name", "molecular-study"),
        pocket=data.get("pocket", "active-site-cluster"),
        basis=chem.get("basis", "def2-SVP"),
        xc=chem.get("xc", "wb97x-d"),
        ao_labels=ao_labels,
        jobs=jobs,
    )
