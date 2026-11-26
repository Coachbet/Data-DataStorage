"""Results: which assumption is closest, where each misses, and how robust the answer is."""

import altair as alt
import streamlit as st

import data
import ui

TIE = 0.3  # pp: differences this small are not read as a ranking


def render() -> None:
    c = data.comparison()
    years = [str(y) for y in data.YEARS]
    ui.header(
        "Section 4 · Results",
        "No assumption explains every election best",
        "Observations first, interpretation after. Every number is the weighted average, "
        "over areas, of the gap between predicted and observed shares of registered voters.",
    )

    st.markdown("## 4.1 How close is each assumption?")
    table = c[years + ["mean", "mean_without_2002"]].rename(
        columns={"mean": "Mean", "mean_without_2002": "Mean w/o 2002"}
    )
    ui.score_table(
        table, [*years, "Mean", "Mean w/o 2002"], tie_margin=TIE, rows_after_sep=("H1", "H3(H1)")
    )
    ui.caption(
        "Table 5",
        "Average error per area, in percentage points (pp); lower is closer. <b>Bold</b>: "
        f"lowest of the column. <b style='color:{ui.MUTED}'>Grey bold</b>: within {TIE} pp of "
        "the lowest. We read those as ties, not as a ranking: with five elections and nine "
        "rules, gaps that small can come from the choice of rules as much as from voters. H3 "
        "is always scored on an election it was not fitted on.",
    )
    frame = c[years].reset_index().melt(id_vars="model", var_name="year", value_name="score")
    frame["family"] = frame.model.map(data.FAMILY)
    dots = (
        alt.Chart(frame)
        .mark_circle(size=90, opacity=0.9)
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
    ui.caption("Figure 6", "Each dot is one assumption in one election. H0b and H1 are labelled.")

    h1_wins = [y for y in years if c.loc["H1", y] < c.loc["H0b", y]]
    st.markdown("### Observations")
    ui.finding(
        1,
        "The original baseline fails on abstention.",
        "H0a predicts more abstention than observed in all five elections (Figure 7). "
        f"Removing that single channel (H0b) lowers the error in all five: "
        f"{c.loc['H0b', 'mean']:.1f} pp against {c.loc['H0a', 'mean']:.1f} pp on average.",
    )
    ui.finding(
        2,
        "H1 has the lowest average, mostly thanks to 2002.",
        f"H1 averages {c.loc['H1', 'mean']:.1f} pp over five elections, ahead of H0b "
        f"({c.loc['H0b', 'mean']:.1f}). It beats H0b only in {' and '.join(h1_wins)}. In 2002 "
        f"it scores {c.loc['H1', '2002']:.1f} pp against {c.loc['H0b', '2002']:.1f}; without "
        f"2002 it ranks {int(c.loc['H1', 'rank_without_2002'])} of 9.",
    )
    ui.finding(
        3,
        "Without 2002, H0b and the H3 mixtures are tied at the top.",
        f"H0b {c.loc['H0b', 'mean_without_2002']:.2f} pp, H3(H2-abst) "
        f"{c.loc['H3(H2-abst)', 'mean_without_2002']:.2f}, H3(H2-blank) "
        f"{c.loc['H3(H2-blank)', 'mean_without_2002']:.2f}: these mixtures are almost "
        "pure H0b (fitted p close to 1). Setting 2002 aside is a check we chose after "
        "seeing the results.",
    )
    ui.finding(
        4,
        "Splitting by distance trades 2002 for the other elections.",
        f"H1-soft is closer than H1 outside 2002 (e.g. {c.loc['H1-soft', '2012']:.1f} against "
        f"{c.loc['H1', '2012']:.1f} pp in 2012) but much worse in 2002 "
        f"({c.loc['H1-soft', '2002']:.1f} against {c.loc['H1', '2002']:.1f}).",
    )

    st.markdown("## 4.2 Where each assumption misses")
    st.markdown(
        "The error score does not say whether a rule predicts too much or too little. Here each "
        "bar is *predicted minus observed*, pooled over the covered areas: above zero, the "
        "rule predicts too much of that outcome."
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
    a = signed[(signed.model == "H0a") & (signed.role == "abstention")].signed_error_pp
    ui.caption(
        "Figure 7",
        "Finalist A is the candidate who came first in round 1."
        + (f" H0a over-predicts abstention by {a.min():.1f} to {a.max():.1f} pp." if len(a) else "")
        + " Blank or invalid ballots are under-predicted by every rule in 2017 and 2022, "
        "H2-blank included. This is consistent with voters of the finalists or abstainers "
        "casting a blank ballot in round 2, a move no rule allows (an interpretation, not "
        "something the totals can show).",
    )

    st.markdown("## 4.3 The distance threshold is really tested only once")
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
        "Figure 8",
        f"Only 2002 is really affected: {thr.loc[thr.year == 2002, 'beyond_threshold_pct'].iloc[0]:.1f}% "
        f"of registered voters, against at most {others:.1f}% in any other election. In 2002 both "
        "finalists sit on the right of the scale, so the whole left is at least one third away "
        "from both and H2 sends it to a non-vote, while in reality it voted for Chirac. The "
        "threshold (⅓) was fixed before any result and never tuned.",
    )

    st.markdown("## 4.4 Does the answer depend on how candidates are placed?")
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
        "Table 6",
        "Five-election mean error (pp) of each assumption under three ways of placing the "
        f"candidates. H1 is lowest on the poll-based and the hand-coded scales; with the "
        f"alternative families the lowest is <b>{best_alt}</b> and H1 comes second. H0a and H0b "
        "read no positions, so their scores never change. The alternative coding changes all "
        "listed candidates at once: it is one other scenario, not a test of each candidate.",
    )
    st.markdown(
        "**What holds on every scale:** the five-election leader is a rule that uses candidate "
        "positions, its lead comes from *2002*, and without 2002 the lead goes to H0b or to a mixture that is almost H0b. "
        "**What does not hold:** the exact name at the top. We therefore do not claim that H1 "
        "is the best assumption."
    )

    st.markdown("## 4.5 Metropolitan France and overseas")
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
    ui.caption(
        "Figure 9",
        "Proximity rules do much worse overseas, where H0b holds up. A left-right scale built "
        "from national polls may describe overseas electorates poorly: this is a hypothesis, "
        "not something we tested.",
    )

    st.markdown("## 4.6 Interpretation")
    st.markdown(
        "These readings go beyond the numbers and carry the limits listed on the *Method* page.\n\n"
        "1. **Most of the original baseline's error came from one modelling choice**, sending "
        "eliminated voters to abstention, not from voters being unpredictable. The baseline to "
        "beat is H0b: *people who voted once vote again, in proportion to the finalists' "
        "first-round strength*.\n"
        "2. **We cannot name one best assumption.** Ideological proximity describes 2002 far "
        "better than anything else, plausibly because that runoff opposed the right and the "
        "far right and almost every other voter ended on the same side. In the four other "
        "elections, H0b does as well or better. Five elections cannot separate a general rule "
        "from one exceptional election.\n"
        "3. **An all-or-nothing threshold is fragile.** H2 fails where the finalists are both "
        "on one side of the scale; elsewhere it barely acts.\n"
        "4. **The honest answer is inconclusive, and that is a result**: it tells us which "
        "simple stories about vote transfers the totals can and cannot tell apart."
    )
