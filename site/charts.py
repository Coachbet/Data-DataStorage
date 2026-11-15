"""Chart builders. One theme, one outcome palette, direct labels, zero baselines.

Titles, subtitles and source lines are HTML around the chart (see
``components.figure``), so they wrap on small screens and are read by assistive
technology. A builder only draws marks.
"""

import math

import pandas as pd
import streamlit as st
from theme import COLOUR, OUTCOME, OUTCOME_NAMES, vega_config
from vote_transfer.application.presentation import ROLES, election_columns, fmt_pct, fmt_pp

SEGMENTS = (*ROLES[:2], "other", *ROLES[2:])
FILLS = [OUTCOME[s][0] for s in SEGMENTS]
LINES = [OUTCOME[s][1] for s in SEGMENTS]
INK, MUTED, PAPER = COLOUR["ink"], COLOUR["muted"], COLOUR["paper"]


def show(data: pd.DataFrame, spec: dict) -> None:
    st.vega_lite_chart(data, {**spec, "config": vega_config()}, width="stretch", theme=None)


def role_colour(field: str = "role") -> dict:
    """Fill and outline by outcome role; the outline keeps pale fills visible."""
    return {
        "fill": {
            "field": field,
            "type": "nominal",
            "scale": {"domain": list(SEGMENTS), "range": FILLS},
            "legend": None,
        },
        "stroke": {
            "field": field,
            "type": "nominal",
            "scale": {"domain": list(SEGMENTS), "range": LINES},
            "legend": None,
        },
    }


def nice_max(value: float, step: float = 5) -> float:
    return max(step, math.ceil(value / step) * step)


def comparison_dots(comparison: pd.DataFrame, highlight: list[str], note: dict | None) -> None:
    """Every assumption's score in every election; three named, the rest as context."""
    years = election_columns(comparison)
    frame = comparison[years].rename_axis("Model").reset_index()
    frame = frame.melt("Model", var_name="Election", value_name="score")
    frame["Score"] = frame.score.map(fmt_pp)
    frame["named"] = frame.Model.isin(highlight)
    named = comparison.loc[highlight, years]
    # Name the points once, in the election where they are furthest apart.
    gaps = {
        y: min(abs(a - b) for i, a in enumerate(named[y]) for b in named[y][i + 1 :]) for y in years
    }
    frame["label"] = [
        row.Model if row.named and row.Election == max(gaps, key=gaps.get) else ""
        for row in frame.itertuples()
    ]
    tooltip = [{"field": "Model"}, {"field": "Election"}, {"field": "Score"}]
    layers = [
        {
            "transform": [{"filter": "!datum.named"}],
            "mark": {
                "type": "point",
                "filled": True,
                "size": 70,
                "fill": COLOUR["context"],
                "stroke": COLOUR["context-line"],
                "strokeWidth": 1,
            },
            "encoding": {"tooltip": tooltip},
        },
        {
            "transform": [{"filter": "datum.named"}],
            "mark": {"type": "point", "size": 150, "strokeWidth": 2, "opacity": 1},
            "encoding": {
                "shape": {
                    "field": "Model",
                    "scale": {"domain": highlight, "range": ["circle", "circle", "diamond"]},
                    "legend": None,
                },
                "fill": {
                    "field": "Model",
                    "scale": {"domain": highlight, "range": [PAPER, INK, COLOUR["accent"]]},
                    "legend": None,
                },
                "stroke": {
                    "field": "Model",
                    "scale": {"domain": highlight, "range": [INK, INK, COLOUR["accent-strong"]]},
                    "legend": None,
                },
                "tooltip": tooltip,
            },
        },
        {
            "transform": [{"filter": "datum.label != ''"}],
            "mark": {"type": "text", "dy": -16, "fontWeight": 600, "fontSize": 13},
            "encoding": {"text": {"field": "label"}},
        },
    ]
    if note:
        layers.append(
            {
                "data": {"values": [note]},
                "mark": {
                    "type": "text",
                    "align": "right",
                    "dy": 19,
                    "color": MUTED,
                    "fontSize": 13,
                },
                "encoding": {"text": {"field": "text"}},
            }
        )
    spec = {
        "height": {"step": 60},
        "encoding": {
            "y": {
                "field": "Election",
                "type": "ordinal",
                "sort": years,
                "axis": {"title": None, "grid": True, "labelColor": INK, "labelFontWeight": 600},
            },
            "x": {
                "field": "score",
                "type": "quantitative",
                "scale": {"domain": [0, nice_max(float(frame.score.max()))]},
                "axis": {
                    "title": "Average error per area, in percentage points (lower is closer)",
                    "grid": False,
                    "tickCount": 5,
                },
            },
        },
        "layer": layers,
    }
    show(frame, spec)


def stacked_rows(frame: pd.DataFrame, names: dict[str, str], axis_title: str) -> None:
    """Rows that each sum to 100%: one bar per row, values written under the bar."""
    chart = frame.copy()
    chart["end"] = chart.groupby("row", sort=False).pct.cumsum()
    chart["start"] = chart.end - chart.pct
    chart["middle"] = (chart.start + chart.end) / 2
    chart["Outcome"] = chart.segment.map(names)
    chart["Share"] = chart.pct.map(fmt_pct)
    chart["label"] = chart.Share.where(chart.pct >= 6, "")
    spec = {
        "height": {"step": 54},
        "encoding": {
            "y": {
                "field": "row",
                "type": "nominal",
                "sort": list(dict.fromkeys(chart.row)),
                "axis": {"title": None, "labelColor": INK, "labelLimit": 150},
            }
        },
        "layer": [
            {
                "mark": {"type": "bar", "height": 20, "yOffset": -8},
                "encoding": {
                    "x": {
                        "field": "start",
                        "type": "quantitative",
                        "scale": {"domain": [0, 100]},
                        "axis": {"title": axis_title, "tickCount": 5, "grid": False},
                    },
                    "x2": {"field": "end"},
                    **role_colour("segment"),
                    "tooltip": [
                        {"field": "row", "title": "Row"},
                        {"field": "Outcome"},
                        {"field": "Share"},
                    ],
                },
            },
            {
                "mark": {"type": "text", "dy": 13, "fontSize": 12.5},
                "encoding": {
                    "x": {"field": "middle", "type": "quantitative"},
                    "text": {"field": "label"},
                },
            },
        ],
    }
    show(chart, spec)


def round_bars(frame: pd.DataFrame, axis_title: str) -> None:
    """One bar per first- or second-round option, coloured by what it becomes in round two."""
    chart = frame.copy()
    chart["Share"] = chart.value.map(fmt_pct)
    spec = {
        "height": {"step": 30},
        "encoding": {
            "y": {
                "field": "outcome",
                "type": "nominal",
                "sort": chart.outcome.tolist(),
                "axis": {"title": None, "labelColor": INK, "labelLimit": 170},
            },
            "x": {
                "field": "value",
                "type": "quantitative",
                "scale": {"domain": [0, min(100, max(10, float(chart.value.max()) * 1.18))]},
                "axis": {"title": axis_title, "tickCount": 5},
            },
            "tooltip": [{"field": "outcome", "title": "Outcome"}, {"field": "Share"}],
        },
        "layer": [
            {"mark": {"type": "bar", "height": 18}, "encoding": role_colour()},
            {
                "mark": {"type": "text", "align": "left", "dx": 6},
                "encoding": {"text": {"field": "Share"}},
            },
        ],
    }
    show(chart, spec)


def observed_vs_model(frame: pd.DataFrame, model: str) -> None:
    """Observed (solid) beside one assumption (outlined) for the four outcomes."""
    chart = frame.melt(
        id_vars=["outcome", "role"],
        value_vars=["actual_share", "predicted_share"],
        var_name="series",
        value_name="value",
    )
    chart["value"] *= 100
    chart["series"] = chart.series.map({"actual_share": "Observed", "predicted_share": model})
    chart["label"] = chart.series + " " + chart.value.map(fmt_pct)
    order = ["Observed", model]
    common = {
        "y": {
            "field": "outcome",
            "type": "nominal",
            "sort": frame.outcome.tolist(),
            "axis": {"title": None, "labelColor": INK, "labelLimit": 170},
        },
        "yOffset": {"field": "series", "sort": order},
        "x": {
            "field": "value",
            "type": "quantitative",
            "scale": {"domain": [0, min(100, float(chart.value.max()) * 1.35)]},
            "axis": {"title": "Share of registered voters (%)", "tickCount": 5},
        },
        "tooltip": [{"field": "outcome", "title": "Outcome"}, {"field": "label", "title": "Value"}],
    }
    colours = role_colour()
    spec = {
        "height": {"step": 23},
        "encoding": common,
        "layer": [
            {
                "transform": [{"filter": "datum.series == 'Observed'"}],
                "mark": {"type": "bar"},
                "encoding": colours,
            },
            {
                "transform": [{"filter": "datum.series != 'Observed'"}],
                "mark": {"type": "bar", "fill": PAPER, "strokeWidth": 2},
                "encoding": {"stroke": colours["stroke"]},
            },
            {
                "mark": {"type": "text", "align": "left", "dx": 6, "fontSize": 12.5},
                "encoding": {"text": {"field": "label"}},
            },
        ],
    }
    show(chart, spec)


def largest_error(frame: pd.DataFrame) -> str:
    """The largest pooled gap of one assumption, in words: '−37.7 pp, Finalist A, 2002'."""
    row = frame.loc[frame.signed_error_pp.abs().idxmax()]
    return f"{fmt_pp(row.signed_error_pp, signed=True)} ({OUTCOME_NAMES[row.role]}, {row.year})"


def signed_errors(frame: pd.DataFrame, limits: tuple[float, float]) -> None:
    """Predicted minus observed for one assumption: four outcomes in each election.

    The largest gap is outlined in ink; ``largest_error`` gives the same fact in words.
    """
    chart = frame.copy()
    chart["Outcome"] = chart.role.map(OUTCOME_NAMES)
    chart["Election"] = chart.year.astype(str)
    chart["Error"] = chart.signed_error_pp.map(lambda v: fmt_pp(v, signed=True))
    chart["largest"] = chart.index == chart.signed_error_pp.abs().idxmax()
    offset = {"field": "role", "sort": list(ROLES)}
    across = {
        "field": "Election",
        "type": "nominal",
        "axis": {"title": None, "labelAngle": 0, "labelColor": INK},
    }
    spec = {
        "height": 170,
        "encoding": {
            "y": {
                "field": "signed_error_pp",
                "type": "quantitative",
                "scale": {"domain": list(limits)},
                "axis": {"title": "pp", "tickCount": 5},
            },
        },
        "layer": [
            {
                "mark": {"type": "bar"},
                "encoding": {
                    "x": across,
                    "xOffset": offset,
                    **role_colour(),
                    "tooltip": [
                        {"field": "model", "title": "Assumption"},
                        {"field": "Election"},
                        {"field": "Outcome"},
                        {"field": "Error", "title": "Predicted − observed"},
                    ],
                },
            },
            {
                "transform": [{"filter": "datum.largest"}],
                "mark": {"type": "bar", "fillOpacity": 0, "stroke": INK, "strokeWidth": 2},
                "encoding": {"x": across, "xOffset": offset},
            },
            {
                "data": {"values": [{"zero": 0}]},
                "mark": {"type": "rule", "color": INK, "strokeWidth": 1},
                "encoding": {"y": {"field": "zero", "type": "quantitative"}},
            },
        ],
    }
    show(chart, spec)


def threshold_bars(threshold: pd.DataFrame) -> None:
    """Share of the electorate that the fixed H2 threshold sends to a non-vote."""
    chart = threshold.copy()
    chart["Election"] = [
        f"{row.year} · finalists at {row.finalist_a_score} and {row.finalist_b_score}"
        for row in chart.itertuples()
    ]
    chart["Share"] = chart.beyond_threshold_pct.map(fmt_pct)
    spec = {
        "height": {"step": 34},
        "encoding": {
            "y": {
                "field": "Election",
                "type": "nominal",
                "sort": chart.Election.tolist(),
                "axis": {"title": None, "labelColor": INK, "labelLimit": 220},
            },
            "x": {
                "field": "beyond_threshold_pct",
                "type": "quantitative",
                "scale": {"domain": [0, nice_max(float(chart.beyond_threshold_pct.max()) * 1.15)]},
                "axis": {"title": "Share of registered voters (%)", "tickCount": 5},
            },
            "tooltip": [{"field": "Election"}, {"field": "Share"}],
        },
        "layer": [
            {
                "mark": {
                    "type": "bar",
                    "height": 18,
                    "fill": COLOUR["context"],
                    "stroke": COLOUR["context-line"],
                }
            },
            {
                "mark": {"type": "text", "align": "left", "dx": 6},
                "encoding": {"text": {"field": "Share"}},
            },
        ],
    }
    show(chart, spec)


def scatter(frame: pd.DataFrame) -> None:
    """Predicted against observed share, one point per area and outcome."""
    chart = frame.copy()
    chart["Outcome"] = chart.role.map(OUTCOME_NAMES)
    chart["Observed"] = chart.actual_pct.map(fmt_pct)
    chart["Predicted"] = chart.predicted_pct.map(fmt_pct)
    top = nice_max(float(max(chart.actual_pct.max(), chart.predicted_pct.max())), 10)
    scale = {"domain": [0, top]}
    spec = {
        "height": 420,
        "layer": [
            {
                "data": {"values": [{"v": 0}, {"v": top}]},
                "mark": {"type": "line", "color": COLOUR["context-line"], "strokeDash": [4, 4]},
                "encoding": {
                    "x": {"field": "v", "type": "quantitative", "scale": scale},
                    "y": {"field": "v", "type": "quantitative", "scale": scale},
                },
            },
            {
                "data": {"values": [{"x": top * 0.04, "y": top * 0.96}]},
                "mark": {
                    "type": "text",
                    "align": "left",
                    "color": MUTED,
                    "text": "Above the line: predicted too high",
                },
                "encoding": {
                    "x": {"field": "x", "type": "quantitative"},
                    "y": {"field": "y", "type": "quantitative"},
                },
            },
            {
                "mark": {"type": "point", "size": 42, "opacity": 0.75, "strokeWidth": 1},
                "encoding": {
                    "x": {
                        "field": "actual_pct",
                        "type": "quantitative",
                        "scale": scale,
                        "axis": {
                            "title": "Observed share of registered voters (%)",
                            "tickCount": 7,
                        },
                    },
                    "y": {
                        "field": "predicted_pct",
                        "type": "quantitative",
                        "scale": scale,
                        "axis": {"title": "Predicted share (%)", "tickCount": 7},
                    },
                    **role_colour(),
                    "shape": {
                        "field": "Territory",
                        "type": "nominal",
                        "scale": {
                            "domain": ["Metropolitan", "Overseas or abroad"],
                            "range": ["circle", "triangle-up"],
                        },
                        "legend": None,
                    },
                    "tooltip": [
                        {"field": "Area"},
                        {"field": "Territory"},
                        {"field": "Outcome"},
                        {"field": "Observed"},
                        {"field": "Predicted"},
                    ],
                },
            },
        ],
    }
    show(chart, spec)
