"""Figure generation (matplotlib, Agg backend). Saved under settings.figures."""
from __future__ import annotations

from ..runtime import Context


def _save(ctx: Context, fig, name: str):
    path = ctx.settings.figures / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    ctx.log(f"figure written: {path}")
    return path


def dft_gap(ctx: Context, gaps: dict[str, float], system: str,
            low_label: str, high_label: str, fname: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not gaps:
        ctx.log("no DFT data for figure", "WARNING")
        return None
    names = list(gaps)
    vals = [gaps[k] for k in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, vals, color=["#c0392b" if v < 0 else "#2c7fb8" for v in vals])
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel(f"E({low_label}) - E({high_label})  [kcal/mol]")
    ax.set_title(f"DFT spin-state gap vs functional -- {system}\n"
                 "sign flips = qualitative disagreement (the classical failure)")
    ax.tick_params(axis="x", rotation=30)
    spread = max(vals) - min(vals)
    ax.text(0.02, 0.95, f"spread = {spread:.1f} kcal/mol", transform=ax.transAxes,
            va="top", bbox=dict(boxstyle="round", fc="#fff3cd"))
    return _save(ctx, fig, fname)


def sqd_convergence(ctx: Context, quantum_curve, classical_curve=None,
                    casci=None, title="SQD convergence", fname="fig2.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    if quantum_curve:
        xs, ys = zip(*quantum_curve)
        ax.plot(xs, ys, "o-", color="#2c7fb8", label="quantum sampling (LUCJ)")
    if classical_curve:
        xs, ys = zip(*classical_curve)
        ax.plot(xs, ys, "s--", color="#e67e22", label="classical-sampling control")
    if casci is not None:
        ax.axhline(casci, color="k", ls=":", label=f"CASCI anchor = {casci:.5f}")
    ax.set_xscale("log")
    ax.set_xlabel("subspace dimension (samples per batch)")
    ax.set_ylabel("SQD energy upper bound  [Ha]")
    ax.set_title(title)
    ax.legend()
    return _save(ctx, fig, fname)
