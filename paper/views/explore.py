"""Explore: the raw election results and every model's prediction, area by area."""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data
import ui


def render() -> None:
    ui.header(
        "Section 5 · Explore the data",
        "Play with the numbers",
        "Pick an election and an area. Everything below is computed live from the cleaned tables.",
    )
    c1, c2, c3 = st.columns([1, 2, 1])
    year = c1.selectbox("Election", data.YEARS[::-1], key="ex_year")
    res = data.results(year)
    areas = (
        res[["department_code", "department_name"]].drop_duplicates().sort_values("department_code")
    )
    labels = {
        "ALL": "All covered areas",
        **dict(
            zip(
                areas.department_code,
                areas.department_code + " · " + areas.department_name,
                strict=True,
            )
        ),
    }
    area = c2.selectbox("Area", list(labels), format_func=labels.get, key="ex_area")
    base = c3.radio(
        "Percent of",
        ["Registered", "Valid votes"],
        key="ex_base",
        help="Our models use registered voters; news reports use valid votes.",
    )

    sel = res if area == "ALL" else res[res.department_code == area]
    e = data.election(year)
    totals = sel.groupby(["round", "option", "label"], as_index=False)["count"].sum()
    reg = sel.drop_duplicates(["round", "department_code"]).groupby("round").registered.sum()
    totals["pct_registered"] = totals.apply(lambda r: r["count"] / reg[r["round"]] * 100, axis=1)
    valid = totals[totals.option.str.startswith("candidate:")].groupby("round")["count"].sum()
    totals["pct_valid"] = totals.apply(
        lambda r: (
            r["count"] / valid[r["round"]] * 100 if r.option.startswith("candidate:") else np.nan
        ),
        axis=1,
    )
    col = "pct_registered" if base == "Registered" else "pct_valid"

    r1 = totals[totals["round"] == 1]
    r2 = totals[totals["round"] == 2]
    ab1 = r1.loc[r1.option == "abstention", "pct_registered"].sum()
    ab2 = r2.loc[r2.option == "abstention", "pct_registered"].sum()
    bl1 = r1.loc[r1.option == "blank_invalid", "pct_registered"].sum()
    bl2 = r2.loc[r2.option == "blank_invalid", "pct_registered"].sum()
    ui.stats(
        [
            (f"{reg[2]:,.0f}", "registered voters in round 2"),
            (f"{ab1:.1f}% → {ab2:.1f}%", "abstention, round 1 → round 2"),
            (f"{bl1:.1f}% → {bl2:.1f}%", "blank or invalid, round 1 → round 2"),
            (
                f"{(1 - (r1[r1.option.isin(e.outcomes)].pct_registered.sum() / 100)) * 100:.1f}%",
                "voted for an eliminated candidate",
            ),
        ]
    )

    ui.section("explore", "s5-1")
    role = {
        e.finalists[0]: "Finalist A",
        e.finalists[1]: "Finalist B",
        "blank_invalid": "Blank or invalid",
        "abstention": "Abstention",
    }
    r1 = r1.assign(
        Group=r1.option.map(role).fillna("Eliminated"), Name=[data.name(year, o) for o in r1.option]
    )
    r1 = r1.dropna(subset=[col]).sort_values(col, ascending=False)
    names = list(r1.Name)
    bars = (
        alt.Chart(r1)
        .mark_bar(height={"band": 0.75})
        .encode(
            y=alt.Y(
                "Name:N", sort=names, title=None, axis=alt.Axis(labelOverlap=False, labelLimit=200)
            ),
            x=alt.X(f"{col}:Q", title=f"% of {base.lower()}"),
            color=alt.Color(
                "Group:N",
                scale=alt.Scale(
                    domain=[
                        "Finalist A",
                        "Finalist B",
                        "Blank or invalid",
                        "Abstention",
                        "Eliminated",
                    ],
                    range=[
                        ui.COLOUR[k]
                        for k in (
                            "finalist_a",
                            "finalist_b",
                            "blank_invalid",
                            "abstention",
                            "eliminated",
                        )
                    ],
                ),
                title=None,
            ),
            tooltip=[
                "Name",
                alt.Tooltip("count:Q", format=","),
                alt.Tooltip(f"{col}:Q", format=".2f", title="%"),
            ],
        )
    )
    txt = bars.mark_text(align="left", dx=3, fontSize=11, color=ui.INK).encode(
        text=alt.Text(f"{col}:Q", format=".1f")
    )
    st.altair_chart((bars + txt).properties(height=26 * len(r1)), width="stretch")
    ui.caption(
        "Figure 5.1",
        f"{labels[area]}, {year}. Source: Ministry of the Interior. "
        "Switch to <i>valid votes</i> to see the percentages usually reported in the news.",
    )

    ui.section("explore", "s5-2")
    order = [e.finalists[0], e.finalists[1], "blank_invalid", "abstention"]

    def grp(o):  # noqa: E306
        return {
            e.finalists[0]: data.outcome_label(year, "finalist_a"),
            e.finalists[1]: data.outcome_label(year, "finalist_b"),
            "blank_invalid": "Blank or invalid",
            "abstention": "Abstention",
        }.get(o, "Eliminated candidates")

    both = (
        totals.assign(Group=totals.option.map(grp))
        .groupby(["round", "Group"], as_index=False)
        .pct_registered.sum()
    )
    both["Round"] = "Round " + both["round"].astype(str)
    both = both.drop(columns="round").rename(columns={"pct_registered": "pct"})
    domain = [grp(o) for o in order] + ["Eliminated candidates"]
    both["o"] = both.Group.map({g: i for i, g in enumerate(domain)})
    stack = (
        alt.Chart(both)
        .mark_bar(size=46)
        .encode(
            y=alt.Y(
                "Round:N",
                title=None,
                sort=["Round 1", "Round 2"],
                scale=alt.Scale(paddingInner=0.35),
            ),
            x=alt.X(
                "pct:Q",
                title="% of registered voters",
                stack="zero",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color(
                "Group:N",
                scale=alt.Scale(
                    domain=domain,
                    range=[ui.COLOUR[k] for k in data.OUTCOMES] + [ui.COLOUR["eliminated"]],
                ),
                title=None,
            ),
            order=alt.Order("o:Q"),
            tooltip=["Round", "Group", alt.Tooltip("pct:Q", format=".1f")],
        )
        .properties(height=alt.Step(64))
    )
    st.altair_chart(stack, width="stretch")
    ui.caption(
        "Figure 5.2",
        "The grey block of round 1 is what every assumption has to redistribute. "
        "Each round has its own number of registered voters. Totals only: they do not show who moved where.",
    )

    ui.section("explore", "s5-3")
    model = st.segmented_control("Assumption", data.MODELS, default="H0b", key="ex_model") or "H0b"
    pred = data.prediction(year, model)
    rows = []
    for i, code in enumerate(e.areas):
        for k, roleo in enumerate(data.OUTCOMES):
            rows.append(
                {
                    "code": code,
                    "area": labels.get(code, code),
                    "outcome": data.outcome_label(year, roleo),
                    "predicted": pred[i, k] * 100,
                    "observed": e.actual[i, k] * 100,
                    "selected": area == "ALL" or code == area,
                }
            )
    pts = pd.DataFrame(rows)
    line = (
        alt.Chart(pd.DataFrame({"v": [0, 75]}))
        .mark_line(color=ui.MUTED, strokeDash=[4, 3])
        .encode(x="v:Q", y="v:Q")
    )
    scatter = (
        alt.Chart(pts)
        .mark_circle(size=34)
        .encode(
            x=alt.X(
                "observed:Q",
                title="Observed share of registered (%)",
                scale=alt.Scale(domain=[0, 75]),
            ),
            y=alt.Y("predicted:Q", title="Predicted share (%)", scale=alt.Scale(domain=[0, 75])),
            color=alt.Color("outcome:N", scale=ui.outcome_scale(year), title=None),
            opacity=alt.condition("datum.selected", alt.value(0.85), alt.value(0.12)),
            tooltip=[
                "area",
                "outcome",
                alt.Tooltip("predicted:Q", format=".1f"),
                alt.Tooltip("observed:Q", format=".1f"),
            ],
        )
    )
    st.altair_chart((line + scatter).properties(height=430), width="stretch")
    err = np.abs(pred - e.actual).mean(axis=1) * 100
    area_err = pd.DataFrame(
        {
            "Area": [labels.get(a, a) for a in e.areas],
            "Error (pp)": err,
            "Registered (round 2)": e.registered_r2.astype(int),
        }
    )
    sc = data.score(year, pred)
    ui.caption(
        "Figure 5.3",
        f"{model}, {year}: one point per area and outcome; on the dashed line the "
        f"prediction equals the observation. Weighted average error: <b>{sc:.1f} pp</b>."
        + (
            ""
            if area == "ALL"
            else f" {labels[area]}: {float(area_err.set_index('Area').loc[labels[area], 'Error (pp)']):.1f} pp."
        ),
    )

    with st.expander("Every area's error for this assumption (sortable, downloadable)"):
        st.dataframe(
            area_err.sort_values("Error (pp)", ascending=False),
            hide_index=True,
            width="stretch",
            column_config={
                "Error (pp)": st.column_config.NumberColumn(format="%.2f"),
                "Registered (round 2)": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.download_button(
            "Download this table (CSV)",
            area_err.to_csv(index=False).encode(),
            f"errors_{model}_{year}.csv",
            "text/csv",
        )
    ui.box(
        "definition",
        "<b>How the score is computed.</b> For each area: the absolute gap between predicted and "
        "observed share, for each of the four outcomes, averaged (no weighting between "
        "outcomes). Then the average over areas, each weighted by its round-2 registered voters. "
        "Gaps are taken <i>before</i> averaging, so an overestimate in one area cannot cancel an "
        "underestimate in another.",
    )
