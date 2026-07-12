"""SQD diagonalisation adapter + subspace sweep.

The energy is a variational UPPER BOUND on the active-space ground state; a
smaller subspace gives a looser but still valid, still classically-certifiable
bound. Input integrals come from `ActiveSpace` (the CASCI-consistent path), so
in Stage 0 the SQD energy must reproduce the CASCI anchor -- if it does not, the
bug is in the quantum stack, not the Hamiltonian (that is Gate 0b).

`qiskit-addon-sqd`'s public API has shifted across releases, so the actual call
is isolated in `_diagonalize_once`. If a signature changed in your environment,
this is the one function to touch.
"""
from __future__ import annotations

from ..chem.active_space import ActiveSpace
from ..runtime import Context


def _diagonalize_once(a: ActiveSpace, bit_array, subspace_dim: int,
                      num_batches: int, max_iterations: int, seed: int) -> float:
    """Return the total energy (electronic bound + core). Targets sqd >= 0.10."""
    from qiskit_addon_sqd.fermion import diagonalize_fermionic_hamiltonian

    result = diagonalize_fermionic_hamiltonian(
        a.h1, a.h2, bit_array,
        samples_per_batch=int(subspace_dim),
        norb=a.ncas, nelec=a.nelec,
        num_batches=num_batches, max_iterations=max_iterations,
        symmetrize_spin=True, seed=seed,
    )
    return float(result.energy) + a.ecore


def diagonalize(ctx: Context, a: ActiveSpace, bit_array, subspace_dim: int,
                num_batches: int = 3, max_iterations: int = 5,
                seed: int = 0) -> float:
    try:
        e_total = _diagonalize_once(a, bit_array, subspace_dim,
                                    num_batches, max_iterations, seed)
    except TypeError as e:
        ctx.log(f"SQD signature mismatch ({e}); check qiskit-addon-sqd version "
                "and adjust _diagonalize_once.", "ERROR")
        raise
    return e_total


def subspace_sweep(ctx: Context, a: ActiveSpace, bit_array, dims,
                   num_batches: int = 3, max_iterations: int = 5, seed: int = 0,
                   on_iteration=None) -> list[tuple[int, float]]:
    """Sweep subspace dimension upward until RAM says stop. Returns [(dim, E)].

    The CURVE is the result -- never a single point. `on_iteration(curve)` is
    called after each step so a disconnect never loses progress.
    """
    curve: list[tuple[int, float]] = []
    for d in dims:
        if not ctx.ram_ok():
            ctx.decide("subspace ceiling", str(d),
                       "RAM ceiling reached before this dimension; reported, not hidden")
            break
        try:
            e_total = diagonalize(ctx, a, bit_array, d, num_batches,
                                  max_iterations, seed)
        except MemoryError:
            ctx.decide("subspace ceiling", str(d), "MemoryError during diagonalisation")
            break
        curve.append((int(d), e_total))
        ctx.log(f"SQD sweep: dim={d:>8} E_upper_bound={e_total:.8f} Ha")
        if on_iteration:
            on_iteration(curve)
    return curve
