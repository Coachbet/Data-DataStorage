"""Chart builders. One theme, one outcome palette, direct labels, zero baselines.

Titles, subtitles and source lines are HTML around the chart (see
``components.figure``), so they wrap on small screens and are read by assistive
technology. A builder only draws marks.
"""

import math

import pandas as pd
import streamlit as st
from theme import COLOUR, OUTCOME, OUTCOME_NAMES, vega_config
from vote_transfer.application.presentation import ROLES, fmt_pct, fmt_pp

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


def mean_bars(comparison: pd.DataFrame) -> None:
    """One bar per assumption: its average error over the elections, value written at the end.

    The lowest bar is in the accent colour, the two baselines in ink, the others in grey.
    """
    frame = comparison[["mean"]].rename_axis("Model").reset_index()
    best = frame.loc[frame["mean"].idxmin(), "Model"]
    frame["Score"] = frame["mean"].map(fmt_pp)
    frame["group"] = [
        "best" if m == best else "baseline" if m in ("H0a", "H0b") else "other" for m in frame.Model
    ]
    groups = ["best", "baseline", "other"]
    spec = {
        "height": {"step": 34},
        "encoding": {
            "y": {
                "field": "Model",
                "type": "nominal",
                "sort": frame.Model.tolist(),
                "axis": {"title": None, "labelColor": INK, "labelFontWeight": 600},
            },
            "x": {
                "field": "mean",
                "type": "quantitative",
                "scale": {"domain": [0, nice_max(float(frame["mean"].max()) * 1.15, 2)]},
                "axis": {"title": "Average error per area (pp), lower is closer", "tickCount": 5},
            },
            "tooltip": [{"field": "Model"}, {"field": "Score", "title": "Average error"}],
        },
        "layer": [
            {
                "mark": {"type": "bar", "height": 20, "cornerRadiusEnd": 3},
                "encoding": {
                    "fill": {
                        "field": "group",
                        "type": "nominal",
                        "scale": {
                            "domain": groups,
                            "range": [COLOUR["accent"], INK, COLOUR["context"]],
                        },
                        "legend": None,
                    },
                    "stroke": {
                        "field": "group",
                        "type": "nominal",
                        "scale": {
                            "domain": groups,
                            "range": [COLOUR["accent-strong"], INK, COLOUR["context-line"]],
                        },
                        "legend": None,
                    },
                },
            },
            {
                "mark": {"type": "text", "align": "left", "dx": 6},
                "encoding": {"text": {"field": "Score"}},
            },
        ],
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
        # Room on the right, so the last bar and the "100" tick are never clipped.
        "padding": {"left": 0, "top": 4, "right": 16, "bottom": 4},
        "autosize": {"type": "fit-x", "contains": "padding"},
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
        f"{row.year} · finalists at {row.finalist_a_score:.2f} and {row.finalist_b_score:.2f}"
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
