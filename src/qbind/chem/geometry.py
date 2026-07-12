"""Molecular geometry: parsing, pyscf mol construction, and cluster splitting.

This is the runnable-chemistry core of the pilot. It operates on small
metal-ligand CLUSTERS (a cluster/supermolecular model of the active site), which
is the honest, testable stand-in for full protein QM/MM+DMET: it needs only a
handful of atoms, so the real DFT/CASSCF/SQD backends run in Colab without a
protein download. Full DMET embedding is the later upgrade (qm/embedding.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field

Atom = tuple[str, tuple[float, float, float]]


@dataclass(frozen=True)
class Geometry:
    atoms: tuple[Atom, ...]
    charge: int = 0
    spin: int = 0                      # 2S = n_alpha - n_beta
    name: str = ""

    @property
    def elements(self) -> tuple[str, ...]:
        return tuple(a[0] for a in self.atoms)

    def has_any(self, symbols) -> bool:
        s = set(symbols)
        return any(el in s for el in self.elements)

    def to_pyscf_atom(self) -> list:
        return [[el, (x, y, z)] for el, (x, y, z) in self.atoms]

    def subset(self, indices, charge: int, spin: int, name: str = "") -> "Geometry":
        atoms = tuple(self.atoms[i] for i in indices)
        return Geometry(atoms=atoms, charge=charge, spin=spin, name=name)


def parse_xyz(text: str, charge: int = 0, spin: int = 0, name: str = "") -> Geometry:
    """Parse a standard .xyz block (first line = count, second = comment)."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("empty xyz")
    try:
        n = int(lines[0].split()[0])
        body = lines[2:2 + n] if len(lines) >= 2 + n else lines[1:]
    except ValueError:
        body = lines                       # headerless xyz
    atoms: list[Atom] = []
    for ln in body:
        p = ln.split()
        if len(p) < 4:
            continue
        atoms.append((p[0], (float(p[1]), float(p[2]), float(p[3]))))
    if not atoms:
        raise ValueError("no atoms parsed from xyz")
    return Geometry(atoms=tuple(atoms), charge=charge, spin=spin, name=name)


def metal_symbols_from_labels(ao_labels) -> set[str]:
    """Element symbols implied by AVAS ao_labels like 'Fe 3d' -> {'Fe'}."""
    out = set()
    for lab in ao_labels:
        tok = lab.split()
        if tok:
            out.add(tok[0])
    return out
