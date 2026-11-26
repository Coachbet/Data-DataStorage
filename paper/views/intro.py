"""Introduction: the problem, why it is hard, what we did and the answer in one screen."""

import streamlit as st

import data
import ui


def render() -> None:
    c = data.comparison()
    best_all = c["mean"].idxmin()
    best_wo = c["mean_without_2002"].idxmin()
    h1_wins = int(sum(c.loc["H1", str(y)] < c.loc["H0b", str(y)] for y in data.YEARS))

    ui.header(
        "Data, Data Storage, Data Collection · group project",
        "Where do the voters of eliminated candidates go?",
        " · ".join(data.TEAM),
    )
    ui.html(
        '<div class="abstract">'
        '<p><b class="label">Abstract.</b> In a French presidential election, voters whose '
        "candidate is eliminated in the first round must choose again in the second: one of "
        "the two finalists, a blank or invalid ballot, or staying at home. The vote is secret, "
        "so these moves are never observed. We write nine simple assumptions about them as "
        "precise rules, predict the second round of every area from its first round, and "
        "compare each prediction with the official result, for the five elections from 2002 "
        "to 2022 (522 area-elections, 673,228 polling-station records). "
        f"<b>No single assumption wins.</b> Sending each group to the ideologically nearest "
        f"finalist (H1) has the lowest five-election error ({c.loc['H1', 'mean']:.1f} pp), but "
        f"almost all of its lead comes from 2002; it beats the simple proportional baseline "
        f"H0b in only {h1_wins} of 5 elections. Without 2002, H0b is best "
        f"({c.loc['H0b', 'mean_without_2002']:.1f} pp). The most robust lesson is about "
        f"abstention: the original baseline was wrong mainly because it let eliminated voters "
        "abstain like everyone else.</p></div>"
    )

    shares = [
        float(data.pooled_first(y)[list(data.election(y).eliminated)].sum() * 100)
        for y in data.YEARS
    ]
    lo, hi = min(shares), max(shares)
    st.markdown("## 1. The problem")
    st.markdown(
        "Only two candidates reach the second round. Everyone who voted for one of the "
        f"others ({lo:.0f} to {hi:.0f}% of registered voters, depending on the year) has to "
        "decide again. "
        "Commentators talk about *reports de voix* (vote transfers) every election night, "
        "but nobody can see them: ballots are secret and the official results only give "
        "totals per area."
    )
    ui.html(
        '<div class="question">Which assumptions about voter behaviour best explain '
        "second-round results in French presidential elections (2002–2022)?</div>"
    )

    st.markdown("### Why it is hard: many stories give the same totals")
    st.markdown(
        "Here is a toy area with 100 registered voters. Both stories below produce **exactly "
        "the same** official result, yet they describe opposite behaviours. This is the "
        "*ecological inference* problem, and it is why we test assumptions against totals "
        "instead of claiming to measure individual transfers."
    )
    _toy_example()

    st.markdown("## 2. What we did")
    st.markdown(
        "We turned the question into a reproducible data workflow, from the Ministry's raw "
        "files to the figures on this site. Each step is documented on the *Data* and "
        "*Method & limits* pages."
    )
    _pipeline()
    st.markdown(
        "The core idea fits in one sentence: **an assumption is a rule that says where each "
        "first-round group goes in the second round.** Apply the rule to the first round of "
        "an area, get a predicted second round, measure how far it is from the real one. "
        "The rule with the smallest error explains the results best."
    )
    ui.html(
        '<p class="formula">first round of an area &nbsp;→&nbsp; <i>rule</i> &nbsp;→&nbsp; '
        "predicted second round &nbsp;⟷&nbsp; observed second round &nbsp;=&nbsp; "
        "<b>error in percentage points</b></p>"
    )

    st.markdown("## 3. The answer in one figure")
    st.markdown(
        "Average error of each assumption over the five elections (green) and without 2002 "
        "(orange). Lower is better. Sorted by the five-election mean: H1 is first, but it barely "
        "changes without 2002, while H0b and the H2 mixtures fall to about 3 pp."
    )
    st.altair_chart(_slope(c), width="stretch")
    ui.caption(
        "Figure 1",
        "Weighted mean over areas of the absolute gap between predicted and observed "
        "shares of registered voters (four outcomes), in percentage points. H3 is always "
        "scored on an election it was not fitted on. Excluding 2002 is a check we decided "
        "after seeing the results, so read it as a diagnostic, not a pre-registered test.",
    )
    ui.stats(
        [
            (f"{c.loc[best_all, 'mean']:.1f} pp", f"lowest five-election error: <b>{best_all}</b>"),
            (
                f"{c.loc[best_wo, 'mean_without_2002']:.1f} pp",
                f"lowest without 2002: <b>{best_wo}</b>",
            ),
            (f"{h1_wins} / 5", "elections where H1 beats the H0b baseline"),
            (
                f"{c.loc['H0a', 'mean'] - c.loc['H0b', 'mean']:.1f} pp",
                "error removed by not sending eliminated voters to abstention",
            ),
        ]
    )

    st.markdown("## 4. How to read this site")
    ui.html(
        '<div class="toc">'
        "<p><b>Data</b>: where the numbers come from, how we cleaned and stored them.</p>"
        "<p><b>Hypotheses</b>: each assumption explained with an animated flow, plus a "
        "playground to build your own rule.</p>"
        "<p><b>Results</b>: which assumption is closest, where each one misses, and how "
        "robust the answer is.</p>"
        "<p><b>Explore</b>: the raw election results, area by area.</p>"
        "<p><b>Method & limits</b>: exact definitions, limits and how to reproduce every number.</p>"
        "<p><b>Report</b>: the full written report.</p></div>"
    )


def _toy_example() -> None:
    left, right = st.columns(2)
    rows = (
        "<tr><td>Round 1</td><td>A 40 · B 30 · C 20 · abstain 10</td></tr>"
        "<tr><td>Round 2 (official)</td><td>A 50 · B 40 · abstain 10</td></tr>"
    )
    with left:
        ui.html(
            '<div class="hyp"><h4>Story 1: a clean split</h4>'
            "<p>C's 20 voters split 10 to A and 10 to B. Nobody else moves.</p>"
            f'<table class="paper">{rows}</table></div>'
        )
    with right:
        ui.html(
            '<div class="hyp"><h4>Story 2: a lot of churn</h4>'
            "<p>All 20 C voters go to B, while 10 of B's voters switch to A.</p>"
            f'<table class="paper">{rows}</table></div>'
        )
    ui.caption(
        "Box 1",
        "Same totals, different behaviour. Official results cannot tell the two stories "
        "apart, so every result on this site describes patterns in totals, not what any "
        "person did.",
    )


def _pipeline() -> None:
    steps = [
        (
            "Collect",
            "Ministry polling-station files 2002–2022, pinned by hash; 22 polling-institute left-right orders collected by hand",
        ),
        (
            "Clean",
            "Zero-tolerance checks: a failed check stops the build. Nothing removed, imputed or corrected",
        ),
        ("Store", "Normalised Parquet tables; compared with SQLite/PostgreSQL and DuckDB"),
        (
            "Analyse",
            "9 assumptions as transfer matrices; one error score; H3 validated leave-one-election-out",
        ),
        ("Communicate", "This site, the report and the slides read the same generated numbers"),
    ]
    cells = "".join(
        f'<div style="flex:1;min-width:0;border-top:3px solid {ui.ACCENT};padding:.5rem .4rem 0">'
        f'<div style="font-family:{ui.SERIF};font-weight:600;font-size:1.05rem">{i}. {t}</div>'
        f'<div style="color:{ui.MUTED};font-size:.86rem;line-height:1.4;margin-top:.25rem">{d}</div></div>'
        for i, (t, d) in enumerate(steps, 1)
    )
    ui.html(f'<div style="display:flex;gap:.7rem;margin:1rem 0 1.4rem">{cells}</div>')


def _slope(c):
    """Dumbbell: each assumption's mean error with and without 2002."""
    import altair as alt
    import pandas as pd

    order = list(c.sort_values("mean").index)
    frame = pd.DataFrame(
        [
            {"model": m, "when": w, "score": c.loc[m, col]}
            for m in data.MODELS
            for w, col in (("All five elections", "mean"), ("Without 2002", "mean_without_2002"))
        ]
    )
    y = alt.Y("model:N", sort=order, title=None, axis=alt.Axis(labelFontSize=13, labelColor=ui.INK))
    link = (
        alt.Chart(frame)
        .mark_line(color=ui.RULE, strokeWidth=3)
        .encode(y=y, x="score:Q", detail="model:N")
    )
    dots = (
        alt.Chart(frame)
        .mark_circle(size=130, opacity=1)
        .encode(
            y=y,
            x=alt.X(
                "score:Q",
                title="Average error (pp), lower is closer",
                scale=alt.Scale(domain=[2.5, 9.2]),
            ),
            color=alt.Color(
                "when:N",
                scale=alt.Scale(
                    domain=["All five elections", "Without 2002"], range=[ui.ACCENT, "#C2410C"]
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=["model", "when", alt.Tooltip("score:Q", format=".2f")],
        )
    )
    labels = (
        alt.Chart(frame)
        .mark_text(fontSize=10.5, color=ui.MUTED, baseline="middle")
        .encode(
            y=y,
            x="score:Q",
            text=alt.Text("score:Q", format=".1f"),
            yOffset=alt.YOffset("o:Q", scale=None),
        )
        .transform_calculate(o="datum.when == 'Without 2002' ? 12 : -12")
    )
    return alt.layer(link, dots, labels).properties(height=360)
