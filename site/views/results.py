"""4. Results: which assumption is closest, where each misses, and how robust the answer is."""

import altair as alt
import streamlit as st

import data
import ui

PAGE = "results"
TIE = 0.3  # pp: differences this small are not read as a ranking


def render() -> None:
    c = data.comparison()
    years = [str(y) for y in data.YEARS]
    ui.header(
        "Section 4 · Results",
        "No assumption explains every election best",
        "Observations first, interpretation last. Every score is the weighted average, over "
        "areas, of the gap between predicted and observed shares of registered voters.",
    )

    # 4.1 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-1")
    table = c[years + ["mean", "mean_without_2002"]].rename(
        columns={"mean": "Mean", "mean_without_2002": "Mean w/o 2002"}
    )
    ui.score_table(
        table, [*years, "Mean", "Mean w/o 2002"], tie_margin=TIE, rows_after_sep=("H1", "H3(H1)")
    )
    ui.caption(
        "Table 4.1",
        "Average error per area in percentage points (pp); lower is closer. <b>Highlighted</b>: "
        f"lowest of the column. <b style='color:{ui.MUTED}'>Grey bold</b>: within {TIE} pp of "
        "the lowest, which we read as a tie. H3 is always scored on an election it was not "
        "fitted on.",
    )
    frame = c[years].reset_index().melt(id_vars="model", var_name="year", value_name="score")
    frame["family"] = frame.model.map(data.FAMILY)
    dots = (
        alt.Chart(frame)
        .mark_circle(size=95, opacity=0.9)
        .encode(
            x=alt.X("score:Q", title="Average error per area (pp), lower is closer"),
            y=alt.Y("year:N", title=None, sort=years[::-1]),
            color=alt.Color(
                "family:N",
                scale=alt.Scale(
                    domain=list(ui.FAMILY_COLOUR), range=list(ui.FAMILY_COLOUR.values())
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=["model", "year", alt.Tooltip("score:Q", format=".1f")],
        )
    )
    focus = (
        alt.Chart(frame[frame.model.isin(["H0b", "H1"])])
        .mark_text(dy=-13, fontSize=11, fontWeight=600)
        .encode(x="score:Q", y=alt.Y("year:N", sort=years[::-1]), text="model:N")
    )
    st.altair_chart((dots + focus).properties(height=280), width="stretch")
    ui.caption(
        "Figure 4.1",
        "Each dot is one assumption in one election; H0b and H1 are labelled. 2002 stands apart.",
    )
    with st.expander("Why we do not read small gaps as a ranking"):
        st.markdown(
            "- Nine rules are compared on five elections, so the “best” one is partly a "
            "**selection effect**: with many contenders, one wins by chance.\n"
            "- All rules share an **error floor** (groups that never move), which compresses "
            "the differences.\n"
            "- We have no sampling error to compute (the data is a census), but we do have "
            "**modelling** uncertainty, which no formula measures. A margin of 0.3 pp is a "
            "conservative reading, not a statistical test."
        )

    # 4.2 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-2")
    h1_wins = [y for y in years if c.loc["H1", y] < c.loc["H0b", y]]
    ui.finding(
        1,
        "The original baseline fails on abstention.",
        "H0a predicts more abstention than observed in all five elections (Figure 4.2). Removing "
        f"that single channel (H0b) lowers the error in all five: {c.loc['H0b', 'mean']:.1f} pp "
        f"against {c.loc['H0a', 'mean']:.1f} pp on average.",
    )
    ui.finding(
        2,
        "H1 has the lowest average, mostly thanks to 2002.",
        f"H1 averages {c.loc['H1', 'mean']:.1f} pp, ahead of H0b ({c.loc['H0b', 'mean']:.1f}). It "
        f"beats H0b only in {' and '.join(h1_wins)}. In 2002 it scores {c.loc['H1', '2002']:.1f} pp "
        f"against {c.loc['H0b', '2002']:.1f}; without 2002 it ranks {int(c.loc['H1', 'rank_without_2002'])} of 9.",
    )
    ui.finding(
        3,
        "Without 2002, H0b and the H2 mixtures are tied at the top.",
        f"H0b {c.loc['H0b', 'mean_without_2002']:.2f} pp, H3(H2-abst) {c.loc['H3(H2-abst)', 'mean_without_2002']:.2f}, "
        f"H3(H2-blank) {c.loc['H3(H2-blank)', 'mean_without_2002']:.2f}. These mixtures are almost pure H0b "
        "(fitted p close to 1).",
    )
    ui.finding(
        4,
        "Splitting by distance trades 2002 for the other elections.",
        f"H1-soft beats H1 outside 2002 (e.g. {c.loc['H1-soft', '2012']:.1f} against {c.loc['H1', '2012']:.1f} pp "
        f"in 2012) but is much worse in 2002 ({c.loc['H1-soft', '2002']:.1f} against {c.loc['H1', '2002']:.1f}).",
    )
    ui.box(
        "limit",
        "<p>Setting 2002 aside is a check we chose <b>after</b> seeing the results. It is a "
        "diagnostic of how much one election drives the ranking, not a pre-registered test.</p>",
    )

    # 4.3 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-3")
    st.markdown(
        "The score does not say whether a rule predicts too much or too little. Each bar below "
        "is **predicted minus observed**, pooled over the covered areas: above zero, the rule "
        "predicts too much of that outcome."
    )
    signed = data.csv("signed_errors.csv")
    signed = signed[signed.variant.isin(["default", "positions=polls;tie=split"])]
    picked = st.multiselect(
        "Assumptions", data.MODELS, default=["H0a", "H0b", "H1"], key="signed_models"
    )
    signed = signed[signed.model.isin(picked)].copy()
    signed["Outcome"] = signed.role.map(data.OUTCOME_LABEL)
    chart = (
        alt.Chart(signed)
        .mark_bar()
        .encode(
            x=alt.X("year:N", title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Outcome:N", sort=list(data.OUTCOME_LABEL.values())),
            y=alt.Y("signed_error_pp:Q", title="Predicted − observed (pp)"),
            color=alt.Color(
                "Outcome:N",
                scale=ui.outcome_scale(),
                title=None,
                sort=list(data.OUTCOME_LABEL.values()),
            ),
            tooltip=[
                "model",
                "year",
                "Outcome",
                alt.Tooltip("signed_error_pp:Q", format="+.1f", title="pp"),
            ],
        )
        .properties(height=170, width=640)
        .facet(row=alt.Row("model:N", title=None, sort=list(data.MODELS)))
    )
    st.altair_chart(chart, width="content")
    a = data.csv("signed_errors.csv")
    a = a[(a.model == "H0a") & (a.role == "abstention")].signed_error_pp
    ui.caption(
        "Figure 4.2",
        f"Finalist A came first in round 1. H0a over-predicts abstention by {a.min():.1f} to {a.max():.1f} pp.",
    )
    ui.box(
        "result",
        "<ul><li><b>H0a</b>: the abstention bar dominates every year.</li>"
        "<li><b>2002</b>: H0a and H0b both badly under-predict Chirac. In reality, almost the "
        "whole left voted for him against Le Pen.</li>"
        "<li><b>Blank or invalid</b> is under-predicted by every rule in 2017 and 2022, "
        "H2-blank included.</li></ul>",
        label="What to look at",
    )
    with st.expander("A possible reading of the blank-ballot gap"):
        st.markdown(
            "Blank ballots rose from about 1.4% to 6.4% of registered voters between the rounds "
            "of 2017. Our rules can only produce blank ballots from **eliminated** groups. If "
            "some voters of the finalists or some first-round abstainers cast a blank ballot in "
            "round 2, no rule can capture it. This is an interpretation: totals cannot show it."
        )

    # 4.4 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-4")
    thr = data.csv("h2_threshold.csv")
    thr["label"] = thr.apply(
        lambda r: (
            f"{int(r.year)} · finalists at {r.finalist_a_score:.2f} and {r.finalist_b_score:.2f}"
        ),
        axis=1,
    )
    bars = (
        alt.Chart(thr)
        .mark_bar(color=ui.COLOUR["abstention"], height=22)
        .encode(
            y=alt.Y(
                "label:N", title=None, sort=None, axis=alt.Axis(labelLimit=320, labelFontSize=12)
            ),
            x=alt.X(
                "beyond_threshold_pct:Q", title="Registered voters sent to a non-vote by H2 (%)"
            ),
            tooltip=[alt.Tooltip("beyond_threshold_pct:Q", format=".1f")],
        )
    )
    text = bars.mark_text(align="left", dx=4, fontSize=12, color=ui.INK).encode(
        text=alt.Text("beyond_threshold_pct:Q", format=".1f")
    )
    st.altair_chart((bars + text).properties(height=200), width="stretch")
    others = thr[thr.year != 2002].beyond_threshold_pct.max()
    ui.caption(
        "Figure 4.3",
        f"Only 2002 is really affected: {thr.loc[thr.year == 2002, 'beyond_threshold_pct'].iloc[0]:.1f}% "
        f"of registered voters, against at most {others:.1f}% in any other election.",
    )
    ui.box(
        "result",
        "<p>In 2002 both finalists sit on the right of the scale (0.80 and 0.93), so the whole "
        "left is at least one third away from both. H2 sends it to a non-vote, while in reality "
        "it voted for Chirac. Elsewhere, H2 barely acts and scores close to H1. <b>The threshold "
        "is really tested in one election only</b>, so we do not claim it helps.</p>",
    )

    # 4.5 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-5")
    st.markdown(
        "The main results use the poll-based scale. We reran every rule with our first "
        "hand-coded 1–7 scale and with its alternative families."
    )
    sens = data.csv("sensitivity.csv")
    sens = (
        sens[sens.tie == "split"]
        .pivot(index="model", columns="positions", values="mean")
        .loc[list(data.MODELS)]
    )
    sens = sens.rename(
        columns={
            "polls": "Poll-based (main)",
            "primary": "Hand-coded 1–7",
            "alternative": "Hand-coded, alternative",
        }
    )
    cols = ["Poll-based (main)", "Hand-coded 1–7", "Hand-coded, alternative"]
    ui.score_table(sens[cols], cols, tie_margin=TIE)
    best_alt = sens["Hand-coded, alternative"].idxmin()
    ui.caption(
        "Table 4.2",
        "Five-election mean error (pp) under three ways of placing the candidates. H0a and H0b read no positions.",
    )
    c1, c2 = st.columns(2)
    with c1:
        ui.box(
            "result",
            "<ul><li>The five-election leader always uses candidate positions, and its lead comes from 2002.</li>"
            "<li>Without 2002, the lead goes to H0b or to a mixture that is almost H0b.</li></ul>",
            label="What holds",
        )
    with c2:
        ui.box(
            "limit",
            f"<ul><li>The exact name at the top: H1 on two scales, <b>{best_alt}</b> on the third.</li>"
            "<li>H2 depends strongly on where candidates are placed (much worse on the 1–7 scale).</li></ul>",
            label="What does not hold",
        )
    with st.expander("Does the tie rule matter?"):
        st.markdown(
            "Two candidates are exactly halfway between the finalists on the poll-based scale "
            "(Boutin 2002, Nihous 2007). Sending them to abstention instead of splitting them "
            "50/50 moves no mean by more than **0.1 pp**."
        )

    # 4.6 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-6")
    st.markdown(
        "From 2017 the Ministry separates blank and invalid ballots. For 2017 and 2022 we "
        "scored every rule on **five** outcomes (blank and invalid apart), keeping invalid "
        "ballots fixed at their first-round level, as the second peer review suggested."
    )
    blank = data.csv("blank_only.csv")
    blank = blank.pivot(
        index="model", columns="year", values=["rank_4_outcomes", "rank_5_outcomes"]
    ).loc[list(data.MODELS)]
    blank.columns = [
        f"{'4' if a == 'rank_4_outcomes' else '5'} outcomes, {y}" for a, y in blank.columns
    ]
    blank = blank[sorted(blank.columns, key=lambda c: (c[-4:], c[0]))].astype(int)
    st.dataframe(blank, width="stretch")
    ui.caption(
        "Table 4.3",
        "Rank of each rule (1 = closest) with blank and invalid merged (4 outcomes) and apart (5 outcomes).",
    )
    ui.box(
        "result",
        "<p>The order of the rules is <b>unchanged</b> in both elections: merging blank and invalid "
        "ballots does not drive our conclusions.</p>",
    )

    # 4.7 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-7")
    terr = data.csv("territory_scores.csv")
    t22 = terr[(terr.year == 2022) & terr.model.isin(["H0b", "H1", "H1-soft"])]
    chart = (
        alt.Chart(t22)
        .mark_bar(height=16)
        .encode(
            y=alt.Y("model:N", title=None),
            x=alt.X("score_pp:Q", title="Error in 2022 (pp)"),
            color=alt.Color(
                "model:N", legend=None, scale=alt.Scale(range=[ui.MUTED, ui.ACCENT, "#5FA3A8"])
            ),
            row=alt.Row("territory:N", title=None, sort=["metropolitan", "overseas", "abroad"]),
            tooltip=["territory", "model", alt.Tooltip("score_pp:Q", format=".1f")],
        )
        .properties(height=70, width=600)
    )
    st.altair_chart(chart, width="content")
    ui.caption("Figure 4.4", "2022. Proximity rules do much worse overseas, where H0b holds up.")
    ui.box(
        "limit",
        "<p>A left–right scale built from national polls may describe overseas electorates "
        "poorly. This is a hypothesis, not something we tested.</p>",
    )

    # 4.8 ------------------------------------------------------------------------------
    ui.section(PAGE, "s4-8")
    st.markdown("These readings go beyond the numbers and carry the limits of Section 7.")
    with st.expander(
        "1 · Most of the original baseline's error came from one modelling choice", expanded=True
    ):
        st.markdown(
            "Sending eliminated voters to abstention, not voters being unpredictable. The "
            "baseline to beat is H0b: *people who voted once vote again, in proportion to the "
            "finalists' first-round strength*."
        )
    with st.expander("2 · We cannot name one best assumption"):
        st.markdown(
            "Ideological proximity describes 2002 far better than anything else, plausibly "
            "because that runoff opposed the right and the far right and almost every other "
            "voter ended on the same side. In the four other elections, H0b does as well or "
            "better. Five elections cannot separate a general rule from one exceptional election."
        )
    with st.expander("3 · An all-or-nothing threshold is fragile"):
        st.markdown(
            "H2 fails where both finalists are on one side of the scale; elsewhere it barely acts."
        )
    with st.expander("4 · An inconclusive answer is still a result"):
        st.markdown(
            "It tells us which simple stories about vote transfers the totals can and cannot "
            "tell apart, and which single modelling choice (abstention) matters most."
        )
