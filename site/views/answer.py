"""Home: the question, the path from it to the assumptions, how we test them, the answer."""

import charts
import components
import streamlit as st
from vote_transfer.application.presentation import answer, fmt_pct, key_findings

QUESTION = (
    "Which assumptions about voter behaviour best explain second-round results in "
    "French presidential elections (2002–2022)?"
)


def go_to(page: str) -> None:
    st.session_state["page"] = page


def threshold_finding(threshold) -> dict:
    """The H2 finding on the poll-based scale: one election carries almost all of it."""
    table = threshold.sort_values("beyond_threshold_pct")
    peak, rest = table.iloc[-1], table.iloc[:-1]
    return {
        "title": "The distance threshold fails in one election.",
        "body": (
            f"In {peak.year} both finalists are on the right of the scale, so H2 sends "
            f"{fmt_pct(peak.beyond_threshold_pct)} of registered voters to a non-vote, while "
            f"most of them voted. In the other elections it removes "
            f"{fmt_pct(rest.beyond_threshold_pct.max())} at most, so the threshold is really "
            "tested only once."
        ),
    }


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
        "people chose each option in each round, but not who moved where. So we cannot "
        "observe the transfers directly. What we can do is write possible behaviours as "
        "precise rules, predict the second round with each rule, and check which "
        "prediction is the closest to what really happened."
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
        "The baselines are our reference, because they use no political information. The "
        "proximity rules and the mixture need a left-right position for every candidate: we "
        "take it from the order in which polling institutes list the candidates, from 0 "
        "(leftmost) to 1 (rightmost). H3 is the only rule with a number fitted on the data: "
        "we fit p on four elections and test it on the fifth."
    )
    st.button(
        "See the candidate positions used by H1, H1-soft, H2 and H3 →",
        key="to_candidates",
        type="tertiary",
        on_click=go_to,
        args=("Method & sources",),
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


SECTIONS = [
    ("The question", "question"),
    ("The assumptions", "tree"),
    ("How we test them", "method"),
    ("What we found", "answer"),
    ("Three findings", "findings"),
    ("Definitions", "definitions"),
]


def render(ctx) -> None:
    components.page_header(
        "Where do the voters of eliminated candidates go?",
        "A data project on the five French presidential elections from 2002 to 2022.",
    )
    components.contents(SECTIONS)
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
    else:
        findings(evaluated)
    components.section(6, "Definitions", "definitions")
    components.glossary()


def findings(evaluated: dict) -> None:
    comparison, report = evaluated["comparison"], evaluated["report"]
    result = answer(comparison)
    components.html(f'<h3 class="answer-head">{components.escape(result["headline"])}</h3>')
    for sentence in result["sentences"]:
        components.prose(sentence)
    best = comparison["mean"].idxmin()
    components.figure_head(
        f"Average error over the five elections: {best} is the lowest",
        "Average gap between the predicted and the observed second round, per area, in "
        "percentage points (pp). Lower is closer. The two baselines are in dark grey.",
    )
    charts.mean_bars(comparison)
    components.source(
        "Source: Ministry of the Interior, results by polling station; our calculations. "
        "Each area counts in proportion to its registered voters, and H3 is always scored on "
        "an election it was not fitted on. The 2002 and 2007 files miss some overseas areas "
        f"and the voters abroad. {report['coding_status'].capitalize()}: the positions come "
        "from polling institutes. These are patterns in the totals, not individual transfers."
    )

    components.section(5, "Three findings", "findings")
    cards = key_findings(comparison, evaluated["errors"], evaluated["threshold"])
    cards[2] = threshold_finding(evaluated["threshold"])
    links = ["See where each assumption misses", "See the comparison table", "See the threshold"]
    for number, (column, finding, link) in enumerate(
        zip(st.columns(len(cards)), cards, links, strict=True), 1
    ):
        with column.container(key=f"finding_card_{number}"):
            components.html(
                f"<h3>{components.escape(finding['title'])}</h3>"
                f"<p>{components.escape(finding['body'])}</p>"
            )
            st.button(
                f"{link} →",
                key=f"finding_{number}",
                type="tertiary",
                on_click=go_to,
                args=("Evidence",),
            )
