"""1. Introduction: the problem, why it is hard, our approach and the answer."""

import altair as alt
import pandas as pd
import streamlit as st

import data
import ui

PAGE = "intro"


def render() -> None:
    c = data.comparison()
    h1_wins = int(sum(c.loc["H1", str(y)] < c.loc["H0b", str(y)] for y in data.YEARS))
    shares = [
        float(data.pooled_first(y)[list(data.election(y).eliminated)].sum() * 100)
        for y in data.YEARS
    ]
    lo, hi = min(shares), max(shares)

    ui.header(
        "Research project · Data, Data Storage, Data Collection",
        "Where do the voters of eliminated candidates go?",
        "Testing nine assumptions about second-round vote transfers in French presidential "
        "elections, 2002–2022<br>" + " · ".join(data.TEAM),
    )
    ui.html(
        '<div class="abstract">'
        '<p><b class="label">Abstract.</b> In a French presidential election, voters whose '
        "candidate is eliminated in the first round must choose again: one of the two "
        "finalists, a blank or invalid ballot, or staying at home. The vote is secret, so these "
        "moves are never observed. We write nine simple assumptions about them as precise "
        "rules, predict the second round of every area from its first round, and compare each "
        "prediction with the official result, for the five elections from 2002 to 2022 "
        "(522 area-elections built from 673,228 polling-station records). "
        "<b>No single assumption wins.</b> Sending each group to the ideologically nearest "
        f"finalist (H1) has the lowest five-election error ({c.loc['H1', 'mean']:.1f} "
        "percentage points), but almost all of its lead comes from 2002; it beats a simple "
        f"proportional baseline (H0b) in only {h1_wins} of 5 elections. Without 2002, H0b is "
        f"best ({c.loc['H0b', 'mean_without_2002']:.1f} pp). The clearest lesson is about "
        "abstention: our original baseline was wrong mainly because it let eliminated voters "
        "abstain like everyone else.</p></div>"
    )
    ui.stats(
        [
            ("5", "presidential elections, 2002–2022"),
            ("522", "area-elections (départements, overseas, abroad)"),
            ("9", "assumptions tested, 1 fitted parameter"),
            ("22", "polls collected by hand for candidate positions"),
        ]
    )

    ui.section(PAGE, "s1-1")
    st.markdown(
        "Only two candidates reach the second round. Everyone who voted for one of the "
        f"others — **{lo:.0f} to {hi:.0f}% of registered voters**, depending on the year — has "
        "to decide again. On election night, commentators talk about *reports de voix* (vote "
        "transfers): how many of the left's voters will go to the centre, how many will stay "
        "home. Nobody can actually see these moves."
    )
    ui.html(
        '<div class="question">Which assumptions about voter behaviour best explain '
        "second-round results in French presidential elections (2002–2022)?</div>"
    )
    st.markdown(
        "We do not try to *measure* transfers. We ask a more modest question that the data can "
        "answer: **which simple story about transfers reproduces the official results best?**"
    )

    ui.section(PAGE, "s1-2")
    st.markdown(
        "Official results only give **totals per area**. Many different individual behaviours "
        "lead to the same totals. Here is a toy area with 100 registered voters:"
    )
    left, right = st.columns(2)
    rows = (
        "<tr><td>Round 1</td><td>A 40 · B 30 · C 20 · abstain 10</td></tr>"
        "<tr><td>Round 2</td><td>A 50 · B 40 · abstain 10</td></tr>"
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
    ui.box(
        "definition",
        "<p><b>Ecological inference</b>: inferring individual behaviour from group totals. Both "
        "stories above give exactly the same official result, so no method can tell them apart "
        "from totals alone. Every result on this site is therefore a statement about "
        "<b>patterns in totals</b>, never about what any person did.</p>",
    )
    with st.expander("Why not use surveys instead?"):
        st.markdown(
            "- Post-election surveys ask people how they voted in both rounds, but they are "
            "small, self-reported and not available in the same form for all five elections.\n"
            "- Our first plan used one preference survey (*Voter Autrement*, 2017) for two extra "
            "hypotheses (H4, H5). The first peer review pointed out that one 2017 volunteer "
            "survey cannot describe five elections, so we dropped it.\n"
            "- Official results are a **census** of registered voters: no sampling error, the "
            "same source every year, and fully reproducible."
        )

    ui.section(PAGE, "s1-3")
    st.markdown("Our approach rests on three ideas:")
    st.markdown(
        "1. **Turn each assumption into a rule.** A rule says, for every first-round group, "
        "which share goes to each second-round option. It can be written as a table.\n"
        "2. **Predict, then compare.** Apply the rule to the first round of each area, get a "
        "predicted second round, and measure the gap with the real one.\n"
        "3. **Keep rules simple and fixed in advance.** Eight of nine rules have no parameter "
        "at all; the ninth has one, always tested on an election it was not fitted on."
    )
    st.latex(
        r"\underbrace{x_{a}}_{\text{round 1 of area }a}\;\xrightarrow{\;\beta\text{ (the rule)}\;}"
        r"\;\underbrace{\hat s_{a}}_{\text{predicted round 2}}\;\longleftrightarrow\;"
        r"\underbrace{s_{a}}_{\text{observed round 2}}"
    )
    steps = [
        ("Collect", "Ministry files 2002–2022, pinned by hash; 22 poll orders collected by hand"),
        ("Clean", "Zero-tolerance checks; nothing removed, imputed or corrected"),
        ("Store", "Normalised Parquet tables, compared with SQLite and DuckDB"),
        ("Analyse", "9 rules as transfer tables, one error score, held-out validation"),
        ("Communicate", "This site, the report and the slides read the same numbers"),
    ]
    ui.html(
        '<div class="pipeline">'
        + "".join(
            f'<div><div class="t">{i}. {t}</div><div class="d">{d}</div></div>'
            for i, (t, d) in enumerate(steps, 1)
        )
        + "</div>"
    )

    ui.section(PAGE, "s1-4")
    st.markdown(
        "Average error of each assumption over all five elections (green) and without 2002 "
        "(orange). Lower is better. H1 is first overall, but it barely changes without 2002, "
        "while H0b and the H2 mixtures fall to about 3 pp."
    )
    st.altair_chart(_dumbbell(c), width="stretch")
    ui.caption(
        "Figure 1.1",
        "Weighted mean over areas of the absolute gap between predicted and observed shares of "
        "registered voters (four outcomes), in percentage points. H3 is always scored on an "
        "election it was not fitted on. Excluding 2002 is a check we chose after seeing the "
        "results: read it as a diagnostic, not a pre-registered test.",
    )
    ui.box(
        "result",
        "<ul>"
        f"<li>Lowest five-election error: <b>H1, {c.loc['H1', 'mean']:.1f} pp</b>, but only "
        f"{h1_wins} wins out of 5 against H0b.</li>"
        f"<li>Lowest without 2002: <b>H0b, {c.loc['H0b', 'mean_without_2002']:.1f} pp</b>.</li>"
        "<li>Not sending eliminated voters to abstention removes "
        f"<b>{c.loc['H0a', 'mean'] - c.loc['H0b', 'mean']:.1f} pp</b> of error on average.</li>"
        "</ul>",
    )

    ui.section(PAGE, "s1-5")
    st.markdown("What this project adds, beyond the numbers:")
    st.markdown(
        "- **A fair comparison.** Every assumption is a transfer table scored by the same rule "
        "on the same 522 area-elections.\n"
        "- **Two baselines, not one.** Peer review showed that our first baseline was "
        "unusually weak; we kept it and added a stronger one, so later rules cannot win cheaply.\n"
        "- **Candidate positions from outside the team.** Instead of our own coding, we built "
        "a left–right score from 22 published polls.\n"
        "- **No tuning on the test data.** Rules and thresholds were fixed before results; the "
        "only fitted parameter is validated leave-one-election-out.\n"
        "- **Full reproducibility.** From raw files pinned by hash to every figure on this "
        "site, one command rebuilds everything."
    )


def _dumbbell(c: pd.DataFrame) -> alt.Chart:
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
