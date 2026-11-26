"""7. Method & limits: notation, the score, H3 validation, limits and reproduction."""

import streamlit as st

import data
import ui

PAGE = "method"

LIMITS = [
    (
        "Totals are not individual transfers",
        "Different individual choices give the same area totals (Introduction, 1.2). A rule that fits is not an observed transfer.",
    ),
    (
        "The unit is the area, not the polling station",
        "Aggregating ~70,000 stations into ~100 areas hides variation inside areas and widens the range of behaviours compatible with the totals.",
    ),
    (
        "2002 rests on one poll",
        "The 2002 positions come from a single institute, and 2002 is the election that decides the five-election ranking.",
    ),
    (
        "The scale is an order, not a distance",
        "Within a poll neighbours are evenly spaced whatever their real gap; institutes' table conventions enter the scale (in 2007 Voynet sits slightly right of Royal). One dimension ignores Europe, sovereignty or ecology.",
    ),
    (
        "Retained groups never move",
        "Real movements of finalists' voters or first-round abstainers are an error floor shared by every rule, which compresses the differences between rules.",
    ),
    (
        "Coverage changes",
        "2002 and 2007 miss voters abroad and some overseas areas; the years are not identical geographic samples.",
    ),
    (
        "Blank and invalid together",
        "The outcome mixes a deliberate act with mistakes; the split exists only for 2017 and 2022 (checked in Results, 4.6).",
    ),
    (
        "Few elections, many rules",
        "Nine rules on five elections: the “best” is partly a selection effect. H0b and H1-soft were added after earlier results were known.",
    ),
]


def render() -> None:
    ui.header(
        "Section 7 · Method & limits",
        "Exact definitions, honest limits",
        "Everything needed to check, criticise or rerun the study.",
    )

    ui.section(PAGE, "s7-1")
    st.markdown(
        "| Symbol | Meaning |\n|---|---|\n"
        "| $a$ | an area: département, overseas territory or voters abroad |\n"
        "| $g$ | a first-round group: a candidate, blank/invalid voters, abstainers |\n"
        "| $k$ | a second-round outcome: finalist A, finalist B, blank/invalid, abstention |\n"
        "| $x_{a,g}$ | first-round share of group $g$ in area $a$ (of registered voters) |\n"
        "| $s_{a,k}$, $\\hat s_{a,k}$ | observed and predicted second-round share |\n"
        "| $\\beta_{g,k}$ | share of group $g$ sent to outcome $k$ by a rule |\n"
        "| $s_c$ | left–right position of candidate $c$, from 0 to 1 |\n"
        "| $w_a$ | weight of area $a$: its share of round-2 registered voters |\n"
    )
    st.latex(
        r"\hat s_{a,k} = \sum_g x_{a,g}\,\beta_{g,k},\qquad \beta_{g,k}\ge0,\qquad \sum_k\beta_{g,k}=1"
    )

    ui.section(PAGE, "s7-2")
    st.markdown("For each area, the mean absolute gap over the four outcomes:")
    st.latex(
        r"\text{error}_a = \frac{100}{4}\sum_{k=1}^{4}\bigl\lvert\hat s_{a,k}-s_{a,k}\bigr\rvert\quad\text{(percentage points)}"
    )
    st.markdown("Then the average over areas, weighted by registered voters:")
    st.latex(
        r"\text{score} = \sum_a w_a\,\text{error}_a,\qquad w_a = \frac{\text{registered}^{(2)}_a}{\sum_{a'}\text{registered}^{(2)}_{a'}}"
    )
    st.markdown(
        "- Gaps are taken **before** averaging, so opposite errors in two areas cannot cancel.\n"
        "- The four outcomes count **equally**.\n"
        "- A large département counts more than a small overseas territory.\n"
        "- A secondary diagnostic, the *gap in combined results*, first adds all areas up and "
        "then compares; there, errors of opposite sign can cancel."
    )
    ui.box(
        "decision",
        "<p>Weight by <b>registered voters of round 2</b> (agreed 31 October): it "
        "matches the evaluated round and needs no population data from INSEE.</p>",
    )

    ui.section(PAGE, "s7-3")
    st.latex(
        r"\beta^{\text{H3}}(p) = (1-p)\,\beta^{\text{base}} + p\,\beta^{\text{H0b}},\qquad \hat p_{e^\ast} = \arg\min_{p}\ \frac14\sum_{e\ne e^\ast}\text{score}_e\bigl(p\bigr)"
    )
    st.markdown(
        "- $p$ is searched on a grid $0, 0.01, \\dots, 1$; ties go to the smallest value.\n"
        "- Each election $e^\\ast$ is held out in turn; its score always uses $\\hat p_{e^\\ast}$.\n"
        "- Areas of one election are never split between training and test."
    )
    folds = data.csv("h3_folds.csv")
    folds = folds[(folds.variant == "positions=polls;tie=split") & folds.test_year.notna()]
    folds = folds.pivot(index="base", columns="test_year", values="p")
    folds.columns = [f"held out {int(c)}" for c in folds.columns]
    st.dataframe(folds.style.format("{:.2f}"), width="stretch")
    ui.caption("Table 7.1", "Fitted p of H3 for each held-out election and proximity base.")
    ui.box(
        "limit",
        "<p>Five folds describe how a rule transfers between elections. They support no "
        "significance test.</p>",
    )

    ui.section(PAGE, "s7-4")
    st.markdown("What we cannot claim, from the most to the least important:")
    for i, (title, text) in enumerate(LIMITS, 1):
        with st.expander(f"{i} · {title}"):
            st.markdown(text)

    ui.section(PAGE, "s7-5")
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
    ui.box(
        "result",
        f"<p>This site recomputes every score from the cleaned tables. Largest difference "
        f"with the published results table: <b>{gap:.1e} pp</b> (rounding only).</p>",
        label="Live check",
    )
    with st.expander("The 22 poll orders and their sources"):
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
            "Orders for 2017 and 2022 come from Delemazure, T., Dong, C., Peters, D. and "
            "Tydrichová, M. (2024). *Comparing Ways of Obtaining Candidate Orderings from "
            "Approval Ballots.* arXiv:2405.04525."
        )
    st.markdown(
        "*AI tools assisted with code, tests and drafting. The team owns the methodological "
        "decisions, the collection of the poll orders and the interpretation.*"
    )
