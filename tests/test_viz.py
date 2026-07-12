"""Dashboard + sweep: self-contained HTML, correct content, honest sensitivity."""
from qbind import run, run_molecular, sweep
from qbind.models import LigandScore, StudyResult
from qbind.scoring import delta
from qbind.viz.dashboard import build_dashboard, render_html


def _demo_result():
    scores = [
        LigandScore("A", -7.0, -9.0, -9.5),
        LigandScore("B", -8.0, -8.2, -8.0),
        LigandScore("C", -9.0, -7.0, -6.8),
    ]
    result = StudyResult("T", "P", scores=scores, fragments=[], solver="reference",
                         coordinating_ids=["A", "C"])
    return result, delta.compute(scores)


def test_render_is_self_contained():
    result, report = _demo_result()
    html = render_html(result, report, reference_mode=True)
    assert "http://" not in html and "https://" not in html
    assert "cdn" not in html.lower()
    assert "<svg" in html
    assert report.verdict[:20] in html
    assert 'data-theme' in html                     # theme toggle present


def test_body_only_has_no_doctype():
    result, report = _demo_result()
    full = render_html(result, report, reference_mode=True)
    body = render_html(result, report, reference_mode=True, full_document=False)
    assert full.strip().startswith("<!doctype")
    assert not body.strip().startswith("<!doctype")
    assert "<style>" in body                          # styles travel with the body


def test_build_dashboard_writes_file(tmp_path):
    result, report = _demo_result()
    p = build_dashboard(result, report, tmp_path / "d.html", reference_mode=False)
    assert (tmp_path / "d.html").exists()
    assert open(p, encoding="utf-8").read().count("<svg") >= 3


def test_run_emits_dashboard(tmp_path):
    run(tmp_path)
    assert (tmp_path / "results" / "dashboard.html").exists()


def test_molecular_emits_dashboard(tmp_path):
    run_molecular(tmp_path, backend="analytic")
    assert (tmp_path / "results" / "dashboard.html").exists()


def test_sweep_trend_more_bias_more_improvement():
    s = sweep(biases=[0.0, 1.0, 2.0, 3.0], seed=3)
    assert len(s["x"]) == 4
    # The honest property: the more systematic DFT error there is to remove, the
    # more the correlated correction improves agreement. At zero bias the
    # improvement sits in a near-null band (single-seed sampling noise, not 0).
    assert s["y"][-1] > s["y"][0]
    assert s["y"][-1] > 0.1
    assert abs(s["y"][0]) < 0.15


def test_sweep_cache_written(tmp_path):
    p = tmp_path / "sweep.json"
    sweep(biases=[0.0, 1.5, 3.0], seed=3, cache_path=str(p))
    assert p.exists()
