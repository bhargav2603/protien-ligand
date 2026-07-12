"""Design system for the interactive dashboard.

Colours are the validated reference palette from the data-viz method (categorical
blue+orange pass CVD ΔE ~97; status good/warn/critical are the reserved status
steps). Everything is exposed as CSS custom properties so inline SVG marks
(`fill="var(--corrected)"`) theme automatically in light/dark with the page.
No external libraries, no web fonts — the dashboard is fully self-contained.
"""
from __future__ import annotations

# Role -> (light, dark). Chart marks reference these by var name.
TOKENS = {
    # surfaces / ink / chrome
    "surface":  ("#fcfcfb", "#1a1a19"),
    "plane":    ("#f4f4f1", "#0d0d0d"),
    "ink":      ("#0b0b0b", "#ffffff"),
    "ink-2":    ("#52514e", "#c3c2b7"),
    "muted":    ("#898781", "#898781"),
    "grid":     ("#e1e0d9", "#2c2c2a"),
    "axis":     ("#c3c2b7", "#383835"),
    "border":   ("rgba(11,11,11,0.10)", "rgba(255,255,255,0.12)"),
    # series / identity
    "corrected": ("#2a78d6", "#3987e5"),   # blue  = quantum-corrected (primary)
    "baseline":  ("#898781", "#a9a89f"),   # gray  = classical baseline (recessive)
    "coord":     ("#eb6834", "#d95926"),   # orange = coordinates the fragment
    "nocoord":   ("#b9b8b1", "#6f6e68"),   # muted  = does not
    # status
    "good":     ("#0ca30c", "#0ca30c"),
    "warn":     ("#fab219", "#fab219"),
    "bad":      ("#d03b3b", "#d03b3b"),
}


def _vars(index: int) -> str:
    return "\n".join(f"      --{k}: {v[index]};" for k, v in TOKENS.items())


def style_block() -> str:
    """Return the full <style> content: tokens (light+dark), layout, components."""
    return f"""
    :root {{
{_vars(0)}
      --radius: 14px;
      --shadow: 0 1px 2px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.06);
      color-scheme: light dark;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
{_vars(1)}
        --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.5);
      }}
    }}
    :root[data-theme="light"] {{
{_vars(0)}
    }}
    :root[data-theme="dark"] {{
{_vars(1)}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--plane); color: var(--ink);
      font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }}
    header.top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }}
    h1 {{ font-size: 22px; margin: 0 0 2px; letter-spacing: -0.01em; }}
    .sub {{ color: var(--ink-2); font-size: 13.5px; }}
    .theme-toggle {{ border: 1px solid var(--border); background: var(--surface); color: var(--ink-2);
      border-radius: 999px; padding: 7px 14px; cursor: pointer; font-size: 13px; }}
    .banner {{ margin: 16px 0 4px; padding: 12px 16px; border-radius: 12px; font-size: 14px;
      border: 1px solid var(--border); background: var(--surface); display: flex; gap: 10px; align-items: center; }}
    .banner .dot {{ width: 10px; height: 10px; border-radius: 50%; flex: none; }}
    .verdict {{ font-size: 15px; font-weight: 600; }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 18px 0 6px; }}
    .tile {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 16px 18px; box-shadow: var(--shadow); }}
    .tile .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }}
    .tile .value {{ font-size: 30px; font-weight: 650; margin-top: 4px; letter-spacing: -0.02em; }}
    .tile .value.sm {{ font-size: 19px; font-weight: 620; }}
    .tile .foot {{ color: var(--ink-2); font-size: 12.5px; margin-top: 2px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-top: 16px; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 16px 16px 8px; box-shadow: var(--shadow); overflow: hidden; }}
    .card.span2 {{ grid-column: 1 / -1; }}
    .card h3 {{ margin: 0 0 2px; font-size: 15px; }}
    .card .hint {{ color: var(--muted); font-size: 12px; margin: 0 0 8px; }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 12.5px; color: var(--ink-2); margin: 2px 0 6px; }}
    .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
    .legend i {{ width: 11px; height: 11px; border-radius: 3px; display: inline-block; }}
    svg {{ width: 100%; height: auto; display: block; }}
    svg text {{ font-family: inherit; }}
    .mark {{ transition: opacity .12s; }}
    .mark:hover {{ opacity: .78; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: right; padding: 7px 10px; border-bottom: 1px solid var(--grid); white-space: nowrap; }}
    th:first-child, td:first-child {{ text-align: left; }}
    thead th {{ color: var(--muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: .05em; }}
    tbody tr:hover {{ background: color-mix(in srgb, var(--corrected) 7%, transparent); }}
    .pill {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 600; }}
    .up {{ color: var(--good); }} .down {{ color: var(--bad); }} .flat {{ color: var(--muted); }}
    footer {{ color: var(--muted); font-size: 12px; margin-top: 26px; text-align: center; }}
    """
