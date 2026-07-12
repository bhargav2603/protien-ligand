"""Assemble a self-contained interactive HTML dashboard from a study result.

No external libraries, no network: inline SVG charts + inline CSS/JS in one file
you can open, download, or share (and it is Artifact-safe: nothing loads from a
CDN). Light/dark aware with a manual toggle. The charts carry native hover
tooltips; identity is shown by legend + labels, never colour alone.
"""
from __future__ import annotations

import datetime as _dt
import html
from pathlib import Path

from ..models import StudyResult
from ..scoring import delta
from ..scoring.delta import DeltaReport
from . import svg
from .theme import style_block


def _status(report: DeltaReport) -> tuple[str, str]:
    """(css-var-name, human word) for the verdict."""
    imp = report.correlation_improvement
    if imp is None:
        return "warn", "no experimental data"
    if not report.quantum_changed_ranking:
        return "warn", "no change"
    if imp > 0.02:
        return "good", "improved toward experiment"
    if imp < -0.02:
        return "bad", "moved away from experiment"
    return "warn", "perturbation, no improvement"


def _e(s) -> str:
    return html.escape(str(s), quote=True)


def _tile(label, value, foot="", small=False) -> str:
    cls = "value sm" if small else "value"
    return (f'<div class="tile"><div class="label">{_e(label)}</div>'
            f'<div class="{cls}">{value}</div><div class="foot">{foot}</div></div>')


def _legend(pairs) -> str:
    items = "".join(f'<span><i style="background:var(--{c})"></i>{_e(t)}</span>' for t, c in pairs)
    return f'<div class="legend">{items}</div>'


def render_html(result: StudyResult, report: DeltaReport, *,
                reference_mode: bool, title: str | None = None, sweep=None,
                full_document: bool = True) -> str:
    coord = set(result.coordinating_ids)
    has_exp = report.spearman_corrected_expt is not None
    rows = delta.ranked_table(result.scores)

    # ---- shared scatter domain ----
    cards = []
    if has_exp:
        xs = [s.experimental_dg for s in result.scores]
        ys = [s.baseline_score for s in result.scores] + [s.corrected_score for s in result.scores]
        dom = (min(xs + ys), max(xs + ys))
        def _pts(attr):
            return [dict(x=s.experimental_dg, y=getattr(s, attr),
                         label=s.ligand_id, group=("coord" if s.ligand_id in coord else "nocoord"))
                    for s in result.scores]
        cards.append(_card("Classical baseline vs experiment",
                           "each point a ligand · dotted line = perfect agreement",
                           _legend([("coordinates fragment", "coord"), ("does not", "nocoord")]),
                           svg.scatter(_pts("baseline_score"), domain=dom, ylabel="baseline pred")))
        cards.append(_card("Quantum-corrected vs experiment",
                           "closer to the dotted line = better",
                           _legend([("coordinates fragment", "coord"), ("does not", "nocoord")]),
                           svg.scatter(_pts("corrected_score"), domain=dom, ylabel="corrected pred")))

    # ---- ranking slopegraph ----
    slope_rows = [dict(label=r["ligand_id"], left=r["baseline_rank"], right=r["corrected_rank"],
                       group=("coord" if r["ligand_id"] in coord else "nocoord"),
                       moved=r["baseline_rank"] != r["corrected_rank"]) for r in rows]
    cards.append(_card("Ranking change",
                       f'Kendall τ {report.kendall_tau_rankings:.2f} · {report.n_rank_changes} moved · rank 1 = tightest',
                       _legend([("coordinates fragment", "coord"), ("does not", "nocoord")]),
                       svg.slopegraph(slope_rows)))

    # ---- per-ligand delta ----
    bar_items = sorted(
        [dict(label=s.ligand_id, value=s.delta,
              group=("coord" if s.ligand_id in coord else "nocoord")) for s in result.scores],
        key=lambda d: d["value"])
    cards.append(_card("Per-ligand correction (corrected − baseline)",
                       "how far the correlated term moved each ligand",
                       _legend([("coordinates fragment", "coord"), ("does not", "nocoord")]),
                       svg.diverging_bars(bar_items)))

    # ---- optional sweep ----
    if sweep:
        xs, ys = sweep["x"], sweep["y"]
        cards.append(_card("Sensitivity sweep", sweep.get("hint", ""), "",
                           svg.line_sweep(xs, ys, xlabel=sweep.get("xlabel", "parameter"),
                                          ylabel=sweep.get("ylabel", "Spearman improvement")),
                           span2=True))

    # ---- headline dumbbell (span2, first) ----
    head = ""
    if has_exp:
        db = svg.dumbbell([dict(label="Spearman ρ vs experiment",
                                a=report.spearman_baseline_expt, b=report.spearman_corrected_expt,
                                a_name="baseline", b_name="corrected",
                                hint="higher is better · gray=baseline, blue=corrected")], dom=(0, 1))
        head = _card("Did the correction improve agreement with experiment?",
                     "the headline: classical baseline → quantum-corrected", "", db, span2=True)

    # ---- KPI tiles ----
    sp_c = f'{report.spearman_corrected_expt:.3f}' if has_exp else "—"
    sp_foot = (f'baseline {report.spearman_baseline_expt:.3f} · Δ {report.correlation_improvement:+.3f}'
               if has_exp else "no experimental affinities supplied")
    mae = (f'{report.mae_corrected:.2f}' if has_exp else str(report.n_ligands))
    mae_lbl = "Error vs exp (MAE)" if has_exp else "Ligands"
    mae_foot = (f'baseline {report.mae_baseline:.2f} kcal/mol' if has_exp else "in this study")
    tiles = "".join([
        _tile("Agreement (Spearman)", sp_c, sp_foot),
        _tile("Ranking moved", f'{report.n_rank_changes}<span style="font-size:16px;color:var(--muted)">/{report.n_ligands}</span>',
              f'Kendall τ {report.kendall_tau_rankings:.2f} · max shift {report.max_rank_shift}'),
        _tile("Mean correction", f'{report.mean_abs_delta:.2f}<span style="font-size:15px;color:var(--muted)"> kcal/mol</span>',
              f'max {report.max_abs_delta:.2f}'),
        _tile(mae_lbl, mae, mae_foot),
    ])

    # ---- table ----
    trs = []
    for r in rows:
        mv = r["rank_move"]
        pill = ('<span class="pill flat">=</span>' if mv == 0 else
                f'<span class="pill up">▲ {mv}</span>' if mv > 0 else
                f'<span class="pill down">▼ {-mv}</span>')
        exp = "" if r["experimental_dg"] is None else f'{r["experimental_dg"]:.2f}'
        trs.append(
            f'<tr><td>{r["corrected_rank"]}</td><td>{_e(r["ligand_id"])}</td>'
            f'<td>{r["corrected_score"]:.2f}</td><td>{r["baseline_score"]:.2f}</td>'
            f'<td>{r["delta"]:+.2f}</td><td>{exp}</td><td>{pill}</td></tr>')
    table = (
        '<table><thead><tr><th>Rank</th><th>Ligand</th><th>Corrected dG</th>'
        '<th>Baseline dG</th><th>Δ</th><th>Exp dG</th><th>Move</th></tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table>')
    cards.append(_card("Ranked candidates (by corrected dG, tightest first)",
                       "Δ = correlated correction · Move = rank change vs baseline", "", table, span2=True))

    # ---- assemble ----
    svar, sword = _status(report)
    ttl = title or f"{result.target_name} · {result.pocket}"
    banner_note = ('<div class="banner"><span class="dot" style="background:var(--warn)"></span>'
                   '<span><b>Reference / demo data</b> — validates the pipeline and visuals; '
                   'not a scientific result.</span></div>') if reference_mode else ""
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    body = f"""<style>{style_block()}</style>
<div class="wrap">
  <header class="top">
    <div><h1>{_e(ttl)}</h1>
      <div class="sub">SQD-corrected rescoring · quantum-vs-classical ranking delta</div></div>
    <button class="theme-toggle" onclick="tgl()">◐ theme</button>
  </header>
  {banner_note}
  <div class="banner"><span class="dot" style="background:var(--{svar})"></span>
    <span class="verdict">{_e(report.verdict)}</span></div>
  <div class="kpis">{tiles}</div>
  <div class="grid">{head}{"".join(cards)}</div>
  <footer>Generated {ts} · self-contained (no external assets) · solver: {_e(result.solver)}</footer>
</div>
<script>
  function tgl(){{var r=document.documentElement,
    d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    r.setAttribute('data-theme', d==='dark'?'light':'dark');}}
</script>"""
    if not full_document:
        return body
    return (f'<!doctype html>\n<html lang="en">\n<head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{_e(ttl)} — qbind</title></head>\n<body>\n{body}\n</body></html>')


def _card(title, hint, legend, body, span2=False) -> str:
    cls = "card span2" if span2 else "card"
    h = f'<p class="hint">{_e(hint)}</p>' if hint else ""
    return f'<div class="{cls}"><h3>{_e(title)}</h3>{h}{legend}{body}</div>'


def build_dashboard(result: StudyResult, report: DeltaReport, out_path,
                    *, reference_mode: bool, title: str | None = None, sweep=None) -> str:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(result, report, reference_mode=reference_mode,
                                    title=title, sweep=sweep), encoding="utf-8")
    return str(out_path)
