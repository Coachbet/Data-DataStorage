"""3. Hypotheses: each assumption explained, formalised, illustrated and animated."""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data
import ui

PAGE = "hypotheses"
EXAMPLE_YEAR = 2022


def render() -> None:
    ui.header(
        "Section 3 · Hypotheses",
        "Nine rules for where eliminated voters go",
        "Each assumption is simple enough to say in one sentence and precise enough to compute. "
        "Open the boxes for the formula, a worked example and the result.",
    )
    _transfer_table()
    _baselines()
    _proximity()
    _mixture()
    _flows()
    _p_playground()
    _own_rule()


# ---- helpers --------------------------------------------------------------------------


def _example_group(year: int = EXAMPLE_YEAR) -> str:
    e = data.election(year)
    first = data.pooled_first(year)
    s = data.scores(year)
    return max((g for g in e.eliminated if s.get(g) is not None), key=lambda g: first[g])


def _row(model: str, year: int = EXAMPLE_YEAR) -> pd.Series:
    """Where a model sends the largest eliminated group, in % of that group."""
    group = _example_group(year)
    f = data.flows(year, model).loc[group]
    return f / f.sum() * 100


def _hypothesis(
    code: str,
    family: str,
    tags: list[tuple[str, str]],
    rule: str,
    plain: str,
    formula: str,
    why: str,
    weakness: str,
) -> None:
    c = data.comparison()
    tag_html = "".join(f'<span class="tag {cls}">{escape_(t)}</span>' for cls, t in tags)
    score = (
        f'<span style="float:right;font-size:.9rem;color:{ui.MUTED}">mean error '
        f'<b style="color:{ui.INK}">{c.loc[code, "mean"]:.1f} pp</b> · rank {int(c.loc[code, "rank"])}/9</span>'
    )
    ui.html(f'<div class="hyp">{score}<h4>{code} {tag_html}</h4><p class="rule">{rule}</p></div>')
    with st.expander(f"{code} — explanation, formula, example and weak point"):
        t1, t2, t3, t4 = st.tabs(
            ["In plain words", "Formula", "Worked example", "Why, and weak point"]
        )
        with t1:
            st.markdown(plain, unsafe_allow_html=True)
        with t2:
            st.latex(formula)
        with t3:
            year = EXAMPLE_YEAR
            group = _example_group(year)
            s = data.scores(year)
            a, b = (s[f] for f in data.election(year).finalists)
            row = _row(code, year)
            st.markdown(
                f"**{data.name(year, group)}** in {year}: {data.pooled_first(year)[group] * 100:.1f}% of "
                f"registered voters, position **{s[group]:.2f}**; finalists "
                f"{data.finalists(year)[0]} at {a:.2f} and {data.finalists(year)[1]} at {b:.2f}. "
                f"Under {code}, this group goes:"
            )
            ui.html(
                '<table class="paper"><thead><tr>'
                + "".join(f"<th>{data.outcome_label(year, r)}</th>" for r in data.OUTCOMES)
                + "</tr></thead><tbody><tr>"
                + "".join(f"<td>{row[r]:.1f}%</td>" for r in data.OUTCOMES)
                + "</tr></tbody></table>"
            )
            st.markdown(
                f"Average error over five elections: **{c.loc[code, 'mean']:.1f} pp** "
                f"(without 2002: {c.loc[code, 'mean_without_2002']:.1f} pp)."
            )
        with t4:
            st.markdown(f"**Why we test it.** {why}", unsafe_allow_html=True)
            st.markdown(f"**Weak point.** {weakness}", unsafe_allow_html=True)


def escape_(text: str) -> str:
    from html import escape

    return escape(text)


# ---- 3.1 -------------------------------------------------------------------------------


def _transfer_table() -> None:
    ui.section(PAGE, "s3-1")
    st.markdown("Every assumption fills **the same table**, called a *transfer matrix* $\\beta$:")
    st.markdown(
        "- each **row** is a first-round group $g$: a candidate, the blank or invalid voters, "
        "the abstainers;\n"
        "- each **column** is a second-round outcome $k$: finalist A, finalist B, blank or "
        "invalid, abstention;\n"
        "- each cell $\\beta_{g,k}$ is the share of group $g$ that goes to outcome $k$. Each "
        "row adds up to 1."
    )
    st.markdown("For an area $a$ with first-round shares $x_{a,g}$, the predicted second round is")
    st.latex(
        r"\hat s_{a,k} \;=\; \sum_{g} x_{a,g}\,\beta_{g,k},\qquad \beta_{g,k}\ge 0,\qquad \sum_k \beta_{g,k}=1"
    )
    ui.box(
        "definition",
        "<p><b>Finalist A</b> is the finalist with more first-round votes, <b>finalist B</b> the "
        "other. All shares are shares of <b>registered voters</b>, so abstention is an outcome "
        "like any other.</p>",
    )
    ui.box(
        "note",
        "<p>Four groups keep their position in <b>all nine rules</b>: voters of finalist A stay "
        "with A, voters of finalist B stay with B, first-round blank or invalid voters stay "
        "blank, and <b>first-round abstainers stay at home</b>. The rules differ only in the "
        "rows of <b>eliminated</b> candidates.</p>",
        label="What every rule shares",
    )
    with st.expander("Consequence: an error floor shared by every rule"):
        st.markdown(
            "Any real movement of these four groups is an error that **no** rule can remove: "
            "for example, people who abstained in round 1 and vote in round 2, or finalists' "
            "voters who cast a blank ballot in round 2. This floor makes the nine rules look "
            "closer to each other than they really are."
        )
    with st.expander("See a full transfer matrix (H1, 2022, all areas pooled)"):
        year = EXAMPLE_YEAR
        f = data.flows(year, "H1")
        m = (f.div(f.sum(axis=1), axis=0) * 100).round(0)
        m.index = [data.name(year, g) for g in m.index]
        m.columns = [data.outcome_label(year, r) for r in data.OUTCOMES]
        st.dataframe(
            m.style.format("{:.0f}%").background_gradient(cmap="Blues", vmin=0, vmax=100),
            width="stretch",
        )
        st.caption(
            "Rows: first-round groups. Columns: second-round outcomes. Each row sums to 100%."
        )


# ---- 3.2-3.4 -------------------------------------------------------------------------


def _baselines() -> None:
    ui.section(PAGE, "s3-2")
    st.markdown(
        "Baselines use **no information about candidates**. They are the bar every other rule "
        "must clear: if a rule that knows politics cannot beat a rule that ignores it, "
        "politics adds nothing."
    )
    _hypothesis(
        "H0a",
        "Baseline",
        [("baseline", "Baseline"), ("fixed", "No parameter")],
        "Eliminated voters split like the whole electorate, abstainers included.",
        "Imagine the voters of an eliminated candidate pick their second-round behaviour by "
        "copying the rest of the area: if 25% of the area abstained in round 1, 25% of them "
        "abstain in round 2. This was our original baseline (named H0 until 15 November).",
        r"\beta_{g,k} = \frac{x_k}{x_A + x_B + x_{\text{blank}} + x_{\text{abst}}}\quad\text{for } k\in\{A,B,\text{blank},\text{abst}\}",
        "Without a rule that ignores politics, we could not tell whether the other rules add anything.",
        "It sends a large share of people who <i>did</i> vote in round 1 to abstention. The "
        "second peer review asked whether this was deliberate; it turned out to explain most of "
        "its error.",
    )
    _hypothesis(
        "H0b",
        "Baseline",
        [("baseline", "Baseline"), ("fixed", "No parameter"), ("added", "Added after review 2")],
        "Eliminated voters split like the voters only: nobody newly abstains.",
        "Same idea as H0a, but people who voted once vote again: they split between the two "
        "finalists and the blank ballot, in proportion to their first-round strength in the area.",
        r"\beta_{g,k} = \frac{x_k}{x_A + x_B + x_{\text{blank}}}\ \ (k\in\{A,B,\text{blank}\}),\qquad \beta_{g,\text{abst}}=0",
        "It answers the second peer review's question: is H0a a fair baseline? H0b is the "
        "strongest rule that still ignores politics.",
        "It was added <i>after</i> H0a's abstention problem was known, so it is a response to a "
        "result, not a rule planned in advance.",
    )


def _proximity() -> None:
    ui.section(PAGE, "s3-3")
    st.markdown(
        "Proximity rules use the **left–right position** $s_c\\in[0,1]$ of each candidate "
        "(Data, 2.5) and the distance to each finalist:"
    )
    st.latex(r"d(c,F) = \lvert s_c - s_F\rvert,\qquad F\in\{A,B\}")
    _hypothesis(
        "H1",
        "Proximity",
        [("proximity", "Proximity"), ("fixed", "No parameter")],
        "Each eliminated group goes entirely to the finalist nearest on the scale.",
        "The textbook story of vote transfers: left-wing voters go to the more left-wing "
        "finalist, right-wing voters to the more right-wing one. A candidate exactly halfway "
        "splits 50/50 (two cases: Boutin 2002, Nihous 2007).",
        r"\beta_{g,A}=\begin{cases}1 & d(c,A)<d(c,B)\\ \tfrac12 & d(c,A)=d(c,B)\\ 0 & \text{otherwise}\end{cases}\qquad \beta_{g,B}=1-\beta_{g,A}",
        "It is the simplest way to say that politics matters.",
        "All or nothing: a group is never split, even when both finalists are almost equally close.",
    )
    _hypothesis(
        "H1-soft",
        "Proximity",
        [
            ("proximity", "Proximity"),
            ("fixed", "No parameter"),
            ("added", "Added after first results"),
        ],
        "Each group splits between the finalists; the nearer one gets more.",
        "A softer version of H1: if a candidate is twice as close to A as to B, A gets two "
        "thirds of the group and B one third. Nobody abstains or votes blank.",
        r"\beta_{g,A} = \frac{d(c,B)}{d(c,A)+d(c,B)},\qquad \beta_{g,B} = \frac{d(c,A)}{d(c,A)+d(c,B)}",
        "It answers the criticism that H1 is too extreme, without adding any parameter.",
        "Added after the first results were known (21 November), so it is not a pre-planned test.",
    )
    _hypothesis(
        "H2-abst",
        "Proximity",
        [("proximity", "Proximity"), ("fixed", "No parameter")],
        "Like H1, unless the candidate is far from both finalists: then the group abstains.",
        "A left-wing voter facing a centre and a far-right finalist may simply stay home. "
        "“Far” means at least one third of the scale from <b>both</b> finalists. H2-blank is "
        "the same rule with a blank ballot instead of abstention; both are always reported.",
        r"\beta_{g,\cdot}=\begin{cases}(0,0,0,1) & d(c,A)\ge\tfrac13\ \text{and}\ d(c,B)\ge\tfrac13\\ \text{H1 row} & \text{otherwise}\end{cases}",
        "It tests the idea that ideological distance can push people out of the vote.",
        "A threshold decides between all and none. The value ⅓ was fixed before any result (two "
        "steps out of six on our first 1–7 scale) and never tuned.",
    )
    with st.expander("H2-blank · same rule, blank ballot instead of abstention"):
        st.latex(
            r"\beta_{g,\cdot}=(0,0,1,0)\ \text{ if } d(c,A)\ge\tfrac13 \text{ and } d(c,B)\ge\tfrac13,\ \text{else the H1 row}"
        )
        c = data.comparison()
        st.markdown(
            f"Average error: **{c.loc['H2-blank', 'mean']:.1f} pp** (H2-abst: "
            f"{c.loc['H2-abst', 'mean']:.1f} pp). We did not choose between the two variants "
            "by looking at the results."
        )
    ui.box(
        "note",
        "<p>Candidates the institutes could not place (Cheminade 2012 and 2017, Lassalle 2017) "
        "follow the <b>H0b row</b> in every proximity rule: a missing position is never read as "
        "“centre” and no vote is dropped.</p>",
        label="Unplaced candidates",
    )


def _mixture() -> None:
    ui.section(PAGE, "s3-4")
    _hypothesis(
        "H3(H1)",
        "Mixture",
        [("mixture", "Mixture"), ("added", "1 fitted parameter")],
        "A share p of each eliminated group behaves like H0b; the rest follows a proximity rule.",
        "Real voters are not all ideological. H3 says: a fraction <i>p</i> of them ignores "
        "the left–right scale and behaves like H0b, the others follow H1 (or H2-abst, H2-blank). "
        "<i>p</i> = 0 is the pure proximity rule, <i>p</i> = 1 is pure H0b.",
        r"\beta^{\text{H3}} = (1-p)\,\beta^{\text{base}} + p\,\beta^{\text{H0b}},\qquad p\in[0,1]",
        "It is the only rule with a number estimated from data, and the smallest possible "
        "step beyond parameter-free rules.",
        "With five elections, <i>p</i> is estimated on four and tested on the fifth. Five "
        "folds describe how a rule transfers between elections; they support no significance test.",
    )
    st.markdown("**Fitting $p$ without looking at the test election** (leave-one-election-out):")
    st.latex(
        r"\hat p_{e^\ast} = \arg\min_{p\in\{0,0.01,\dots,1\}}\ \frac14\sum_{e\neq e^\ast}\text{score}_e(p)"
    )
    st.markdown(
        "The score reported for election $e^\\ast$ always uses $\\hat p_{e^\\ast}$, fitted without it."
    )


# ---- 3.5 -------------------------------------------------------------------------------


def _flows() -> None:
    ui.section(PAGE, "s3-5")
    st.markdown(
        "Pick an election and an assumption. The ribbons show where the rule sends each "
        "first-round group (share of registered voters, all covered areas). Eliminated "
        "candidates are ordered from left to right. Dashed outlines on the right are what "
        "really happened. Hover a ribbon for its size."
    )
    year = st.segmented_control("Election", data.YEARS, default=2022, key="flow_year") or 2022
    model = st.segmented_control("Assumption", data.MODELS, default="H1", key="flow_model") or "H1"
    ui.flow_diagram(year, model, key=f"{year}-{model}")
    comp = data.comparison()
    sc = comp.loc[model, str(year)]
    best = comp[str(year)].idxmin()
    ui.caption(
        f"Figure 3.1 ({model}, {year})",
        f"{data.ONE_LINE[model]} Average error per area for this election: <b>{sc:.1f} pp</b> "
        f"(best this year: {best}, {comp.loc[best, str(year)]:.1f} pp). Pale ribbons are the "
        "four groups that never move. This shows what a rule <i>assumes</i>, not an observed "
        "transfer."
        + (
            f" H3 uses p = {data.fold_p(model[3:-1], year):.2f}, fitted without {year}."
            if model.startswith("H3")
            else ""
        ),
    )
    with st.expander("One group, nine destinations"):
        _one_group(year)


def _one_group(year: int) -> None:
    group = _example_group(year)
    rows = []
    for model in data.MODELS:
        row = _row(model, year)
        for role in data.OUTCOMES:
            rows.append(
                {"model": model, "outcome": data.outcome_label(year, role), "share": row[role]}
            )
    frame = pd.DataFrame(rows)
    order = [data.outcome_label(year, r) for r in data.OUTCOMES]
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
        .transform_calculate(order=f"indexof({order}, datum.outcome)")
    )
    st.altair_chart(chart.properties(height=330), width="stretch")
    s = data.scores(year)
    a, b = (s[f] for f in data.election(year).finalists)
    ui.caption(
        f"Figure 3.2 ({year})",
        f"The largest eliminated group, {data.name(year, group)} "
        f"({data.pooled_first(year)[group] * 100:.1f}% of registered voters, position "
        f"{s[group]:.2f}; finalists at {a:.2f} and {b:.2f}), under each assumption.",
    )


# ---- 3.6-3.7 -------------------------------------------------------------------------


def _p_playground() -> None:
    ui.section(PAGE, "s3-6")
    st.markdown(
        "Slide $p$ from 0 (pure proximity rule) to 1 (pure H0b) and watch the error of each "
        "election. Diamonds mark the value fitted with that election held out."
    )
    c1, c2 = st.columns([1, 2])
    base = c1.radio("Proximity rule mixed with H0b", ["H1", "H2-abst", "H2-blank"], key="p_base")
    p = c2.slider("Share p that behaves like H0b", 0.0, 1.0, 0.25, 0.01, key="p_value")
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
            color=alt.Color("year:N", title="Election", scale=alt.Scale(scheme="tableau10")),
        )
    )
    fitted = (
        alt.Chart(marks)
        .mark_point(shape="diamond", size=120, filled=True)
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
    ui.caption(
        "Figure 3.3",
        f"Error of H3({base}) as p changes, per election. At p = {p:.2f} the five-election mean "
        f"is <b>{now.score.mean():.2f} pp</b>.",
    )
    ui.box(
        "result",
        "<ul><li>On the H2 bases the fitted <i>p</i> is 0.77–1.00: the fit almost throws the H2 "
        "rule away.</li><li>On H1, <i>p</i> is 0.15–0.34, except 0.83 when 2002 is held out: "
        "without 2002, proximity looks much less useful.</li></ul>",
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


def _own_rule() -> None:
    ui.section(PAGE, "s3-7")
    st.markdown(
        "Decide what eliminated voters do, in four parts. The site applies your rule to every "
        "area of every election and scores it exactly like ours:"
    )
    st.latex(
        r"\beta^{\text{yours}} = w_1\,\beta^{\text{H1}} + w_2\,\beta^{\text{H0b}} + w_3\,\beta^{\text{abstain}} + w_4\,\beta^{\text{blank}},\qquad \textstyle\sum w_i = 1"
    )
    cols = st.columns(4)
    raw = {
        "nearest": cols[0].slider("Nearest finalist", 0, 100, 40, 5, key="mix_near"),
        "proportional": cols[1].slider("Split like voters (H0b)", 0, 100, 50, 5, key="mix_prop"),
        "abstain": cols[2].slider("Abstain", 0, 100, 5, 5, key="mix_abst"),
        "blank": cols[3].slider("Vote blank", 0, 100, 5, 5, key="mix_blank"),
    }
    total = sum(raw.values()) or 1
    mixture = {k: v / total for k, v in raw.items()}
    ui.html(
        "<p class='caption'>Normalised: "
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
        "Table 3.1",
        "Error in pp per election (lower is closer). Highlighted: lowest in each column.",
    )
    ui.box(
        "limit",
        "<p>Tuning these sliders while looking at the scores is exactly what we refused to do "
        "with our own rules. A rule chosen this way fits these five elections and tells you "
        "little about the next one. For example, sending a few percent to the blank ballot "
        "helps in 2017 and 2022 only because every rule under-predicts blank ballots there "
        "(Results, 4.3).</p>",
        label="Why we did not do this",
    )
