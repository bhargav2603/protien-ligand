"""qadv -- autonomous SQD pipeline for drug-relevant metalloenzymes.

Typical use (Colab or local):

    import qadv
    ctx = qadv.make_context("/content/drive/MyDrive/qchem_advantage")
    qadv.run_stage0(ctx)          # validation (FeP, ~20q)
    qadv.run_stage1(ctx)          # advantage attempt (Cpd I, >=40q)
    qadv.build_report(ctx)        # writes results/REPORT.md
"""
from __future__ import annotations

from .pipeline import report, stage0, stage1
from .pipeline.errors import GateFailure
from .runtime import Context
from .settings import Settings

__all__ = [
    "Settings", "Context", "GateFailure",
    "make_context", "run_stage0", "run_stage1", "build_report",
]


def make_context(proj=None, **overrides) -> Context:
    """Build a Context from an output directory (defaults to $QADV_PROJ)."""
    return Context(Settings.from_env(proj, **overrides))


def run_stage0(ctx: Context):
    return stage0.run(ctx)


def run_stage1(ctx: Context, use_hardware: bool = True):
    return stage1.run(ctx, use_hardware=use_hardware)


def build_report(ctx: Context) -> str:
    return report.generate(ctx)
