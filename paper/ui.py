"""Look and shared pieces of the paper site: type, colours, captions, the animated flow."""

from __future__ import annotations

import base64
from html import escape

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data

FONTS = data.PROJECT / "site" / "assets" / "fonts"
SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
SANS = "'Source Sans 3', -apple-system, 'Segoe UI', Arial, sans-serif"

INK, MUTED, RULE, PAPER, WASH = "#16181D", "#5B616B", "#DAD8D1", "#FCFBF8", "#F2F0EA"
ACCENT = "#0B5F66"
COLOUR = {
    "finalist_a": "#3F7CC0",
    "finalist_b": "#D27A50",
    "blank_invalid": "#3E9C7E",
    "abstention": "#D4A23C",
    "eliminated": "#9AA0A8",
}
FAMILY_COLOUR = {"Baseline": "#6B717B", "Proximity": ACCENT, "Mixture": "#8A6BB0"}


def outcome_scale(year: int | None = None) -> alt.Scale:
    return alt.Scale(
        domain=[
            data.outcome_label(year, r) if year else data.OUTCOME_LABEL[r] for r in data.OUTCOMES
        ],
        range=[COLOUR[r] for r in data.OUTCOMES],
    )


# ---- Page setup ---------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def _font_faces() -> str:
    faces = []
    for family, file in (
        ("Source Sans 3", "source-sans-3-latin-wght-normal.woff2"),
        ("Source Serif 4", "source-serif-4-latin-wght-normal.woff2"),
    ):
        encoded = base64.b64encode((FONTS / file).read_bytes()).decode("ascii")
        faces.append(
            f"@font-face{{font-family:'{family}';font-weight:200 900;font-display:swap;"
            f"src:url(data:font/woff2;base64,{encoded}) format('woff2');}}"
        )
    return "".join(faces)


CSS = """
.stApp { background: %(paper)s; color: %(ink)s; }
[data-testid="stMainBlockContainer"] { max-width: 860px; padding-top: 4.2rem; padding-bottom: 5rem; }
.stApp, .stApp p, .stApp li, .stApp td, .stApp th, .stApp label { font-family: %(sans)s; }
.stApp p, .stApp li { font-size: 1.06rem; line-height: 1.62; }
.stApp h1, .stApp h2, .stApp h3 { font-family: %(serif)s; color: %(ink)s; letter-spacing: -0.01em; }
.stApp h1 { font-size: 2.45rem; line-height: 1.12; font-weight: 600; }
.stApp h2 { font-size: 1.6rem; font-weight: 600; margin-top: 2.6rem; padding-bottom: .35rem;
            border-bottom: 1px solid %(rule)s; }
.stApp h3 { font-size: 1.2rem; font-weight: 600; margin-top: 1.4rem; }
[data-testid="stHeaderActionElements"] { display: none; }
.stApp a { color: %(accent)s; }

/* Motion: every block rises in gently when a page opens. */
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div {
  animation: rise .55s cubic-bezier(.2,.7,.2,1) both; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(n+3) { animation-delay: .06s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(n+5) { animation-delay: .12s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(n+7) { animation-delay: .18s; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

.kicker { font-family: %(sans)s; text-transform: uppercase; letter-spacing: .12em; font-size: .78rem;
          color: %(accent)s; font-weight: 700; margin: 0 0 .5rem; }
.byline { color: %(muted)s; font-size: .98rem; margin-top: -.3rem; }
.abstract { background: %(wash)s; border-left: 3px solid %(accent)s; padding: 1.1rem 1.35rem;
            margin: 1.4rem 0 1.6rem; }
.abstract p { margin: .3rem 0; font-size: 1.02rem; }
.abstract b.label { font-variant: small-caps; letter-spacing: .06em; color: %(accent)s; }
.question { font-family: %(serif)s; font-size: 1.45rem; line-height: 1.35; padding: 1rem 0 1rem 1.3rem;
            border-left: 3px solid %(ink)s; margin: 1.2rem 0; }
.caption { color: %(muted)s; font-size: .9rem; line-height: 1.5; margin: -.2rem 0 1.4rem; }
.caption b { color: %(ink)s; }
.callout { border: 1px solid %(rule)s; background: #fff; padding: .9rem 1.1rem; margin: 1rem 0;
           border-radius: 3px; }
.callout p { margin: .2rem 0; }
.callout.warn { border-color: #E6CF95; background: #FCF5E1; }
.finding { display: grid; grid-template-columns: 2.2rem 1fr; gap: .2rem .7rem; margin: 1.1rem 0; }
.finding .n { font-family: %(serif)s; font-size: 1.6rem; color: %(accent)s; line-height: 1; }
.finding h4 { font-family: %(serif)s; font-size: 1.12rem; margin: 0 0 .2rem; }
.finding p { margin: 0; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: 1rem 0 1.4rem; }
.stat { border-top: 2px solid %(ink)s; padding-top: .45rem; }
.stat .v { font-family: %(serif)s; font-size: 1.45rem; white-space: nowrap; line-height: 1.1; }
.stat .l { color: %(muted)s; font-size: .86rem; line-height: 1.35; }
.formula { font-family: %(serif)s; font-size: 1.08rem; text-align: center; margin: .6rem 0 1rem; }
.tag { display: inline-block; font-size: .78rem; font-weight: 600; padding: .05rem .45rem;
       border-radius: 2px; background: %(wash)s; color: %(muted)s; margin-right: .3rem; }
.hyp { border: 1px solid %(rule)s; background: #fff; padding: 1rem 1.15rem .8rem; margin: .6rem 0 1rem; border-radius: 3px; }
.hyp h4 { font-family: %(serif)s; margin: 0 0 .3rem; font-size: 1.15rem; }
.hyp .rule { font-family: %(serif)s; font-style: italic; color: %(ink)s; }
.toc a { text-decoration: none; }
.footer { margin-top: 3.5rem; padding-top: 1rem; border-top: 1px solid %(rule)s; color: %(muted)s; font-size: .86rem; }
table.paper { border-collapse: collapse; width: 100%%; font-size: .93rem; margin: .4rem 0 .6rem; }
table.paper th { text-align: right; font-weight: 600; border-bottom: 1.5px solid %(ink)s; padding: .35rem .5rem; }
table.paper th:first-child, table.paper td:first-child { text-align: left; }
table.paper td { text-align: right; padding: .3rem .5rem; border-bottom: 1px solid %(rule)s; font-variant-numeric: tabular-nums; }
table.paper tr.sep td { border-top: 1.5px solid %(ink)s; }
table.paper td.best { font-weight: 700; }
table.paper td.tie { font-weight: 700; color: %(muted)s; }
.pending { background: #FCF5E1; border: 1px solid #E6CF95; padding: 0 .3rem; border-radius: 2px; font-size: .85em; }
"""


def setup() -> None:
    style = CSS % {
        "paper": PAPER,
        "ink": INK,
        "muted": MUTED,
        "rule": RULE,
        "wash": WASH,
        "accent": ACCENT,
        "serif": SERIF,
        "sans": SANS,
    }
    st.html(f"<style>{_font_faces()}{style}</style>")
    alt.themes.register("paper", _altair_theme)
    alt.themes.enable("paper")


def _altair_theme() -> dict:
    return {
        "config": {
            "background": "transparent",
            "font": SANS,
            "view": {"stroke": None},
            "axis": {
                "labelColor": MUTED,
                "titleColor": MUTED,
                "titleFontWeight": 400,
                "labelFontSize": 12,
                "titleFontSize": 12,
                "gridColor": RULE,
                "domainColor": "#8A8F97",
                "tickColor": "#8A8F97",
            },
            "legend": {
                "labelFontSize": 12,
                "titleFontSize": 12,
                "titleFontWeight": 400,
                "labelColor": INK,
                "titleColor": MUTED,
                "orient": "top",
            },
            "header": {"labelFontSize": 13, "labelColor": INK, "titleFontWeight": 400},
            "title": {"font": SERIF, "fontSize": 15, "anchor": "start", "color": INK},
        }
    }


# ---- Text helpers -------------------------------------------------------------------


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def header(kicker: str, title: str, lead: str | None = None) -> None:
    html(f'<p class="kicker">{escape(kicker)}</p>')
    st.markdown(f"# {title}")
    if lead:
        html(f'<p class="byline">{lead}</p>')


def caption(label: str, text: str) -> None:
    html(f'<p class="caption"><b>{escape(label)}.</b> {text}</p>')


def callout(text: str, warn: bool = False) -> None:
    html(f'<div class="callout{" warn" if warn else ""}"><p>{text}</p></div>')


def finding(number: int, title: str, text: str) -> None:
    html(
        f'<div class="finding"><div class="n">{number}</div>'
        f"<div><h4>{title}</h4><p>{text}</p></div></div>"
    )


def stats(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="stat"><div class="v">{v}</div><div class="l">{label}</div></div>'
        for v, label in items
    )
    html(f'<div class="stat-row">{cells}</div>')


def footer() -> None:
    html(
        '<div class="footer">'
        f"{' · '.join(data.TEAM)}<br>{data.COURSE}<br>"
        "Source: Ministry of the Interior polling-station files (data.gouv.fr) and the "
        "left-to-right orders published by polling institutes. Results describe patterns in "
        "area totals, never individual transfers: the vote is secret. "
        f'Code and data: <a href="{data.REPOSITORY}">{data.REPOSITORY.removeprefix("https://")}</a>.'
        "</div>"
    )


def score_table(
    frame: pd.DataFrame,
    columns: list[str],
    tie_margin: float = 0.3,
    rows_after_sep: tuple[str, ...] = (),
) -> None:
    """A paper-style table of scores (lower is better) with the best of each column bold.

    Values within ``tie_margin`` pp of the column minimum are also marked, in grey: we
    do not read differences that small as a ranking.
    """
    head = "".join(f"<th>{escape(c)}</th>" for c in ["", *columns])
    body = []
    minima = {c: frame[c].min() for c in columns}
    for label, row in frame.iterrows():
        cells = [f"<td>{escape(str(label))}</td>"]
        for c in columns:
            v = row[c]
            cls = ""
            if np.isclose(v, minima[c]):
                cls = "best"
            elif v - minima[c] <= tie_margin:
                cls = "tie"
            cells.append(f'<td class="{cls}">{v:.1f}</td>')
        sep = ' class="sep"' if label in rows_after_sep else ""
        body.append(f"<tr{sep}>{''.join(cells)}</tr>")
    html(
        f'<table class="paper"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'
    )


# ---- The animated flow (round 1 -> round 2) ----------------------------------------


def flow_diagram(
    year: int,
    model: str,
    p: float | None = None,
    height: int = 560,
    observed: bool = True,
    key: str = "",
) -> None:
    """Animated ribbons from every first-round group to the four second-round outcomes.

    Widths are shares of registered voters, pooled over the covered areas. Ribbons of
    groups that keep their position (the finalists' voters, blank voters, abstainers)
    are drawn pale: no model moves them. Grey outlines on the right show the observed
    second round, so the gap between prediction and reality is visible.
    """
    flows = data.flows(year, model, p)
    e = data.election(year)
    s = data.scores(year)
    eliminated = sorted(e.eliminated, key=lambda g: (s.get(g) is None, s.get(g) or 0))
    retained = list(e.outcomes)
    order = eliminated + retained
    actual = data.pooled(year, e.actual) * 100

    W, top, gap = 760, 34, 2.2
    usable = height - top - 18 - gap * (len(order) + 1)
    unit = usable / 100.0
    left_x, right_x, node_w = 210, 560, 14

    # Left nodes.
    y = top
    left = {}
    for g in order:
        if g == retained[0]:
            y += 10  # a little air before the retained groups
        h = max(flows.loc[g].sum() * unit, 0.8)
        left[g] = (y, h)
        y += h + gap
    # Right nodes: stack outcomes, sized by the larger of predicted and observed.
    predicted = flows.sum(axis=0).to_numpy()
    y = top
    right = {}
    for k, role in enumerate(data.OUTCOMES):
        h = predicted[k] * unit
        hobs = actual[k] * unit
        right[role] = (y, h, hobs)
        y += max(h, hobs) + 14

    paths, labels, nodes = [], [], []
    right_cursor = {r: right[r][0] for r in data.OUTCOMES}
    for i, g in enumerate(order):
        y0, _ = left[g]
        cursor = y0
        for role in data.OUTCOMES:
            v = flows.loc[g, role]
            if v <= 1e-6:
                continue
            h = v * unit
            ry = right_cursor[role]
            right_cursor[role] += h
            x0, x1 = left_x + node_w, right_x
            c = (x0 + x1) / 2
            d = (
                f"M{x0},{cursor:.2f} C{c},{cursor:.2f} {c},{ry:.2f} {x1},{ry:.2f} "
                f"L{x1},{ry + h:.2f} C{c},{ry + h:.2f} {c},{cursor + h:.2f} {x0},{cursor + h:.2f} Z"
            )
            pale = g in retained
            tip = f"{data.name(year, g)} → {data.outcome_label(year, role)}: {v:.1f}% of registered"
            paths.append(
                f'<path d="{d}" fill="{COLOUR[role]}" fill-opacity="{0.16 if pale else 0.62}" '
                f'style="animation-delay:{0.04 * i:.2f}s"><title>{escape(tip)}</title></path>'
            )
            cursor += h
        # Left node and label.
        y0, h = left[g]
        role = g if g in retained else "eliminated"
        fill = (
            COLOUR["finalist_a"]
            if g == e.finalists[0]
            else COLOUR["finalist_b"]
            if g == e.finalists[1]
            else COLOUR.get(role, COLOUR["eliminated"])
        )
        nodes.append(
            f'<rect x="{left_x}" y="{y0:.2f}" width="{node_w}" height="{h:.2f}" fill="{fill}"/>'
        )
        share = flows.loc[g].sum()
        if h >= 9 or share >= 1.5:
            pos = s.get(g)
            pos_txt = "" if g in retained else (" · not placed" if pos is None else f" · {pos:.2f}")
            labels.append(
                f'<text x="{left_x - 8}" y="{y0 + h / 2 + 4:.2f}" text-anchor="end" class="lab">'
                f"{escape(data.name(year, g))} <tspan class='num'>{share:.1f}%{pos_txt}</tspan></text>"
            )
    for k, role in enumerate(data.OUTCOMES):
        y0, h, hobs = right[role]
        nodes.append(
            f'<rect class="grow" x="{right_x}" y="{y0:.2f}" width="{node_w}" height="{h:.2f}" fill="{COLOUR[role]}"/>'
        )
        if observed:
            nodes.append(
                f'<rect x="{right_x + node_w + 4}" y="{y0:.2f}" width="6" height="{hobs:.2f}" '
                f'fill="none" stroke="#2B2F36" stroke-width="1.2" stroke-dasharray="2 2"/>'
            )
        gap_pp = predicted[k] - actual[k]
        obs = f"observed {actual[k]:.1f}% ({gap_pp:+.1f} pp)" if observed else ""
        labels.append(
            f'<text x="{right_x + node_w + 16}" y="{y0 + max(h, hobs) / 2 - 2:.2f}" class="lab strong">'
            f"{escape(data.outcome_label(year, role))}</text>"
            f'<text x="{right_x + node_w + 16}" y="{y0 + max(h, hobs) / 2 + 14:.2f}" class="num">'
            f"predicted {predicted[k]:.1f}% · {obs}</text>"
        )
    heads = (
        f'<text x="{left_x + node_w}" y="16" text-anchor="end" class="head">ROUND 1 · {year}</text>'
        f'<text x="{right_x}" y="16" class="head">ROUND 2 · predicted by {escape(model)}</text>'
        f'<text x="{left_x - 8}" y="{left[retained[0]][0] - 4:.2f}" text-anchor="end" class="hint">'
        "keep their position in every model ↓</text>"
        f'<text x="{left_x - 8}" y="{top - 6}" text-anchor="end" class="hint">eliminated, left → right ↓</text>'
    )
    svg = (
        f'<svg viewBox="0 0 {W + 140} {height}" width="100%" xmlns="http://www.w3.org/2000/svg">'
        f"{heads}<g class='ribbons'>{''.join(paths)}</g>{''.join(nodes)}{''.join(labels)}</svg>"
    )
    style = f"""
    <style>
    body {{ margin:0; background:transparent; font-family:{SANS}; }}
    .lab {{ font-size:12px; fill:{INK}; }} .strong {{ font-weight:600; font-size:13px; }}
    .num {{ font-size:11px; fill:{MUTED}; }} .head {{ font-size:11px; letter-spacing:.1em; fill:{MUTED}; font-weight:600; }}
    .hint {{ font-size:10.5px; fill:{MUTED}; font-style:italic; }}
    .ribbons path {{ animation: draw 1.1s cubic-bezier(.2,.7,.2,1) both; transform-origin: left; }}
    .ribbons path:hover {{ fill-opacity:.9; }}
    @keyframes draw {{ from {{ opacity:0; transform: scaleX(.05); }} to {{ opacity:1; transform:none; }} }}
    .grow {{ animation: grow .9s .35s cubic-bezier(.2,.7,.2,1) both; transform-box: fill-box; transform-origin: top; }}
    @keyframes grow {{ from {{ transform: scaleY(0); }} to {{ transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
    </style>"""
    st.iframe(
        f"<!doctype html><html><head>{style}</head><body>{svg}<!-- {escape(key)} --></body></html>",
        height=height + 6,
    )


# ---- Charts -------------------------------------------------------------------------


def position_strip(year: int, show_threshold: bool = True, height: int = 170) -> alt.Chart:
    """Candidates of one election on the 0-1 scale, sized by first-round share."""
    table = data.candidate_table(year).dropna(subset=["score"]).copy()
    table["Role"] = table.role.map(
        {
            "finalist_a": data.finalists(year)[0],
            "finalist_b": data.finalists(year)[1],
            "eliminated": "Eliminated",
        }
    )
    a, b = (data.scores(year)[f] for f in data.election(year).finalists)
    layers = []
    if show_threshold:
        t = data.threshold()
        lo, hi = min(a, b), max(a, b)
        zones = pd.DataFrame(
            [{"x0": 0, "x1": max(0, lo - t)}, {"x0": min(1, hi + t), "x1": 1}]
            + ([{"x0": lo + t, "x1": hi - t}] if hi - lo > 2 * t else [])
        )
        zones = zones[zones.x1 > zones.x0]
        if len(zones):
            layers.append(
                alt.Chart(zones)
                .mark_rect(color="#E9DFC6", opacity=0.55)
                .encode(x=alt.X("x0:Q", scale=alt.Scale(domain=[-0.02, 1.02])), x2="x1:Q")
            )
    dots = (
        alt.Chart(table)
        .mark_circle(stroke=INK, strokeWidth=0.6, opacity=0.9)
        .encode(
            x=alt.X(
                "score:Q",
                title="Poll-based position: 0 = leftmost, 1 = rightmost",
                scale=alt.Scale(domain=[-0.02, 1.02]),
                axis=alt.Axis(values=[0, 0.2, 0.4, 0.6, 0.8, 1], format=".1f"),
            ),
            size=alt.Size("share:Q", scale=alt.Scale(range=[40, 1400]), legend=None),
            color=alt.Color(
                "Role:N",
                scale=alt.Scale(
                    domain=[*data.finalists(year), "Eliminated"],
                    range=[COLOUR["finalist_a"], COLOUR["finalist_b"], COLOUR["eliminated"]],
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("candidate:N", title="Candidate"),
                alt.Tooltip("party:N", title="Party"),
                alt.Tooltip("score:Q", title="Position", format=".2f"),
                alt.Tooltip("share:Q", title="Round 1, % registered", format=".1f"),
            ],
        )
    )
    labelled = table[table.share >= 3].sort_values("score").reset_index(drop=True)
    labelled["dy"] = [-24 if i % 2 == 0 else 26 for i in range(len(labelled))]
    text = (
        alt.Chart(labelled)
        .mark_text(fontSize=11, color=INK)
        .encode(x="score:Q", text="candidate:N", yOffset=alt.YOffset("dy:Q", scale=None))
    )
    return alt.layer(*layers, dots, text).properties(height=height)
