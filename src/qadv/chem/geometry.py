"""Idealized target geometries. Pure functions -- no I/O, no logging.

Bond lengths are literature-typical and were bond-length-checked:
  Fe-N 2.00 | N-Ca 1.38 | Ca-Cb 1.43 | Cb-Cb 1.40 | Ca-Cm 1.37 | C-H ~1.07
  Cpd I adds: Fe=O 1.63 | Fe-S 2.50 | S-H 1.35 | Fe out-of-plane 0.30

These are NOT literature-pinned coordinate sets; the pipeline records that
caveat to DECISIONS.md. Swap in SI/optimized coordinates for publication.
"""
from __future__ import annotations

import numpy as np

Atom = tuple[str, tuple[float, float, float]]


def _c4(x: float, y: float) -> list[tuple[float, float]]:
    """The four C4 images (90 deg rotations about z) of an in-plane point."""
    out = []
    for k in range(4):
        th = np.pi / 2 * k
        c, s = np.cos(th), np.sin(th)
        out.append((c * x - s * y, s * x + c * y))
    return out


def _porphine_core(z: float = 0.0) -> list[Atom]:
    """20 C, 4 N, 12 H macrocycle in the xy-plane (metal removed)."""
    unit = {
        "N": [(2.00, 0.00)],
        "C": [(2.83, 1.10), (2.83, -1.10), (4.20, 0.70), (4.20, -0.70), (2.40, 2.40)],
        "H": [(5.10, 1.28), (5.10, -1.28), (3.16, 3.16)],
    }
    atoms: list[Atom] = []
    for element, points in unit.items():
        for (x, y) in points:
            for X, Y in _c4(x, y):
                atoms.append((element, (float(X), float(Y), z)))
    return atoms


def iron_porphine() -> list[Atom]:
    """Idealized D4h Fe(II)-porphine, FeN4C20H12 (37 atoms), Fe at origin."""
    return [("Fe", (0.0, 0.0, 0.0))] + _porphine_core(0.0)


def compound_i(fe_z: float = 0.30) -> list[Atom]:
    """Idealized P450 Compound I model (40 atoms): porphine + oxo + thiolate SH."""
    core = _porphine_core(0.0)
    fe = ("Fe", (0.0, 0.0, fe_z))
    oxo = ("O", (0.0, 0.0, fe_z + 1.63))
    s = ("S", (0.0, 0.0, fe_z - 2.50))
    hs = ("H", (1.15, 0.0, fe_z - 2.50 - 0.70))
    return [fe] + core + [oxo, s, hs]
