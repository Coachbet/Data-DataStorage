"""Method & sources: where the numbers come from, how they were checked, what they cannot say."""

import components
import pandas as pd
import streamlit as st
from vote_transfer.application.positions import REFERENCE_DIR
from vote_transfer.application.presentation import fmt_int

REPO = "https://github.com/Coachbet/Data-DataStorage"
REPO_FOLDERS = [
    (
        "backend/",
        "The Python code: download and check the Ministry files, clean them, run "
        "every assumption and compute the errors",
    ),
    ("site/", "This website (Streamlit)"),
    (
        "data/bundled/",
        "The cleaned results of the five elections and all the predictions, "
        "so the site works without downloading anything",
    ),
    ("data/reference/", "The polls' left-right orders and the candidate table, with their sources"),
    ("notebooks/", "The notebook that turns the poll orders into the 0 to 1 score"),
    ("reports/", "The tables and figures used in the report"),
    ("docs/", "The report, the methodology and our answers to the peer reviews"),
    ("tests/", "Automatic tests that check the data, the models and the site"),
]

PAPER = (
    "Delemazure, T., Dong, C., Peters, D. and Tydrichová, M. (2024). Comparing Ways of "
    "Obtaining Candidate Orderings from Approval Ballots. arXiv:2405.04525",
    "https://arxiv.org/abs/2405.04525",
)


def poll_sources() -> None:
    """The polls behind the candidate scale, one line per election, each with its link."""
    try:
        polls = pd.read_csv(REFERENCE_DIR / "polling_axes.csv", keep_default_na=False)
    except OSError as exc:
        st.error(f"The list of polls could not be opened: {exc}")
        return
    items = []
    for year, group in polls.groupby("year"):
        reports = group[group.source_url != PAPER[1]]
        links = ", ".join(
            f'<a href="{components.escape(row.source_url)}" target="_blank" rel="noopener">'
            f"{components.escape(row.institute)}</a>"
            for row in reports.itertuples()
        )
        compiled = group[group.source_url == PAPER[1]].institute.tolist()
        parts = [links] if links else []
        if compiled:
            parts.append(
                f"{components.escape(', '.join(compiled))}, as compiled in the paper below"
            )
        items.append(f"<li><strong>{year}</strong>: {'; '.join(parts)}</li>")
    components.html(f'<ul class="links">{"".join(items)}</ul>')
    components.html(
        f'<p class="prose">{components.escape(PAPER[0])}. '
        f'<a href="{PAPER[1]}" target="_blank" rel="noopener">arxiv.org/abs/2405.04525</a></p>'
    )


def render(ctx) -> None:
    quality = ctx.quality
    components.page_header(
        "Where the numbers come from, and what they cannot say",
        "The figures come from the Ministry of the Interior's polling-station files. We check "
        "the counts, add them up by reporting area and compute the same outcomes for every "
        "election.",
    )
    components.contents(
        [
            ("Sources", "sources"),
            ("Limits", "limits"),
            ("Checks, cleaning and storage", "checks"),
            ("Reproduce the results", "reproduce"),
            ("Candidate positions and definitions", "reference"),
        ]
    )

    components.section(1, "Sources", "sources")
    components.prose(
        "The election results come from the Ministry of the Interior; the links to every "
        "file, and the columns we keep, are on the Explore the data page."
    )
    components.election_picker(ctx, area=False)
    if quality.get("geographic_labels") == "codes_only":
        st.info(
            "This year's source does not provide department names. We display its "
            "original reporting-area codes rather than attach unverified modern names."
        )
    components.prose(
        "The second input places each first-round candidate on a left–right scale from 0 "
        "(leftmost) to 1 (rightmost). It is built from the left-to-right orders that polling "
        "institutes publish in their pre-election polls: within each poll the candidates are "
        "evenly spaced, then each candidate's positions are averaged across institutes. "
        "For 2002 to 2012 the orders come from the institutes' own reports; for 2017 and "
        "2022 from the compilation by Delemazure, Dong, Peters and Tydrichová (2024). "
        "H1, H1-soft, H2 and H3 read this scale; H0a and H0b do not. Our earlier hand-coded "
        "seven-family scale is kept only as a comparison."
    )
    poll_sources()

    components.section(2, "Limits", "limits", lead="Four things to keep in mind.")
    st.markdown(
        "1. **Totals are not personal voting histories.** Different individual "
        "behaviours can produce the same area totals.\n"
        "2. **Coverage changes.** The 2002 and 2007 files omit some overseas areas "
        "and voters abroad. "
        "Historical boundaries have not been harmonised, so years are not identical "
        "geographic samples.\n"
        "3. **Ballot detail changes.** Before 2017, blank and invalid ballots are "
        "reported together. "
        "We use their combined total for every year.\n"
        "4. **Every model is an assumption.** H1, H2 and H3 place candidates with the "
        "left-to-right orders published by polling institutes: an order, not a measured "
        "ideological distance."
    )

    components.section(3, "Checks, cleaning and storage", "checks")
    components.prose(
        f"The {ctx.year} build contains {fmt_int(quality['polling_station_round_rows'])} "
        f"polling-station records across {quality['territorial_units']} reporting areas. "
        "Checks cover source-file integrity, duplicate records, nonnegative counts, turnout "
        "accounting, candidate vote totals and matching area coverage between rounds. "
        "A failed check stops the build: no observation is removed, imputed or corrected."
    )
    components.prose(
        "Raw files are kept unchanged and pinned by checksum. Cleaned data is stored as "
        "Parquet tables: per election, one table of areas, one of counts per outcome and one "
        "of labels; and one long table of predictions for every assumption. Shares are "
        "computed when the data is read, never stored."
    )
    st.caption(
        "Using a bundled aggregate snapshot."
        if ctx.datasets[ctx.year].parent.name == "bundled"
        else "Using a complete local processed dataset."
    )
    with st.expander("Quality report of this build"):
        st.json(quality, expanded=False)

    components.section(4, "The code on GitHub", "github")
    components.html(
        '<p class="prose">Everything behind this site is in one public repository: '
        f'<a href="{REPO}" target="_blank" rel="noopener">{REPO.removeprefix("https://")}</a>. '
        "Anyone can download it and get the same numbers, because the cleaned data for the "
        "five elections is included and every step is a command.</p>"
    )
    components.html(
        '<table class="plain-table"><thead><tr><th>Folder</th><th>What is inside</th></tr>'
        "</thead><tbody>"
        + "".join(
            f"<tr><td><code>{components.escape(folder)}</code></td>"
            f"<td>{components.escape(text)}</td></tr>"
            for folder, text in REPO_FOLDERS
        )
        + "</tbody></table>"
    )

    components.section(5, "Reproduce the results", "reproduce")
    st.code(
        "uv sync --locked --dev\n"
        "make analysis    # every result, figure and table, from the bundled snapshots\n"
        f"uv run vote-transfer acquire --year {ctx.year}\n"
        f"uv run vote-transfer process --year {ctx.year}",
        language=None,  # plain: syntax colours would add hues that mean nothing
    )
    with st.expander("What comes next in the research?"):
        st.markdown(
            "- Check every poll order against its source (in progress).\n"
            "- Compare historical results against the consolidated reference dataset.\n"
            "- Out of scope, as future work: strategic first-round voting (H4), transfers "
            "learned by political family (H5) and two-dimensional positions."
        )

    components.section(6, "Candidate positions and definitions", "reference")
    components.candidate_reference(ctx.year)
    components.glossary()
    st.caption(
        "AI assisted with development, documentation and tests. The project team is "
        "responsible for source verification, methodological decisions and interpretation."
    )
