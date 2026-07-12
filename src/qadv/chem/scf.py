"""Mean-field SCF with a convergence-escalation ladder.

Fixes vs the first draft: convergence is checked *between* rungs (so we stop as
soon as one works), and the large level shift is dropped before switching to the
second-order (Newton) solver, which otherwise stalls.
"""
from __future__ import annotations

from ..runtime import Context


def build_mol(atoms, spin: int, charge: int = 0, basis: str = "cc-pvdz",
              symmetry: bool = False, max_mem_frac: float = 0.6):
    from pyscf import gto
    max_mem = 4000
    try:
        import psutil
        max_mem = int(psutil.virtual_memory().total / 1e6 * max_mem_frac)
    except Exception:
        pass
    return gto.M(atom=atoms, basis=basis, spin=spin, charge=charge,
                 symmetry=symmetry, verbose=3, max_memory=max_mem)


def run_rohf(ctx: Context, mol, tag: str = "scf"):
    """ROHF with escalation: plain -> DF -> DF+levelshift -> SOSCF -> minao guess."""
    from pyscf import scf

    def attempt(mf) -> bool:
        try:
            mf.kernel()
            return bool(mf.converged)
        except Exception as e:
            ctx.log(f"SCF/{tag} attempt raised: {e}", "WARNING")
            return False

    mf = scf.ROHF(mol)
    mf.max_cycle = 200
    if attempt(mf):
        ctx.log(f"SCF/{tag} converged (plain ROHF) E={mf.e_tot:.8f}")
        return mf

    ctx.decide(f"SCF/{tag}", "density_fit", "plain ROHF did not converge")
    mf = scf.ROHF(mol).density_fit()
    mf.max_cycle = 200
    if attempt(mf):
        ctx.log(f"SCF/{tag} converged (DF) E={mf.e_tot:.8f}")
        return mf

    ctx.decide(f"SCF/{tag}", "DF + level_shift then SOSCF", "DF alone insufficient")
    mf = scf.ROHF(mol).density_fit()
    mf.level_shift = 0.5
    mf.max_cycle = 200
    attempt(mf)
    mf.level_shift = 0.0            # remove shift before Newton (else it stalls)
    mf = mf.newton()
    if attempt(mf):
        ctx.log(f"SCF/{tag} converged (SOSCF) E={mf.e_tot:.8f}")
        return mf

    ctx.decide(f"SCF/{tag}", "minao guess + conv_tol 1e-6", "SOSCF insufficient")
    mf = scf.ROHF(mol).density_fit()
    mf.conv_tol = 1e-6
    mf.max_cycle = 300
    try:
        mf.kernel(mf.get_init_guess(key="minao"))
    except Exception as e:
        ctx.log(f"SCF/{tag} minao attempt raised: {e}", "WARNING")
    mf = mf.newton()
    attempt(mf)
    if not mf.converged:
        ctx.decide(f"SCF/{tag}", "PROCEED UNCONVERGED",
                   "escalation ladder exhausted; reported explicitly, not hidden")
    ctx.log(f"SCF/{tag} converged={mf.converged} E={mf.e_tot:.8f}")
    return mf
