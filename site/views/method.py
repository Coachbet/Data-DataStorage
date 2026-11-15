"""Method & sources: where the numbers come from, how they were checked, what they cannot say."""

import components
import streamlit as st
from vote_transfer.application.presentation import fmt_int
from vote_transfer.application.source_catalog import SOURCES


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
    components.election_picker(ctx, area=False)
    components.html(
        '<ul class="links">'
        + "".join(
            f'<li><a href="{components.escape(source.landing_url)}" target="_blank" '
            f'rel="noopener">Original Ministry dataset, {components.escape(ctx.year)}, '
            f"round {components.escape(source.key[-1])}</a></li>"
            for source in SOURCES
            if source.key.startswith(f"official_{ctx.year}_")
        )
        + "</ul>"
    )
    st.caption(
        "The 2002–2012 source files contain both rounds together. Links for those "
        "rounds lead to the same dataset."
    )
    if quality.get("geographic_labels") == "codes_only":
        st.info(
            "This year's source does not provide department names. We display its "
            "original reporting-area codes rather than attach unverified modern names."
        )
    components.prose(
        "A second input is made by the team: a table that places each first-round candidate "
        "on a seven-point left–right scale. H1, H2 and H3 read it; H0a and H0b do not. "
        "It is the weakest input and is still a draft."
    )

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
        "4. **Every model is an assumption.** H1, H2 and H3 depend on hand-coded candidate "
        "positions that are still drafts. The 2027 page explores hypothetical scenarios on "
        "the 2022 electorate; it does not forecast an election."
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

    components.section(4, "Reproduce the results", "reproduce")
    st.code(
        "uv sync --locked --dev\n"
        "make analysis    # every result, figure and table, from the bundled snapshots\n"
        f"uv run vote-transfer acquire --year {ctx.year}\n"
        f"uv run vote-transfer process --year {ctx.year}",
        language=None,  # plain: syntax colours would add hues that mean nothing
    )
    with st.expander("What comes next in the research?"):
        st.markdown(
            "- Two team members code the candidate positions independently; agreement "
            "is reported and every model is rerun.\n"
            "- Compare historical results against the consolidated reference dataset.\n"
            "- Out of scope, as future work: strategic first-round voting (H4), transfers "
            "learned by political family (H5) and two-dimensional positions."
        )

    components.section(5, "Candidate positions and definitions", "reference")
    components.candidate_reference(ctx.year)
    components.glossary()
    st.caption(
        "AI assisted with development, documentation and tests. The project team is "
        "responsible for source verification, methodological decisions and interpretation."
    )
