"""Home: the question, the path from it to the assumptions, how we test them, the answer."""

import charts
import components
import streamlit as st
from vote_transfer.application.presentation import answer, key_findings

QUESTION = (
    "Which assumptions about voter behaviour best explain second-round results in "
    "French presidential elections (2002–2022)?"
)


def go_to(page: str) -> None:
    st.session_state["page"] = page


def node(name: str, text: str, kind: str = "leaf") -> str:
    """One box of the tree: a short name and one line of explanation."""
    return (
        f'<div class="node node-{kind}"><strong>{components.escape(name)}</strong>'
        f"<span>{components.escape(text)}</span></div>"
    )


def leaves(*items: tuple[str, str]) -> str:
    return "<ul>" + "".join(f"<li>{node(name, text)}</li>" for name, text in items) + "</ul>"


def problem() -> None:
    components.section(
        1,
        "The question",
        "question",
        lead="In a French presidential election only two candidates reach the second round, "
        "so the voters of all the other candidates have to choose again.",
    )
    components.html(
        '<div class="question-box"><p class="question-label">Our research question</p>'
        f'<p class="question-text">{components.escape(QUESTION)}</p></div>'
    )
    components.prose(
        "The vote is secret, so the official results only give totals: we know how many "
        "people chose each option in each round, but not who moved where between the two "
        "rounds. That is why we cannot observe the transfers directly. What we can do is "
        "write down possible behaviours as precise rules, predict the second round with "
        "each rule, and check which prediction is closest to what really happened."
    )


def tree() -> None:
    components.section(
        2,
        "From the question to the assumptions",
        "tree",
        lead="We split the question into three families of answers, and each family into "
        "rules that we can test.",
    )
    baselines = leaves(
        ("H0a", "They split like the whole electorate, abstainers included"),
        ("H0b", "They split like the voters only: nobody abstains"),
    )
    threshold = leaves(
        ("H2-abst", "Too far from both: they abstain"),
        ("H2-blank", "Too far from both: they vote blank"),
    )
    proximity = (
        "<ul>"
        f"<li>{node('H1', 'They all vote for the closest finalist')}</li>"
        f"<li>{node('H1-soft', 'They split, the closer finalist gets more')}</li>"
        f"<li>{node('H2', 'Like H1, unless the candidate is far from both', 'branch')}"
        f"{threshold}</li>"
        "</ul>"
    )
    mixture = leaves(("H3", "A share p behaves like H0b, the rest like H1 or H2"))
    components.html(
        '<div class="tree"><ul><li>'
        + node("Where do the voters of eliminated candidates go?", "Second round", "root")
        + "<ul>"
        + f"<li>{node('Baselines', 'Politics does not matter', 'branch')}{baselines}</li>"
        + f"<li>{node('Proximity', 'They follow the left-right scale', 'branch')}{proximity}</li>"
        + f"<li>{node('Mixture', 'A bit of both', 'branch')}{mixture}</li>"
        + "</ul></li></ul></div>"
    )
    components.prose(
        "The baselines are our reference: they use no political information at all. The "
        "proximity rules need a left-right position for every candidate, which we take from "
        "the order in which polling institutes list the candidates (0 is the leftmost, 1 the "
        "rightmost). H3 is the only rule with a number fitted on the data: we fit p on four "
        "elections and test it on the fifth."
    )


def pipeline() -> None:
    components.section(
        3,
        "How we test an assumption",
        "method",
        lead="The same steps are repeated for every rule, every election and every area.",
    )
    steps = [
        ("First round", "Official results of each area, from the Ministry of the Interior"),
        ("Rule", "One assumption says where the eliminated voters go"),
        ("Predicted second round", "Shares of the two finalists, blank or invalid, abstention"),
        ("Observed second round", "The real official results of the same area"),
        ("Error", "Average gap in percentage points: lower means closer"),
    ]
    boxes = '<span class="arrow" aria-hidden="true">→</span>'.join(
        f'<div class="step"><strong>{components.escape(title)}</strong>'
        f"<span>{components.escape(text)}</span></div>"
        for title, text in steps
    )
    components.html(f'<div class="pipeline">{boxes}</div>')


def render(ctx) -> None:
    components.page_header(
        "Where do the voters of eliminated candidates go?",
        "A data project on the five French presidential elections from 2002 to 2022.",
    )
    problem()
    tree()
    pipeline()

    evaluated = ctx.evaluated
    components.section(4, "What we found", "answer")
    if evaluated is None:
        st.info(
            "Cross-election results are not available in this data folder. "
            "Run `vote-transfer evaluate --all-models --all-years`."
        )
        components.glossary()
        return
    comparison, report = evaluated["comparison"], evaluated["report"]
    result = answer(comparison)
    components.html(f'<h3 class="answer-head">{components.escape(result["headline"])}</h3>')
    for sentence in result["sentences"]:
        components.prose(sentence)
    best = comparison["mean"].idxmin()
    components.figure_head(
        f"Average error over the five elections: {best} is the lowest",
        "Average gap between predicted and observed second-round shares, per area, in "
        "percentage points. Lower is closer. The two baselines are dark.",
    )
    charts.mean_bars(comparison)
    components.source(
        "Source: Ministry of the Interior results by polling station; our calculations. "
        "Each area counts in proportion to its registered voters. H3 is scored on elections "
        f"it was not fitted on. {report['coding_status'].capitalize()}."
    )

    components.section(5, "Three findings", "findings")
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
    st.warning(
        f"**{report['coding_status'].capitalize()}.** "
        "H1, H2 and H3 place candidates with the left-to-right orders published by polling "
        "institutes; the earlier hand-coded 1-7 scale is kept as a comparison "
        f"({report.get('comparison_coding_status', 'draft coding')}). "
        "The 2002 and 2007 files omit some overseas areas and voters abroad, so those years "
        "describe covered areas only. " + components.AGGREGATE_NOTE
    )
    components.glossary()
