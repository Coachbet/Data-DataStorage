"""Hypotheses: what each assumption says, shown as animated flows, plus two playgrounds."""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data
import ui


def render() -> None:
    ui.header(
        "Section 3 · Hypotheses",
        "Nine rules for where eliminated voters go",
        "Each assumption is a rule simple enough to say in one sentence, "
        "and precise enough to compute.",
    )

    st.markdown("## 3.1 An assumption is a transfer table")
    st.markdown(
        "Every assumption fills the same table. Each **row** is a first-round group (a "
        "candidate, the blank voters, the abstainers); each **column** is a second-round "
        "outcome (finalist A, finalist B, blank or invalid, abstention); each cell says which "
        "share of the row goes to the column. Multiply an area's first-round shares by the "
        "table and you get its predicted second round."
    )
    ui.html(
        '<p class="formula">predicted share of outcome <i>k</i> &nbsp;=&nbsp; '
        "Σ<sub>groups g</sub> &nbsp;(first-round share of <i>g</i>) × (share of <i>g</i> that goes to <i>k</i>)</p>"
    )
    ui.callout(
        "<b>What every assumption has in common.</b> Four groups keep their position in "
        "<i>all</i> nine rules: the voters of finalist A stay with A, the voters of finalist B "
        "stay with B, first-round blank or invalid voters stay blank, and <b>first-round "
        "abstainers stay at home</b>. The rules only differ in where the voters of "
        "<b>eliminated</b> candidates go. Consequence: any real movement of these four groups "
        "(for example, people who abstained in round 1 and vote in round 2) is an error that "
        "no rule can remove. It sets a floor under every score and makes the rules look "
        "closer to each other than they are."
    )
    st.markdown(
        "*Finalist A* is the finalist with more first-round votes, *finalist B* the other; the "
        "labels use only first-round information."
    )

    st.markdown("## 3.2 The three families")
    _family(
        "Baselines: politics does not matter",
        "They use no information about candidates. They are the bar the other rules must clear.",
        [
            (
                "H0a",
                "Eliminated voters split like the whole electorate, abstainers included.",
                "share to outcome <i>k</i> = first-round share of <i>k</i> ÷ (A + B + blank + abstention)",
                "Our original baseline. It implies that a large share of people who bothered to vote "
                "in round 1 stay home in round 2.",
            ),
            (
                "H0b",
                "Eliminated voters split like the voters only: nobody newly abstains.",
                "share to <i>k</i> = first-round share of <i>k</i> ÷ (A + B + blank), and 0 to abstention",
                "Added after the second peer review, once H0a's abstention problem was known: it "
                "answers a result, it was not planned in advance.",
            ),
        ],
    )
    _family(
        "Proximity: voters follow the left-right scale",
        "They need a position for every candidate, taken from polling institutes (0 = left, 1 = right).",
        [
            (
                "H1",
                "Each eliminated group goes entirely to the finalist nearest on the scale.",
                "all to the nearer finalist; an exact tie splits 50/50",
                "The textbook story of vote transfers. All-or-nothing by construction.",
            ),
            (
                "H1-soft",
                "Each group splits between the finalists; the nearer one gets more.",
                "share to A = distance to B ÷ (distance to A + distance to B)",
                "Added after the first results were known, in response to a review. No parameter.",
            ),
            (
                "H2-abst / H2-blank",
                "Like H1, unless the candidate is far from both finalists: then the "
                "group abstains (H2-abst) or votes blank (H2-blank).",
                "far = at least ⅓ of the scale from both finalists",
                "The threshold of ⅓ was fixed before any result was computed and never tuned.",
            ),
        ],
    )
    _family(
        "Mixture: a bit of both",
        "The only rules with a number estimated from data.",
        [
            (
                "H3",
                "A share p of each eliminated group behaves like H0b; the rest follows H1 or H2.",
                "table = (1 − p) × proximity rule + p × H0b",
                "p is fitted on four elections and scored on the fifth (leave-one-election-out), "
                "so it is never scored on data it has seen.",
            ),
        ],
    )

    st.markdown("## 3.3 Watch a rule move the voters")
    st.markdown(
        "Pick an election and an assumption. The ribbons show where the rule sends each "
        "first-round group, as a share of registered voters over all covered areas. "
        "Eliminated candidates are ordered from left to right on the scale. The dashed "
        "outlines on the right are what really happened. Hover a ribbon for its size."
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        year = st.selectbox("Election", data.YEARS[::-1], key="flow_year")
    with c2:
        model = (
            st.segmented_control("Assumption", data.MODELS, default="H1", key="flow_model") or "H1"
        )
    ui.flow_diagram(year, model, key=f"{year}-{model}")
    sc = data.comparison().loc[model, str(year)]
    best = data.comparison()[str(year)].idxmin()
    ui.caption(
        f"Figure 3 ({model}, {year})",
        f"{data.ONE_LINE[model]} Average error per area for this election: <b>{sc:.1f} pp</b> "
        f"(best this year: {best}, {data.comparison().loc[best, str(year)]:.1f} pp). Pale ribbons "
        "are the four groups that never move. This shows what a rule <i>assumes</i>, not an "
        "observed transfer."
        + (
            f" H3 uses p = {data.fold_p(model[3:-1], year):.2f}, fitted without {year}."
            if model.startswith("H3")
            else ""
        ),
    )

    st.markdown("### One group, nine destinations")
    group_year = year
    _one_group(group_year)

    st.markdown("## 3.4 Playground: the mixture parameter p")
    st.markdown(
        "H3 mixes a proximity rule with H0b. Slide p from 0 (pure proximity) to 1 (pure H0b) "
        "and watch the error of each election. The fitted value is the p that minimises the "
        "average error on the four *other* elections."
    )
    base = st.radio(
        "Proximity rule mixed with H0b",
        ["H1", "H2-abst", "H2-blank"],
        horizontal=True,
        key="p_base",
    )
    p = st.slider("Share p that behaves like H0b", 0.0, 1.0, 0.25, 0.01, key="p_value")
    curves = _p_curves(base)
    marks = pd.DataFrame([{"year": str(y), "p": data.fold_p(base, y)} for y in data.YEARS])
    marks = marks.merge(curves, on=["year", "p"], how="left")
    now = curves[np.isclose(curves.p, round(p, 2))]
    line = (
        alt.Chart(curves)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("p:Q", title="p (0 = pure proximity rule, 1 = pure H0b)"),
            y=alt.Y("score:Q", title="Error (pp), lower is closer"),
            color=alt.Color("year:N", title="Election"),
        )
    )
    fitted = (
        alt.Chart(marks)
        .mark_point(shape="diamond", size=110, filled=True)
        .encode(
            x="p:Q",
            y="score:Q",
            color="year:N",
            tooltip=[
                alt.Tooltip("year:N"),
                alt.Tooltip("p:Q", title="fitted p (held out)", format=".2f"),
            ],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"p": [p]}))
        .mark_rule(color=ui.INK, strokeDash=[4, 3])
        .encode(x="p:Q")
    )
    dots = alt.Chart(now).mark_circle(size=70, color=ui.INK).encode(x="p:Q", y="score:Q")
    st.altair_chart(alt.layer(line, rule, dots, fitted).properties(height=320), width="stretch")
    mean_now = now.score.mean()
    ui.caption(
        "Figure 4",
        f"Error of H3({base}) as p changes, per election. Diamonds: the p fitted with that "
        f"election held out. At p = {p:.2f} the five-election mean is <b>{mean_now:.2f} pp</b>. "
        "On the H2 bases the fitted p is close to 1: the fit almost throws the H2 rule away. "
        "On H1, p is small except when 2002 is held out.",
    )

    st.markdown("## 3.5 Playground: build your own rule")
    st.markdown(
        "Decide what eliminated voters do, in four parts. The site applies your rule to every "
        "area of every election and scores it exactly like ours."
    )
    cols = st.columns(4)
    raw = {
        "nearest": cols[0].slider("Go to the nearest finalist", 0, 100, 40, 5, key="mix_near"),
        "proportional": cols[1].slider("Split like voters (H0b)", 0, 100, 50, 5, key="mix_prop"),
        "abstain": cols[2].slider("Abstain", 0, 100, 5, 5, key="mix_abst"),
        "blank": cols[3].slider("Vote blank", 0, 100, 5, 5, key="mix_blank"),
    }
    total = sum(raw.values()) or 1
    mixture = {k: v / total for k, v in raw.items()}
    ui.html(
        "<p class='caption'>Normalised to 100%: "
        + " · ".join(f"{k} <b>{v * 100:.0f}%</b>" for k, v in mixture.items())
        + "</p>"
    )
    yours = {y: data.score(y, data.predict_custom(y, mixture)) for y in data.YEARS}
    c = data.comparison()
    table = pd.DataFrame(
        {
            "Your rule": [*yours.values(), np.mean(list(yours.values()))],
            "H0b": [*(c.loc["H0b", str(y)] for y in data.YEARS), c.loc["H0b", "mean"]],
            "H1": [*(c.loc["H1", str(y)] for y in data.YEARS), c.loc["H1", "mean"]],
            "Best of our nine": [*(c[str(y)].min() for y in data.YEARS), c["mean"].min()],
        },
        index=[*map(str, data.YEARS), "Mean"],
    )
    ui.score_table(table.T, list(table.index), tie_margin=0)
    ui.caption(
        "Table 4",
        "Error in pp per election (lower is closer). Bold: lowest in each column. Tuning "
        "these sliders while looking at the scores is exactly what we refused to do with our "
        "own rules: a rule chosen this way fits these five elections and tells you little "
        "about the next one.",
    )


def _family(title: str, lead: str, items: list[tuple[str, str, str, str]]) -> None:
    st.markdown(f"### {title}")
    st.markdown(lead)
    for name, rule, formula, note in items:
        ui.html(
            f'<div class="hyp"><h4>{name}</h4><p class="rule">{rule}</p>'
            f'<p style="font-size:.92rem;color:{ui.MUTED};margin:.3rem 0 0"><span class="tag">rule</span>{formula}</p>'
            f'<p style="font-size:.92rem;color:{ui.MUTED};margin:.2rem 0 0"><span class="tag">note</span>{note}</p></div>'
        )


def _one_group(year: int) -> None:
    e = data.election(year)
    first = data.pooled_first(year)
    s = data.scores(year)
    placed = [g for g in e.eliminated if s.get(g) is not None]
    group = max(placed, key=lambda g: first[g])
    rows = []
    for model in data.MODELS:
        f = data.flows(year, model)
        row = f.loc[group] / f.loc[group].sum() * 100
        for role in data.OUTCOMES:
            rows.append(
                {"model": model, "outcome": data.outcome_label(year, role), "share": row[role]}
            )
    frame = pd.DataFrame(rows)
    chart = (
        alt.Chart(frame)
        .mark_bar(height={"band": 0.72})
        .encode(
            y=alt.Y(
                "model:N",
                sort=list(data.MODELS),
                title=None,
                axis=alt.Axis(labelOverlap=False, labelFontSize=12),
            ),
            x=alt.X(
                "share:Q",
                stack="normalize",
                title=f"Share of {data.name(year, group)}'s voters",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color("outcome:N", scale=ui.outcome_scale(year), title=None),
            order=alt.Order("order:Q"),
            tooltip=["model", "outcome", alt.Tooltip("share:Q", format=".1f", title="%")],
        )
        .transform_calculate(
            order=f"indexof({[data.outcome_label(year, r) for r in data.OUTCOMES]}, datum.outcome)"
        )
    )
    st.altair_chart(chart.properties(height=330), width="stretch")
    a, b = (s[f] for f in e.finalists)
    ui.caption(
        f"Figure 5 ({year})",
        f"The largest eliminated group, {data.name(year, group)} ({first[group] * 100:.1f}% of "
        f"registered voters, position {s[group]:.2f}; finalists at {a:.2f} and {b:.2f}), under "
        "each assumption. Change the election above to see another group.",
    )


@st.cache_data(show_spinner=False)
def _p_curves(base: str) -> pd.DataFrame:
    rows = []
    grid = np.round(np.arange(101) / 100, 2)
    for y in data.YEARS:
        b = data.prediction(y, base)
        h = data.prediction(y, "H0b")
        for p in grid:
            rows.append({"year": str(y), "p": p, "score": data.score(y, (1 - p) * b + p * h)})
    return pd.DataFrame(rows)
