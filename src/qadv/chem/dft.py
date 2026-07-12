"""DFT spin-state gap scan -- the classical-failure figure (Gate 0c).

Computes E(low-spin) - E(high-spin) across a range of functional families. A
large spread (or a sign flip) means the production-scale classical method is
qualitatively unreliable on this system, which is what the whole project claims.
"""
from __future__ import annotations

from ..constants import HARTREE_TO_KCAL
from ..runtime import Context
from .scf import build_mol

# GGA / meta-GGA / hybrid / range-separated families. Unparseable names are
# skipped and logged, never fatal.
FUNCTIONALS = ["B3LYP", "PBE0", "TPSSh", "PBE", "BP86", "M06", "r2scan", "B97-D"]


def spin_gap_scan(ctx: Context, atoms, basis: str, spin_low: int, spin_high: int,
                  charge: int = 0, tag: str = "sys",
                  functionals=FUNCTIONALS) -> dict[str, float]:
    from pyscf import dft

    def energy(spin, xc):
        mol = build_mol(atoms, spin, charge, basis)
        mol.verbose = 1
        ks = dft.UKS(mol).density_fit()
        ks.xc = xc
        ks.max_cycle = 200
        ks.kernel()
        return ks.e_tot, ks.converged

    gaps: dict[str, float] = {}
    for xc in functionals:
        try:
            e_lo, ok_lo = energy(spin_low, xc)
            e_hi, ok_hi = energy(spin_high, xc)
            if not (ok_lo and ok_hi):
                ctx.decide(f"DFT {xc}/{tag}", "skipped", "a spin state did not converge")
                continue
            gaps[xc] = (e_lo - e_hi) * HARTREE_TO_KCAL
            ctx.log(f"DFT {xc:8s}/{tag}: gap(low-high) = {gaps[xc]:+.2f} kcal/mol")
        except Exception as e:
            ctx.decide(f"DFT {xc}/{tag}", "skipped", str(e)[:100])
    return gaps
