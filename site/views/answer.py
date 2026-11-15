"""The answer: the question, what we found, and the one chart behind it."""

import charts
import components
import streamlit as st
from vote_transfer.application.presentation import answer, election_columns, key_findings

QUESTION = (
    "Which assumptions about voter behaviour best explain second-round results in "
    "French presidential elections (2002–2022)?"
)


def go_to(page: str) -> None:
    st.session_state["page"] = page


def outlier_note(comparison) -> dict | None:
    """Name the election in which most assumptions have their largest error."""
    years = election_columns(comparison)
    worst = comparison[years].astype(float).idxmax(axis=1)
    year, count = worst.value_counts().index[0], int(worst.value_counts().iloc[0])
    if count <= len(comparison) / 2:
        return None
    return {
        "Election": year,
        "score": float(comparison[year].max()),
        "text": f"{year}: the largest error of {count} of the {len(comparison)} assumptions",
    }


def render(ctx) -> None:
    evaluated = ctx.evaluated
    if evaluated is None:
        components.page_header(
            "The comparison of assumptions has not been computed here",
            "This page states the current answer once every assumption has been evaluated.",
            kicker=QUESTION,
        )
        st.info(
            "Cross-election results are not available in this data folder. "
            "Run `vote-transfer evaluate --all-models --all-years`."
        )
        components.assumption_list()
        components.glossary()
        return

    comparison, report = evaluated["comparison"], evaluated["report"]
    result = answer(comparison)
    components.page_header(result["headline"], " ".join(result["sentences"]), kicker=QUESTION)

    best = result["best"]
    highlight = ["H0a", "H0b", best if best not in ("H0a", "H0b") else "H1"]
    components.figure_head(
        result["chart_title"],
        "Average gap between predicted and observed second-round shares, per area, in "
        f"percentage points. Named: {', '.join(highlight)}. Grey: the other assumptions.",
    )
    charts.comparison_dots(comparison, highlight, outlier_note(comparison))
    components.source(
        "Source: Ministry of the Interior results by polling station; our calculations. "
        "Each error is weighted by the area's registered voters. H3 is scored on elections "
        f"it was not fitted on. {report['coding_status'].capitalize()}."
    )

    components.section(None, "The assumptions, in one line each", "assumptions")
    components.assumption_list()

    components.section(None, "Three findings", "findings")
    findings = key_findings(comparison, evaluated["errors"], evaluated["threshold"])
    for number, finding in enumerate(findings, 1):
        components.html(
            f'<div class="finding"><span class="finding-number">{number}</span>'
            f"<div><h3>{components.escape(finding['title'])}</h3>"
            f"<p>{components.escape(finding['body'])}</p></div></div>"
        )
        st.button(
            f"{finding['evidence']} →",
            key=f"finding_{number}",
            type="tertiary",
            on_click=go_to,
            args=("Evidence",),
        )

    components.section(None, "Status of these results", "status")
    draft = "draft" in report["coding_status"]
    st.warning(
        f"**{report['coding_status'].capitalize()}.** "
        + (
            "H1, H2 and H3 use candidate positions that two coders have not yet reviewed "
            "independently: `[PENDING: coder agreement]`. "
            if draft
            else "The candidate positions used by H1, H2 and H3 have been reviewed. "
        )
        + "H3 fits one parameter and is shown pending approval: "
        "`[PENDING: professor approval]`. The 2002 and 2007 files omit some overseas areas "
        "and voters abroad, so those years describe covered areas only. "
        + components.AGGREGATE_NOTE
    )
    components.glossary()
