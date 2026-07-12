"""Multireference diagnostics: decide which fragment(s) actually need the
correlated/quantum solver, instead of assuming it.

`select_strong_fragments` keeps fragments whose natural-orbital occupations put
them in the strongly-correlated window -- that is the gate that stops us from
spending the quantum budget on fragments DFT already handles.
"""
from __future__ import annotations

from ..models import FragmentSpec


def natural_orbital_diagnostic(occupations) -> float:
    """Fraction of NOs with occupation in (0.02, 1.98)."""
    occ = list(occupations)
    if not occ:
        return 0.0
    return sum(1 for o in occ if 0.02 < o < 1.98) / len(occ)


def select_strong_fragments(fragments: list[FragmentSpec],
                            threshold: float = 0.25) -> list[FragmentSpec]:
    """Fragments that are pre-flagged OR score above the diagnostic threshold."""
    strong = []
    for f in fragments:
        if f.is_strongly_correlated or f.multireference_score >= threshold:
            strong.append(f)
    return strong
