"""Shared pieces of the interface. Every dynamic value placed in HTML is escaped."""

import base64
from html import escape

import pandas as pd
import streamlit as st
import theme
from vote_transfer.application.presentation import fmt_pct, fmt_pp

LOGO_PATH = theme.SITE_DIR / "assets" / "logo.svg"
AGGREGATE_NOTE = (
    "Results describe aggregate patterns in area totals, not individual transfers: "
    "ballots are secret, and different individual behaviours can produce the same totals."
)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


STYLES = theme.SITE_DIR / "styles.css"


@st.cache_resource(show_spinner=False)
def stylesheet(version: int) -> str:
    """Tokens, embedded fonts and rules as one string; rebuilt when the stylesheet changes."""
    return theme.css_variables() + STYLES.read_text()


def inject_styles() -> None:
    html(f"<style>{stylesheet(STYLES.stat().st_mtime_ns)}</style>")


def navigation(pages: tuple[str, ...]) -> str:
    """Site name and page links, fixed at the top. The radio keeps keyboard support."""
    logo = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    with st.container(key="topbar"):
        html(
            f'<div class="brand"><img src="data:image/svg+xml;base64,{logo}" alt="" width="22" '
            'height="22"><span>Vote Transfer Lab</span></div>'
        )
        return st.radio(
            "Main navigation", pages, key="page", horizontal=True, label_visibility="collapsed"
        )


def remembered(key: str, options: list, default):
    """Keep a picker's value while its widget is on another page."""
    value = st.session_state.get(key, st.session_state.get(f"saved_{key}", default))
    if value not in options:
        value = default
    st.session_state[key] = st.session_state[f"saved_{key}"] = value
    return value


def page_header(title: str, purpose: str, kicker: str | None = None) -> None:
    lead = f'<p class="kicker">{escape(kicker)}</p>' if kicker else ""
    html(
        f'<header class="page-head">{lead}<h1>{escape(title)}</h1>'
        f'<p class="purpose">{escape(purpose)}</p></header>'
    )


def section(number: int | None, title: str, anchor: str, lead: str | None = None) -> None:
    label = f'<span class="section-number">{number}</span>' if number else ""
    body = f'<p class="section-lead">{escape(lead)}</p>' if lead else ""
    html(
        f'<div class="section-head" id="{escape(anchor)}"><h2>{label}{escape(title)}</h2>'
        f"{body}</div>"
    )


def contents(items: list[tuple[str, str]]) -> None:
    links = "".join(f'<li><a href="#{escape(a)}">{escape(t)}</a></li>' for t, a in items)
    html(f'<nav class="contents" aria-label="On this page"><ol>{links}</ol></nav>')


def prose(text: str) -> None:
    """A paragraph held to the reading measure."""
    html(f'<p class="prose">{escape(text)}</p>')


def note(title: str, text: str) -> None:
    """A quiet explanatory note: how to read a chart, or what a table shows."""
    html(f'<aside class="reading"><strong>{escape(title)}</strong> {escape(text)}</aside>')


def figure_head(title: str, subtitle: str) -> None:
    """Chart title that states the takeaway, and a subtitle that states the measure."""
    html(
        f'<div class="figure-head"><h3>{escape(title)}</h3>'
        f'<p class="figure-sub">{escape(subtitle)}</p></div>'
    )


def source(text: str) -> None:
    html(f'<p class="source">{escape(text)}</p>')


def outcome_key(names: dict[str, str], extra: list[tuple[str, str]] | None = None) -> None:
    """Colour key in words. Used where bars cannot each carry their outcome's name."""
    items = "".join(
        f'<li><i class="swatch swatch-{escape(role.replace("_", "-"))}"></i>{escape(name)}</li>'
        for role, name in names.items()
    )
    items += "".join(
        f'<li><i class="swatch {escape(kind)}"></i>{escape(name)}</li>'
        for kind, name in extra or []
    )
    html(f'<ul class="key" aria-label="Colour key">{items}</ul>')


def stat_row(items: list[tuple[str, str, str]]) -> None:
    """Three or four headline figures on one hairline row; label, value, explanation."""
    for column, (label, value, hint) in zip(st.columns(len(items)), items, strict=True):
        column.metric(label, value, help=hint)


def data_table(
    frame: pd.DataFrame,
    formats: dict[str, str] | None = None,
    best: str | None = None,
) -> None:
    """A real HTML table: numbers right-aligned, hairlines, lowest value per row in bold.

    ``best='row'`` marks the lowest number of each row; it is bold and outlined, so
    the mark does not rely on colour.
    """
    styler = frame.style.format(formats or {}, na_rep="—").hide(axis="index")
    numeric = frame.select_dtypes("number").columns
    if best == "row" and len(numeric):
        styler = styler.highlight_min(
            subset=list(numeric),
            axis=1,
            props=f"font-weight:700; box-shadow: inset 0 -2px 0 {theme.COLOUR['ink']}; "
            f"background:{theme.COLOUR['wash']};",
        )
    st.table(styler)


def pct_formats(frame: pd.DataFrame, unit: str = "pct") -> dict:
    formatter = fmt_pct if unit == "pct" else fmt_pp
    return {column: formatter for column in frame.select_dtypes("number").columns}


ASSUMPTIONS = {
    "H0a": "Original baseline. Supporters of eliminated candidates split like the rest of "
    "the electorate, abstainers included.",
    "H0b": "Second baseline. They split between the two finalists and a blank or invalid "
    "ballot, in proportion to first-round shares. None abstain.",
    "H1": "Proximity. Each group goes to the finalist nearest to its candidate on a "
    "seven-point left–right scale.",
    "H2": "Proximity with a threshold. As H1, unless the candidate is at least two steps "
    "from both finalists: then the group abstains (H2-abst) or votes blank (H2-blank).",
    "H3": "Mixture. A share p of each group behaves as in H0b and the rest follows H1 or H2. "
    "p is the only fitted number; it is fitted on four elections and tested on the fifth.",
}


def assumption_summary(model: str) -> str:
    """The short name of an assumption's family: 'Original baseline', 'Mixture', ..."""
    key = model if model in ASSUMPTIONS else model[:2]
    return ASSUMPTIONS[key].split(".")[0]


def assumption_list() -> None:
    """Each assumption in one line. Used wherever the labels H0a to H3 first appear."""
    rows = "".join(
        f"<dt>{escape(name)}</dt><dd>{escape(text)}</dd>" for name, text in ASSUMPTIONS.items()
    )
    html(f'<dl class="assumptions">{rows}</dl>')


def election_picker(ctx, area: bool = True) -> None:
    """Election and area selectors, placed on the page beside what they change."""
    columns = st.columns([1, 2] if area else [1, 2])
    columns[0].selectbox("Election", list(ctx.datasets), key="year")
    if area:
        columns[1].selectbox(
            "Area",
            ["All units", *ctx.unit_labels],
            key="unit",
            format_func=lambda x: (
                "All covered areas" if x == "All units" else f"{x} · {ctx.unit_labels[x]}"
            ),
        )


def glossary() -> None:
    with st.expander("Definitions"):
        st.markdown(
            "**Registered voters**: everyone on the electoral roll, whether or not they voted. "
            "Every share on this site is a share of registered voters unless stated.\n\n"
            "**Abstention**: a registered voter did not cast a ballot.\n\n"
            "**Blank or invalid ballot**: a ballot was cast but did not count for a candidate. "
            "The two are grouped so the outcome has one definition in every year.\n\n"
            "**Percentage point (pp)**: the difference between two percentages. "
            "A predicted share of 30% and an observed share of 25% differ by 5 pp.\n\n"
            "**Reporting area**: an area used in the official files: usually a department, "
            "sometimes an overseas territory or the electorate abroad.\n\n"
            "**Finalist A, finalist B**: the two second-round candidates. A is the one with "
            "more first-round votes.\n\n"
            "**Assumption (model)**: a rule that says where the supporters of eliminated "
            "candidates go in the second round. H0a to H3 are the rules compared here."
        )


def candidate_reference(year: str) -> None:
    with st.expander("Candidate parties and political families"):
        st.write(
            "Our manual reference links each candidate to their party at that election. "
            "The scale runs from 1 (Far left) to 7 (Far right), with Centre at 4. "
            "The team has agreed on this scale; the individual classifications are drafts "
            "for review. H0 does not use these scores."
        )
        try:
            import loaders

            positions, sources = loaders.positions()
        except (OSError, ValueError) as exc:
            st.error(f"The candidate reference could not be opened: {exc}")
            return
        selected = positions[positions.year == int(year)]
        table = selected[
            [
                "candidate_name",
                "party_abbreviation",
                "political_family",
                "ideology_score",
                "alternative_family",
                "review_status",
                "classification_note",
            ]
        ].copy()
        table.columns = [
            "Candidate",
            "Party",
            "Proposed family",
            "Score (1–7)",
            "Alternative family",
            "Review status",
            "Coding note",
        ]
        st.dataframe(table, hide_index=True, width="stretch", key="candidate_table")
        if selected.ideology_score.isna().any():
            st.info(
                "Jacques Cheminade has no score yet: a single left–right classification "
                "is unresolved. Missing does not mean Centre or zero."
            )
        st.caption(
            "Political families simplify different dimensions of politics. Equal numerical "
            "steps are a modelling assumption, not measured ideological distances. "
            "Alternative families identify sensitivity checks; they are not additional scores."
        )
        st.download_button(
            "Download all candidate positions (CSV)",
            positions.to_csv(index=False),
            file_name="candidate_positions.csv",
            mime="text/csv",
            key="candidate_download",
        )
        st.markdown("**References for this election**")
        source_ids = sorted({key for keys in selected.source_ids for key in keys.split(";")})
        for key in source_ids:
            reference = sources[key]
            st.markdown(f"- [{reference['title']}]({reference['url']}), {reference['publisher']}")
        st.caption(
            "Sources document affiliations and background. The seven-category coding is "
            "our research choice, not an official classification."
        )


def coding_banner(report: dict) -> None:
    st.warning(
        f"**{report['coding_status'].capitalize()}.** H1, H2 and H3 read hand-coded candidate "
        "positions. Until two coders have reviewed them independently, treat every result "
        "that depends on them as provisional. Scores describe aggregate patterns, "
        "not individual transfers."
    )


def footer() -> None:
    html(
        f'<footer class="footer"><p>{escape(AGGREGATE_NOTE)}</p>'
        "<p>Vote Transfer Lab · French presidential elections 2002–2022 · "
        "Source: Ministry of the Interior polling-station files, via data.gouv.fr</p></footer>"
    )
