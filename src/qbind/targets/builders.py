"""Idealized truncated active-site cluster models for the two chosen targets.

  * P450  : Fe(III)-porphine + axial thiolate (SH-, a cysteine proxy), with a
            sixth axial N-donor as the azole-warhead proxy. Fe is genuinely
            correlated; binding a strong-field N-donor drives a HIGH-SPIN (S=5/2,
            5-coordinate) -> LOW-SPIN (S=1/2, 6-coordinate) crossover, which is
            exactly the multireference physics DFT gets wrong.
  * CA-II : Zn(2+) with three amine donors (a His3 proxy) + a coordinating
            inhibitor. Zn is d10 closed-shell -> essentially NO static
            correlation. This is the control: the correlated correction should
            be ~0, and the pipeline should say so.

IDEALIZED geometries (bond-length checked, planar/symmetric). NOT literature
coordinates. Replace with poses carved from the real PDB complexes and DFT-
optimized before any production result (see docs/TARGETS.md). The N-donor /
sulfonamide ligands here are minimal congeneric proxies for the real drugs.
"""
from __future__ import annotations

import math

from ..chem.geometry import Geometry
from ..chem.interaction import InteractionJob

Atom = tuple[str, tuple[float, float, float]]

# Coordination bond lengths (Angstrom).
FE_N_AX = 2.00      # Fe-N(axial donor)
FE_S = 2.30         # Fe-S(thiolate)
ZN_N = 2.05         # Zn-N


# --------------------------------------------------------------------------- #
# Metal-site fragments (metal at origin).
# --------------------------------------------------------------------------- #
def fe_heme_thiolate() -> list[Atom]:
    """Fe-porphine + axial SH- on -z; the +z site is open for the N-donor."""
    from qadv.chem.geometry import iron_porphine
    atoms: list[Atom] = [(el, (x, y, z)) for el, (x, y, z) in iron_porphine()]
    atoms.append(("S", (0.0, 0.0, -FE_S)))
    atoms.append(("H", (0.95, 0.0, -FE_S - 0.60)))     # S-H ~1.13 (proxy for Cys)
    return atoms


def _perp_basis(u):
    """Two orthonormal vectors perpendicular to unit vector u."""
    a = (1.0, 0.0, 0.0) if abs(u[0]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = (u[1] * a[2] - u[2] * a[1], u[2] * a[0] - u[0] * a[2], u[0] * a[1] - u[1] * a[0])
    n = math.sqrt(sum(c * c for c in e1)); e1 = tuple(c / n for c in e1)
    e2 = (u[1] * e1[2] - u[2] * e1[1], u[2] * e1[0] - u[0] * e1[2], u[0] * e1[1] - u[1] * e1[0])
    return e1, e2


def zn_amine3() -> list[Atom]:
    """Zn(2+) + 3 neutral NH3 donors in a tripod (His3 proxy); +z site left open."""
    atoms: list[Atom] = [("Zn", (0.0, 0.0, 0.0))]
    st, ct = math.sin(math.radians(109.5)), math.cos(math.radians(109.5))
    for k in range(3):
        phi = math.radians(120 * k)
        u = (st * math.cos(phi), st * math.sin(phi), ct)              # outward unit
        P = tuple(ZN_N * c for c in u)
        atoms.append(("N", P))
        e1, e2 = _perp_basis(u)
        for j in range(3):                                           # 3 H -> neutral NH3
            f = math.radians(120 * j)
            H = tuple(P[i] + 0.34 * u[i] + 0.94 * (math.cos(f) * e1[i] + math.sin(f) * e2[i])
                      for i in range(3))
            atoms.append(("H", H))
    return atoms


# --------------------------------------------------------------------------- #
# Coordinating ligands (coordinating atom at origin, body extending +z; the
# assembler translates them to sit at the metal's +z site).
# --------------------------------------------------------------------------- #
def ammonia() -> list[Atom]:
    a = [("N", (0.0, 0.0, 0.0))]
    for k in range(3):
        phi = math.radians(120 * k)
        a.append(("H", (0.94 * math.cos(phi), 0.94 * math.sin(phi), 0.38)))
    return a


def methylamine() -> list[Atom]:
    a = [("N", (0.0, 0.0, 0.0)), ("C", (0.0, 0.0, 1.47))]
    for k in range(2):                                   # 2 H on N
        phi = math.radians(120 + 120 * k)
        a.append(("H", (0.94 * math.cos(phi), 0.94 * math.sin(phi), -0.35)))
    for k in range(3):                                   # 3 H on methyl C
        phi = math.radians(60 + 120 * k)
        a.append(("H", (1.03 * math.cos(phi), 1.03 * math.sin(phi), 1.47 + 0.36)))
    return a


def pyridine() -> list[Atom]:
    """Planar 6-ring in the xz-plane, coordinating N at origin."""
    r = 1.39
    cx, cz = 0.0, r                                       # ring centre above N
    a: list[Atom] = []
    verts = []
    for k in range(6):
        th = math.radians(180 - 60 * k)                  # k=0 -> bottom vertex = N
        vx, vz = cx + r * math.sin(math.radians(60 * k)) * 0 + r * math.cos(th) * 0, 0
        # place explicitly: vertex = centre + r*(sin a, 0, -cos a) with a=60k
        ax = math.radians(60 * k)
        vx = r * math.sin(ax)
        vz = cz - r * math.cos(ax)
        verts.append((vx, 0.0, vz))
    a.append(("N", verts[0]))
    for k in range(1, 6):
        a.append(("C", verts[k]))
        ux, _, uz = verts[k][0] - cx, 0.0, verts[k][2] - cz
        n = math.hypot(ux, uz)
        a.append(("H", (verts[k][0] + 1.08 * ux / n, 0.0, verts[k][2] + 1.08 * uz / n)))
    return a


def methanesulfonamide_anion() -> list[Atom]:
    """CH3-SO2-NH(-) coordinating through the deprotonated N at origin."""
    n = (0.0, 0.0, 0.0)
    s = (0.0, 0.0, 1.60)
    a: list[Atom] = [("N", n), ("S", s), ("H", (0.95, 0.0, -0.30))]  # N-H
    st, ct = math.sin(math.radians(70.5)), math.cos(math.radians(70.5))
    subs = []
    for k in range(3):
        phi = math.radians(120 * k)
        subs.append((s[0] + st * math.cos(phi), s[1] + st * math.sin(phi), s[2] + ct))
    ox, oy, oz = subs[1]; ox2, oy2, oz2 = subs[2]
    a.append(("O", (s[0] + 1.45 * (ox - s[0]) / 1.0, s[1] + 1.45 * (oy - s[1]),
                    s[2] + 1.45 * (oz - s[2]))))
    a.append(("O", (s[0] + 1.45 * (ox2 - s[0]), s[1] + 1.45 * (oy2 - s[1]),
                    s[2] + 1.45 * (oz2 - s[2]))))
    cx, cy, cz = subs[0]
    c = (s[0] + 1.78 * (cx - s[0]), s[1] + 1.78 * (cy - s[1]), s[2] + 1.78 * (cz - s[2]))
    a.append(("C", c))
    for k in range(3):                                   # methyl H (approximate)
        phi = math.radians(60 + 120 * k)
        a.append(("H", (c[0] + 1.05 * math.cos(phi), c[1] + 1.05 * math.sin(phi), c[2] + 0.4)))
    return a


LIGANDS = {
    "ammonia": ammonia, "methylamine": methylamine, "pyridine": pyridine,
    "methanesulfonamide": methanesulfonamide_anion,
}


def _translate(atoms, dz) -> list[Atom]:
    return [(el, (x, y, z + dz)) for el, (x, y, z) in atoms]


# --------------------------------------------------------------------------- #
# Assemble an interaction job for one target + one ligand.
# --------------------------------------------------------------------------- #
def _job(fragment_atoms, frag_charge, frag_spin, ligand_atoms, lig_charge,
         d_ml, complex_spin, ligand_id, expt_dg) -> InteractionJob:
    lig = _translate(ligand_atoms, d_ml)
    frag = Geometry(tuple(fragment_atoms), charge=frag_charge, spin=frag_spin, name="fragment")
    ligand = Geometry(tuple(lig), charge=lig_charge, spin=0, name=ligand_id)
    complex_ab = Geometry(tuple(list(fragment_atoms) + list(lig)),
                          charge=frag_charge + lig_charge, spin=complex_spin,
                          name=f"{ligand_id}-complex")
    return InteractionJob(ligand_id=ligand_id, complex_ab=complex_ab, fragment_a=frag,
                          ligand_b=ligand, is_strongly_correlated=True,
                          experimental_dg=expt_dg)


def p450_job(ligand_id, expt_dg=None) -> InteractionJob:
    # Fe(III) [Fe(por)(SH)]: 5-coord high-spin S=5/2 (spin 5); complex 6-coord low-spin S=1/2 (spin 1).
    return _job(fe_heme_thiolate(), frag_charge=0, frag_spin=5,
                ligand_atoms=LIGANDS[ligand_id](), lig_charge=0,
                d_ml=FE_N_AX, complex_spin=1, ligand_id=ligand_id, expt_dg=expt_dg)


def ca2_job(ligand_id, expt_dg=None) -> InteractionJob:
    lig_charge = -1 if ligand_id == "methanesulfonamide" else 0
    # Zn(2+)(amine)3 fragment (+2), closed shell; complex closed shell (spin 0).
    return _job(zn_amine3(), frag_charge=2, frag_spin=0,
                ligand_atoms=LIGANDS[ligand_id](), lig_charge=lig_charge,
                d_ml=ZN_N, complex_spin=0, ligand_id=ligand_id, expt_dg=expt_dg)
