"""Load a real benchmark set of ligands with experimental affinities.

CSV schema (header row required):
    ligand_id,name,smiles,experimental_dg,coordinates_fragment

`experimental_dg` in kcal/mol (dG; convert Ki/Kd via dG = RT ln Kd, ~0.593
kcal/mol at 298 K). `coordinates_fragment` is 1/0 or true/false.
"""
from __future__ import annotations

from pathlib import Path

from ..models import Ligand


def load_ligands(csv_path: str | Path) -> list[Ligand]:
    import pandas as pd

    df = pd.read_csv(csv_path)
    required = {"ligand_id", "name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"benchmark CSV missing columns: {missing}")

    ligands: list[Ligand] = []
    for _, r in df.iterrows():
        dg = r.get("experimental_dg")
        coord = r.get("coordinates_fragment", 0)
        ligands.append(Ligand(
            ligand_id=str(r["ligand_id"]),
            name=str(r["name"]),
            smiles=str(r.get("smiles", "")),
            experimental_dg=(float(dg) if dg is not None and str(dg) != "nan" else None),
            coordinates_fragment=str(coord).strip().lower() in ("1", "true", "yes"),
        ))
    return ligands


def ki_to_dg(ki_molar: float, temperature_k: float = 298.15) -> float:
    """Convert a dissociation/inhibition constant (in molar) to dG (kcal/mol)."""
    import math
    R = 1.987204259e-3   # kcal/(mol K)
    return R * temperature_k * math.log(ki_molar)
