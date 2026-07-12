"""Live interactive explorer for Colab/Jupyter (ipywidgets).

Drag sliders for the reference-model knobs and watch the dashboard recompute in
real time. This works ONLY for the synthetic reference mode, which is cheap
(milliseconds). Real CASSCF/SQD chemistry is far too slow to recompute behind a
slider — for that, precompute a grid with `viz.sweep` and scrub the cache.

Usage in a Colab cell:
    from qbind.viz.explorer import reference_explorer
    reference_explorer()
"""
from __future__ import annotations

import html


def _dashboard_html(systematic_bias, classical_noise, correlated_noise,
                    n_ligands, seed) -> str:
    from ..config import Config, ReferenceModel
    from ..models import StudyResult
    from ..pipeline.orchestrator import _build_reference_stages, score_ligands
    from ..qm import diagnostics
    from ..scoring import delta
    from .dashboard import render_html

    cfg = Config(reference=ReferenceModel(
        systematic_bias=systematic_bias, classical_noise=classical_noise,
        correlated_noise=correlated_noise, n_ligands=int(n_ligands), seed=int(seed)))
    stages = _build_reference_stages(cfg)
    fragments = stages["embedder"].fragments()
    strong = {f.name for f in diagnostics.select_strong_fragments(fragments)}
    scores = score_ligands(stages, fragments, strong)
    report = delta.compute(scores)
    result = StudyResult(
        target_name=cfg.target_name, pocket=cfg.pocket, scores=scores,
        fragments=fragments, solver="reference",
        coordinating_ids=[l.ligand_id for l in stages["ligands"] if l.coordinates_fragment])
    return render_html(result, report, reference_mode=True,
                       title="Live reference explorer")


def reference_explorer():
    """Return/display an interactive widget (call inside a notebook)."""
    import ipywidgets as W
    from IPython.display import HTML, display

    out = W.Output()

    def _update(**kw):
        page = _dashboard_html(**kw)
        srcdoc = html.escape(page, quote=True)
        with out:
            out.clear_output(wait=True)
            display(HTML(f'<iframe style="width:100%;height:1400px;border:0" '
                         f'srcdoc="{srcdoc}"></iframe>'))

    controls = dict(
        systematic_bias=W.FloatSlider(1.8, min=0, max=4, step=0.1, description="DFT bias"),
        classical_noise=W.FloatSlider(0.6, min=0, max=1.5, step=0.05, description="cls noise"),
        correlated_noise=W.FloatSlider(0.3, min=0, max=1.5, step=0.05, description="corr noise"),
        n_ligands=W.IntSlider(18, min=6, max=40, step=1, description="ligands"),
        seed=W.IntSlider(7, min=0, max=50, step=1, description="seed"),
    )
    ui = W.interactive(_update, **controls)
    display(W.VBox([ui.children[-1] if False else W.VBox(list(controls.values())), out]))
    _update(**{k: v.value for k, v in controls.items()})
    for w in controls.values():
        w.observe(lambda ch: _update(**{k: v.value for k, v in controls.items()}), names="value")
