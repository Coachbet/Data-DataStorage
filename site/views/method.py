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
        "Method and sources",
        "How we place the candidates, what we check, the limits of the project and how to "
        "get the same numbers yourself.",
    )
    components.contents(
        [
            ("Candidate positions", "positions"),
            ("Limits", "limits"),
            ("Checks and storage", "checks"),
            ("The code on GitHub", "github"),
            ("Reproduce the results", "reproduce"),
        ]
    )

    components.section(
        1,
        "Candidate positions",
        "positions",
        lead="H1, H1-soft, H2 and H3 all need to know where each candidate is on the "
        "left-right scale. This table is a big part of our assumptions.",
    )
    with st.container(key="candidates_box"):
        components.prose(
            "Polling institutes list the candidates from left to right in their reports. For "
            "2002 to 2012 we took these orders from the institutes' own reports, and for 2017 "
            "and 2022 from the compilation of Delemazure, Dong, Peters and Tydrichová (2024). "
            "Inside each poll the candidates are evenly spaced between 0 and 1, and then we "
            "take the average over the institutes. H0a and H0b do not use these positions."
        )
        components.election_picker(ctx, area=False)
        components.candidate_reference(ctx.year)
    components.figure_head("The polls behind the scale", "One link per institute and election.")
    poll_sources()

    components.section(2, "Limits", "limits")
    st.markdown(
        "1. **Totals are not personal voting histories.** Different individual choices can "
        "give the same totals in an area, so our results are not individual transfers.\n"
        "2. **Coverage changes.** The 2002 and 2007 files miss some overseas areas and the "
        "voters abroad, and the area boundaries were not harmonised.\n"
        "3. **Blank and invalid together.** Before 2017 the files report them together, so we "
        "always use their total.\n"
        "4. **The scale is an order.** The polls give an order of the candidates: it is an "
        "order, not a measured ideological distance."
    )

    components.section(3, "Checks and storage", "checks")
    if quality.get("geographic_labels") == "codes_only":
        st.info(
            "This year's file does not give department names, so we show the original area "
            "codes instead of adding modern names that we could not check."
        )
    components.prose(
        f"For {ctx.year} the data has {fmt_int(quality['polling_station_round_rows'])} "
        f"polling-station records in {quality['territorial_units']} areas. We check the "
        "source files, duplicates, negative counts, the turnout accounting, the candidate "
        "totals and that both rounds cover the same areas. If a check fails the build "
        "stops: we never remove, fill in or correct an observation."
    )
    components.prose(
        "The original files are kept unchanged and checked with a checksum. The cleaned data "
        "is stored as Parquet tables, and the shares are computed when the data is read."
    )

    components.section(4, "The code on GitHub", "github")
    components.html(
        '<p class="prose">Everything behind this site is in one repository: '
        f'<a href="{REPO}" target="_blank" rel="noopener">{REPO.removeprefix("https://")}</a>. '
        "The cleaned data of the five elections is included, so anyone can get the same "
        "numbers without downloading anything else.</p>"
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

    components.section(
        5,
        "Reproduce the results",
        "reproduce",
        lead="Every step is a short make command. Make calls uv for us, so you never have to "
        "install packages by hand: the first command installs the exact versions we used.",
    )
    st.code(
        "make setup      # install the exact package versions (uv.lock)\n"
        "make app        # open this site on your computer\n"
        "make analysis   # every result, figure and table, from the data in the repository\n"
        "make data       # download the Ministry files again and rebuild everything\n"
        "make check      # run the tests",
        language=None,  # plain: syntax colours would add hues that mean nothing
    )

    st.caption(
        "AI assisted with development, documentation and tests. The project team is "
        "responsible for source verification, methodological decisions and interpretation."
    )
