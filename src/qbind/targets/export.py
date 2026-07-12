"""Write a target's cluster models out as a runnable study.json + xyz files.

Regenerate the shipped examples with:  python -m qbind.targets.export
"""
from __future__ import annotations

import json
from pathlib import Path

from . import builders as B

TARGETS = {
    "p450_azoles": dict(
        job=B.p450_job,
        ligands=["ammonia", "methylamine", "pyridine"],
        target_name="Cytochrome P450 (heme-Fe) + N-donor azole proxies",
        pocket="heme active site (Fe-porphine-thiolate)",
        ao_labels=["Fe 3d", "Fe 4d"],
        note="Fe(III): fragment 5-coordinate high-spin (S=5/2), complex 6-coordinate "
             "low-spin (S=1/2) -- the spin crossover DFT gets wrong. Ligands are "
             "minimal N-donor proxies; replace with real azoles from the PDB complexes.",
    ),
    "ca2_sulfonamides": dict(
        job=B.ca2_job,
        ligands=["ammonia", "methylamine", "methanesulfonamide"],
        target_name="Carbonic anhydrase II (Zn) + sulfonamide/N-donor proxies (CONTROL)",
        pocket="Zn active site (Zn-amine3 His proxy)",
        ao_labels=["Zn 3d"],
        note="Zn(II) d10 closed shell -> expected NULL correlated effect. This is the "
             "control that proves the method reports 'no effect' when there is none.",
    ),
}


def _write_xyz(path: Path, geom, comment: str) -> None:
    lines = [str(len(geom.atoms)), comment]
    for el, (x, y, z) in geom.atoms:
        lines.append(f"{el:2s} {x:12.6f} {y:12.6f} {z:12.6f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_study(key: str, outdir: str | Path) -> Path:
    spec = TARGETS[key]
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for lid in spec["ligands"]:
        job = spec["job"](lid, expt_dg=None)
        _write_xyz(out / f"{lid}.xyz", job.complex_ab, f"{lid} complex (idealized)")
        n_frag = len(job.fragment_a.atoms)
        entries.append({
            "ligand_id": lid,
            "complex_xyz": f"{lid}.xyz",
            "fragment_atoms": list(range(n_frag)),
            "ligand_atoms": None,
            "charges": {"fragment": job.fragment_a.charge, "ligand": job.ligand_b.charge,
                        "complex": job.complex_ab.charge},
            "spins": {"fragment": job.fragment_a.spin, "ligand": job.ligand_b.spin,
                      "complex": job.complex_ab.spin},
            "experimental_dg": None,   # <-- fill from ChEMBL/BindingDB (kcal/mol)
        })
    study = {
        "target_name": spec["target_name"],
        "pocket": spec["pocket"],
        "_note": spec["note"],
        "chemistry": {"basis": "def2-SVP", "xc": "wb97x-d", "ao_labels": spec["ao_labels"]},
        "ligands": entries,
    }
    (out / "study.json").write_text(json.dumps(study, indent=2), encoding="utf-8")
    return out / "study.json"


def main() -> None:
    root = Path(__file__).resolve().parents[3] / "examples"
    for key in TARGETS:
        p = write_study(key, root / key)
        print("wrote", p)


if __name__ == "__main__":
    main()
