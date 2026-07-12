"""Typed result records. Replaces the untyped dicts of the first draft.

Dataclasses make the report generator and tests depend on a stable schema
instead of stringly-typed keys, and they pickle cleanly for checkpointing.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Stage0Result:
    n_qubits: int
    ncas: int
    nelec: tuple[int, int]
    basis: str
    e_casci: float
    e_sqd_noiseless: float
    quantum_curve: list[tuple[int, float]] = field(default_factory=list)
    classical_curve: list[tuple[int, float]] = field(default_factory=list)
    dft_gaps: dict[str, float] = field(default_factory=dict)
    quantum_is_fallback: bool = False
    gate_0b_passed: bool = False
    gate_0c_passed: bool = False

    @property
    def dft_spread(self) -> float:
        return (max(self.dft_gaps.values()) - min(self.dft_gaps.values())
                if self.dft_gaps else 0.0)


@dataclass
class Stage1Result:
    n_qubits: int
    ncas: int
    basis: str
    status: str                       # COMPLETE | PENDING_HARDWARE
    nelec: tuple[int, int] | None = None
    sample_source: str | None = None  # "hardware" | "mps (NOT advantage)"
    sweep: list[tuple[int, float]] = field(default_factory=list)
    integrity_clean: bool | None = None
