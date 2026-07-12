"""Immutable run configuration.

A frozen dataclass instead of module globals: explicit, testable, and safe to
pass around. Construct once (usually via `from_env`) and hand to `Context`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import constants as K

_DEFAULT_PROJ = "/content/drive/MyDrive/qchem_advantage"


@dataclass(frozen=True)
class Settings:
    proj: Path
    basis: str = "cc-pvdz"
    seed: int = 0
    shots: int = 100_000
    # Subspace-dimension sweeps (samples per batch). The curve is the result.
    stage0_sweep: tuple[int, ...] = (100, 300, 1_000, 3_000, 10_000)
    stage1_sweep: tuple[int, ...] = (
        1_000, 5_000, 20_000, 50_000, 100_000, 200_000, 500_000,
    )
    # SQD self-consistent configuration-recovery controls.
    sqd_num_batches: int = 3
    sqd_max_iterations: int = 5
    ram_threshold_pct: float = 80.0
    chem_acc_ha: float = K.CHEM_ACC_HA

    @classmethod
    def from_env(cls, proj: str | Path | None = None, **overrides) -> "Settings":
        p = Path(proj or os.environ.get("QADV_PROJ", _DEFAULT_PROJ))
        return cls(proj=p, **overrides)

    # Convenience path helpers -------------------------------------------- #
    @property
    def checkpoints(self) -> Path:
        return self.proj / "checkpoints"

    @property
    def results(self) -> Path:
        return self.proj / "results"

    @property
    def figures(self) -> Path:
        return self.proj / "figures"

    @property
    def logs(self) -> Path:
        return self.proj / "logs"

    @property
    def decisions_file(self) -> Path:
        return self.proj / "DECISIONS.md"
