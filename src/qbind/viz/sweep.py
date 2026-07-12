"""Sensitivity sweep: vary one reference-model parameter and record how much the
correlated correction improves agreement with experiment.

This is the honest antidote to slider cherry-picking: instead of dialing one knob
to a flattering value, you show the whole response curve. Cheap (pure numpy), so
it is safe to recompute; the expensive real-chemistry path would precompute a
grid the same way and cache it.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import Config, ReferenceModel
from ..pipeline.orchestrator import _build_reference_stages, score_ligands
from ..qm import diagnostics
from ..scoring import delta


def sweep_reference(biases=(0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0), *,
                    seed: int = 7, cache_path=None, **model_kw) -> dict:
    """Return {x, y, xlabel, ylabel, hint} of Spearman improvement vs DFT bias."""
    xs, ys = [], []
    for b in biases:
        cfg = Config(reference=ReferenceModel(systematic_bias=float(b), seed=seed, **model_kw))
        stages = _build_reference_stages(cfg)
        fragments = stages["embedder"].fragments()
        strong = {f.name for f in diagnostics.select_strong_fragments(fragments)}
        report = delta.compute(score_ligands(stages, fragments, strong))
        xs.append(float(b))
        ys.append(report.correlation_improvement or 0.0)

    result = {
        "x": xs, "y": ys,
        "xlabel": "systematic DFT bias (kcal/mol)",
        "ylabel": "Spearman improvement",
        "hint": "how much the correlated correction helps as the DFT error grows "
                "(at bias 0 there is nothing to fix — the honest null)",
    }
    if cache_path:
        Path(cache_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
