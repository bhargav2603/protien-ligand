"""Inline-SVG chart builders. Pure string output; no dependencies.

Marks follow the data-viz mark specs: thin strokes, >=8px markers, rounded bar
ends with a surface gap, recessive grid/axis, native <title> hover tooltips, and
fills bound to CSS variables so they theme with the page. Identity is never
colour-alone: a legend is rendered by the dashboard and key marks are labelled.
"""
from __future__ import annotations

import html
from typing import Sequence


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _fmt(v: float, nd: int = 2) -> str:
    return f"{v:.{nd}f}"


def _scale(d0, d1, r0, r1):
    if d1 == d0:
        return lambda _v: (r0 + r1) / 2
    m = (r1 - r0) / (d1 - d0)
    return lambda v: r0 + (v - d0) * m


# --------------------------------------------------------------------------- #
def scatter(points: Sequence[dict], *, domain=None, width=360, height=320,
            xlabel="experimental dG", ylabel="predicted dG") -> str:
    """points: {x, y, label, group}. Square panel with a y=x reference line."""
    ml, mr, mt, mb = 46, 14, 14, 40
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    lo, hi = (domain if domain else (min(xs + ys), max(xs + ys)))
    pad = (hi - lo) * 0.08 or 1.0
    lo, hi = lo - pad, hi + pad
    sx = _scale(lo, hi, ml, width - mr)
    sy = _scale(lo, hi, height - mb, mt)

    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(ylabel)} vs {_esc(xlabel)}">']
    # y=x reference
    out.append(f'<line x1="{sx(lo):.1f}" y1="{sy(lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}" '
               f'stroke="var(--axis)" stroke-width="1.5" stroke-dasharray="3 4"/>')
    # axes
    out.append(f'<line x1="{ml}" y1="{height-mb}" x2="{width-mr}" y2="{height-mb}" stroke="var(--axis)" stroke-width="1"/>')
    out.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{height-mb}" stroke="var(--axis)" stroke-width="1"/>')
    for t in (lo + pad, (lo + hi) / 2, hi - pad):
        out.append(f'<text x="{sx(t):.1f}" y="{height-mb+16}" fill="var(--muted)" font-size="10" '
                   f'text-anchor="middle">{_fmt(t,1)}</text>')
        out.append(f'<text x="{ml-6}" y="{sy(t)+3:.1f}" fill="var(--muted)" font-size="10" '
                   f'text-anchor="end">{_fmt(t,1)}</text>')
    # points
    for p in points:
        col = f'var(--{p["group"]})'
        out.append(
            f'<circle class="mark" cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="5.5" '
            f'fill="{col}" stroke="var(--surface)" stroke-width="1.5">'
            f'<title>{_esc(p["label"])}\nexp {_fmt(p["x"])}  ·  pred {_fmt(p["y"])}</title></circle>')
    out.append(f'<text x="{(ml+width-mr)/2:.0f}" y="{height-4}" fill="var(--ink-2)" font-size="11" '
               f'text-anchor="middle">{_esc(xlabel)} (kcal/mol)</text>')
    out.append('</svg>')
    return "".join(out)


# --------------------------------------------------------------------------- #
def slopegraph(rows: Sequence[dict], *, width=360, row_h=26) -> str:
    """rows: {label, left, right, group, moved}. Ranks: 1 at top."""
    n = len(rows)
    mt, mb = 26, 14
    height = mt + mb + n * row_h
    lx, rx = 118, width - 118
    ranks = [r["left"] for r in rows] + [r["right"] for r in rows]
    sy = _scale(min(ranks), max(ranks), mt, height - mb)

    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="ranking change">']
    out.append(f'<text x="{lx}" y="14" fill="var(--muted)" font-size="10.5" text-anchor="middle">baseline</text>')
    out.append(f'<text x="{rx}" y="14" fill="var(--muted)" font-size="10.5" text-anchor="middle">corrected</text>')
    for r in rows:
        col = f'var(--{r["group"]})'
        y0, y1 = sy(r["left"]), sy(r["right"])
        w = 2.4 if r["moved"] else 1.2
        op = 1.0 if r["moved"] else 0.5
        out.append(f'<g class="mark"><title>{_esc(r["label"])}\nrank {r["left"]} → {r["right"]}</title>'
                   f'<line x1="{lx}" y1="{y0:.1f}" x2="{rx}" y2="{y1:.1f}" stroke="{col}" '
                   f'stroke-width="{w}" opacity="{op}"/>'
                   f'<circle cx="{lx}" cy="{y0:.1f}" r="4.5" fill="{col}" opacity="{op}"/>'
                   f'<circle cx="{rx}" cy="{y1:.1f}" r="4.5" fill="{col}" opacity="{op}"/>'
                   f'<text x="{lx-9}" y="{y0+3:.1f}" fill="var(--ink-2)" font-size="10.5" text-anchor="end">{_esc(r["label"])}</text>'
                   f'<text x="{rx+9}" y="{y1+3:.1f}" fill="var(--ink-2)" font-size="10.5">{_esc(r["label"])}</text></g>')
    out.append('</svg>')
    return "".join(out)


# --------------------------------------------------------------------------- #
def diverging_bars(items: Sequence[dict], *, width=360, row_h=24, unit="kcal/mol") -> str:
    """items: {label, value, group}. Horizontal bars around a zero baseline."""
    n = len(items)
    mt, mb, ml = 10, 24, 60
    height = mt + mb + n * row_h
    vals = [it["value"] for it in items] or [0]
    vmax = max(1e-6, max(abs(v) for v in vals))
    zero = ml + (width - ml - 14) * 0.5
    sx = _scale(-vmax, vmax, ml, width - 14)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="per-ligand correction">']
    out.append(f'<line x1="{zero:.1f}" y1="{mt}" x2="{zero:.1f}" y2="{height-mb}" stroke="var(--axis)" stroke-width="1"/>')
    for i, it in enumerate(items):
        y = mt + i * row_h + row_h / 2
        col = f'var(--{it["group"]})'
        x = sx(it["value"])
        x0, x1 = (zero, x) if x >= zero else (x, zero)
        bw = max(2.0, x1 - x0)
        out.append(f'<g class="mark"><title>{_esc(it["label"])}\n{_fmt(it["value"])} {unit}</title>'
                   f'<rect x="{x0:.1f}" y="{y-6:.1f}" width="{bw:.1f}" height="12" rx="3.5" fill="{col}"/>'
                   f'<text x="{ml-8}" y="{y+3:.1f}" fill="var(--ink-2)" font-size="10.5" text-anchor="end">{_esc(it["label"])}</text></g>')
    for t, lab in ((-vmax, _fmt(-vmax,1)), (vmax, "+"+_fmt(vmax,1))):
        out.append(f'<text x="{sx(t):.1f}" y="{height-8}" fill="var(--muted)" font-size="9.5" text-anchor="middle">{lab}</text>')
    out.append(f'<text x="{zero:.1f}" y="{height-8}" fill="var(--muted)" font-size="9.5" text-anchor="middle">0</text>')
    out.append('</svg>')
    return "".join(out)


# --------------------------------------------------------------------------- #
def dumbbell(rows: Sequence[dict], *, width=360, row_h=54, dom=(0.0, 1.0)) -> str:
    """rows: {label, a, b, a_name, b_name, hint}. a=baseline dot, b=corrected dot."""
    n = len(rows)
    mt, mb, ml = 14, 26, 14
    height = mt + mb + n * row_h
    sx = _scale(dom[0], dom[1], ml + 96, width - 40)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="agreement before and after">']
    for i, r in enumerate(rows):
        y = mt + i * row_h + 18
        xa, xb = sx(r["a"]), sx(r["b"])
        up = r["b"] >= r["a"]
        out.append(f'<text x="{ml}" y="{y+3:.1f}" fill="var(--ink-2)" font-size="12">{_esc(r["label"])}</text>')
        out.append(f'<line x1="{xa:.1f}" y1="{y:.1f}" x2="{xb:.1f}" y2="{y:.1f}" '
                   f'stroke="var(--{"good" if up else "bad"})" stroke-width="2.5" opacity=".6"/>')
        out.append(f'<circle class="mark" cx="{xa:.1f}" cy="{y:.1f}" r="7" fill="var(--baseline)" stroke="var(--surface)" stroke-width="1.5">'
                   f'<title>{_esc(r.get("a_name","baseline"))}: {_fmt(r["a"],3)}</title></circle>')
        out.append(f'<circle class="mark" cx="{xb:.1f}" cy="{y:.1f}" r="7" fill="var(--corrected)" stroke="var(--surface)" stroke-width="1.5">'
                   f'<title>{_esc(r.get("b_name","corrected"))}: {_fmt(r["b"],3)}</title></circle>')
        d = r["b"] - r["a"]
        out.append(f'<text x="{max(xa,xb)+12:.1f}" y="{y+3:.1f}" fill="var(--{"good" if up else "bad"})" '
                   f'font-size="12" font-weight="600">{"+" if d>=0 else ""}{_fmt(d,3)}</text>')
        out.append(f'<text x="{ml}" y="{y+20:.1f}" fill="var(--muted)" font-size="10">{_esc(r.get("hint",""))}</text>')
    out.append('</svg>')
    return "".join(out)


# --------------------------------------------------------------------------- #
def line_sweep(xs, ys, *, width=520, height=260, xlabel="", ylabel="", zero_line=True) -> str:
    """A single-series line for a parameter sweep (sensitivity)."""
    ml, mr, mt, mb = 52, 16, 16, 40
    xlo, xhi = min(xs), max(xs)
    ylo, yhi = min(ys + [0.0]), max(ys + [0.0])
    pad = (yhi - ylo) * 0.1 or 0.05
    ylo, yhi = ylo - pad, yhi + pad
    sx = _scale(xlo, xhi, ml, width - mr)
    sy = _scale(ylo, yhi, height - mb, mt)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(ylabel)} vs {_esc(xlabel)}">']
    if zero_line and ylo < 0 < yhi:
        out.append(f'<line x1="{ml}" y1="{sy(0):.1f}" x2="{width-mr}" y2="{sy(0):.1f}" stroke="var(--axis)" stroke-width="1" stroke-dasharray="3 4"/>')
    out.append(f'<line x1="{ml}" y1="{height-mb}" x2="{width-mr}" y2="{height-mb}" stroke="var(--axis)" stroke-width="1"/>')
    out.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{height-mb}" stroke="var(--axis)" stroke-width="1"/>')
    pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys))
    out.append(f'<polyline points="{pts}" fill="none" stroke="var(--corrected)" stroke-width="2.5" stroke-linejoin="round"/>')
    for x, y in zip(xs, ys):
        out.append(f'<circle class="mark" cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="4.5" fill="var(--corrected)" stroke="var(--surface)" stroke-width="1.5">'
                   f'<title>{_esc(xlabel)} {_fmt(x,2)}\n{_esc(ylabel)} {_fmt(y,3)}</title></circle>')
    for t in (xlo, (xlo + xhi) / 2, xhi):
        out.append(f'<text x="{sx(t):.1f}" y="{height-mb+16}" fill="var(--muted)" font-size="10" text-anchor="middle">{_fmt(t,1)}</text>')
    for t in (ylo + pad, yhi - pad):
        out.append(f'<text x="{ml-6}" y="{sy(t)+3:.1f}" fill="var(--muted)" font-size="10" text-anchor="end">{_fmt(t,2)}</text>')
    out.append(f'<text x="{(ml+width-mr)/2:.0f}" y="{height-4}" fill="var(--ink-2)" font-size="11" text-anchor="middle">{_esc(xlabel)}</text>')
    out.append('</svg>')
    return "".join(out)
