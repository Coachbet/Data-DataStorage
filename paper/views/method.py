"""Method & limits: exact definitions, what we cannot claim, how to reproduce."""

import streamlit as st

import data
import ui


def render() -> None:
    ui.header(
        "Section 6 · Method & limits",
        "Exact definitions, honest limits",
        "Everything needed to check, criticise or rerun the study.",
    )

    st.markdown("## 6.1 The error score")
    st.markdown(
        "For area *a* and outcome *k* (finalist A, finalist B, blank or invalid, abstention), "
        "with ŝ the predicted and s the observed share of registered voters:"
    )
    st.latex(
        r"\text{error}_a \;=\; \frac{100}{4}\sum_{k=1}^{4}\bigl|\,\hat s_{a,k}-s_{a,k}\bigr|"
        r"\qquad\text{(percentage points)}"
    )
    st.latex(
        r"\text{score} \;=\; \sum_a w_a\,\text{error}_a,\qquad "
        r"w_a=\frac{\text{registered voters in round 2 of } a}{\text{all registered voters in round 2}}"
    )
    st.markdown(
        "Absolute gaps are taken **before** averaging, so opposite errors in two areas cannot "
        "cancel. The four outcomes count equally. Weighting by registered voters means a large "
        "département counts more than a small overseas territory. A secondary diagnostic, the "
        "*gap in combined results*, first adds all areas up and then compares: there, errors "
        "of opposite sign can cancel."
    )

    st.markdown("## 6.2 The transfer table, formally")
    st.markdown(
        "With x the first-round shares of an area and β the transfer table of an assumption "
        "(rows sum to one), the prediction is"
    )
    st.latex(r"\hat s_{a,k} \;=\; \sum_{g} x_{a,g}\,\beta_{g,k}")
    st.markdown(
        "- **Retained groups never move**: the rows of both finalists, of first-round blank or "
        "invalid voters and of first-round abstainers are the identity in every assumption.\n"
        "- **Unplaced candidates** (Cheminade 2012 and 2017, Lassalle 2017: institutes disagree "
        "or list them last by default) use the H0b row in every proximity rule.\n"
        "- **Ties**: a candidate exactly halfway between the finalists splits 50/50 (2 cases: "
        "Boutin 2002, Nihous 2007). Sending them to abstention instead moves no mean by more "
        "than 0.1 pp.\n"
        "- **H3**: p is chosen on a grid (0, 0.01, …, 1) to minimise the mean score of four "
        "elections, then scored on the fifth. With five folds this describes how a rule "
        "transfers between elections; it supports no significance test."
    )
    folds = data.csv("h3_folds.csv")
    folds = folds[(folds.variant == "positions=polls;tie=split") & folds.test_year.notna()].pivot(
        index="base", columns="test_year", values="p"
    )
    folds.columns = [f"held out {int(c)}" for c in folds.columns]
    st.dataframe(folds.style.format("{:.2f}"), width="stretch")
    ui.caption("Table 7", "Fitted p of H3 for each held-out election and proximity base.")

    st.markdown("## 6.3 Limits")
    limits = [
        (
            "Totals are not individual transfers.",
            "Different individual choices give the same area totals "
            "(Box 1 on the Introduction). A rule that fits is not an observed transfer.",
        ),
        (
            "The unit is the area, not the polling station.",
            "Aggregating ~70,000 stations into ~100 areas "
            "hides variation inside areas and widens the range of behaviours compatible with the totals.",
        ),
        (
            "2002 rests on one poll.",
            "The poll-based positions for 2002 come from a single institute, and "
            "2002 is the election that decides the five-election ranking.",
        ),
        (
            "The scale is an order, not a distance.",
            "Within a poll neighbours are evenly spaced whatever "
            "their real gap; institutes' table conventions enter the scale (in 2007 Voynet sits slightly "
            "right of Royal). One dimension ignores Europe, sovereignty or ecology.",
        ),
        (
            "Retained groups never move.",
            "Real movements of finalists' voters or round-1 abstainers are an "
            "error floor shared by every rule, which compresses the differences between rules.",
        ),
        (
            "Coverage changes.",
            "2002 and 2007 miss voters abroad and some overseas areas; years are not "
            "identical geographic samples.",
        ),
        (
            "Blank and invalid together.",
            "The outcome mixes a deliberate act with mistakes; the split exists "
            "only for 2017 and 2022.",
        ),
        (
            "Few elections, many rules.",
            "Nine rules on five elections: the 'best' is partly a selection "
            "effect, and gaps under ~0.3 pp are read as ties. H0b and H1-soft were added after earlier "
            "results were known.",
        ),
    ]
    for i, (t, d) in enumerate(limits, 1):
        ui.finding(i, t, d)

    st.markdown("## 6.4 Reproduce every number")
    st.markdown(
        f"All code and data: [{data.REPOSITORY.removeprefix('https://')}]({data.REPOSITORY}). "
        "The repository contains the verified cleaned tables, so no download is needed."
    )
    st.code(
        "uv sync --locked --dev            # exact package versions (uv.lock)\n"
        "uv run streamlit run paper/app.py # this site\n"
        "make analysis                     # every result, table and figure from the bundled data\n"
        "make data                         # download the Ministry files again and rebuild everything\n"
        "make check                        # tests, lint, and processed-vs-bundled comparison",
        language="bash",
    )
    live = data.live_scores().pivot(index="model", columns="year", values="score")
    pub = data.comparison()[[str(y) for y in data.YEARS]]
    pub.columns = [int(c) for c in pub.columns]
    gap = float((live.loc[pub.index] - pub).abs().max().max())
    ui.callout(
        f"<b>Live check.</b> This site recomputes every score from the cleaned tables when it "
        f"starts. Largest difference with the published results table: <b>{gap:.1e} pp</b> "
        "(rounding only)."
    )
    st.markdown(
        "What a command cannot reproduce is the extraction of the poll orders from the "
        "institutes' reports. Each of the 22 rows of `data/reference/polling_axes.csv` links to "
        "its source:"
    )
    p = data.polls()[["year", "institute", "fieldwork", "source_url"]]
    st.dataframe(
        p,
        hide_index=True,
        width="stretch",
        column_config={
            "source_url": st.column_config.LinkColumn("Source", display_text="open"),
            "year": st.column_config.NumberColumn("Election", format="%d"),
        },
    )
    st.markdown(
        "Poll orders for 2017 and 2022 are taken from Delemazure, T., Dong, C., Peters, D. and "
        "Tydrichová, M. (2024). *Comparing Ways of Obtaining Candidate Orderings from Approval "
        "Ballots.* arXiv:2405.04525."
    )
    st.markdown(
        "*AI tools assisted with code, tests and drafting. The team owns the methodological "
        "decisions, the collection of the poll orders and the interpretation.*"
    )
