"""Explore the data: one election, by round and by area."""

import charts
import components
import streamlit as st
from theme import OUTCOME_NAMES
from vote_transfer.application.exploration import round_summary
from vote_transfer.application.presentation import (
    fmt_int,
    fmt_pct,
    outcome_roles,
    rounds_side_by_side,
)
from vote_transfer.application.source_catalog import SOURCES


def finalist_names(results, roles: dict[str, str]) -> dict[str, str]:
    """Outcome names for one election: the finalists by name, the rest as outcomes."""
    labels = results.drop_duplicates("option").set_index("option").label
    names = dict(OUTCOME_NAMES)
    for option, role in roles.items():
        if option.startswith("candidate:"):
            names[role] = labels[option].title()
    return names


FIELDS = [
    ("Inscrits", "Registered voters", "Everyone on the electoral roll of the polling station"),
    ("Abstentions", "Abstention", "Registered voters who did not vote"),
    ("Votants", "Voters", "People who cast a ballot, valid or not"),
    ("Blancs, Nuls", "Blank or invalid", "Ballots that count for no candidate; we add them up"),
    ("Exprimés", "Valid votes", "Ballots for a candidate; used only for the usual percentages"),
    ("Voix", "Votes per candidate", "One count per candidate and polling station"),
]


def provenance() -> None:
    """Where the election files come from, what they are called and what we keep."""
    components.section(
        None,
        "Where the data comes from",
        "provenance",
        lead="All the results come from the French Ministry of the Interior. It publishes "
        "one file per election on data.gouv.fr, with one line per polling station "
        "('bureau de vote').",
    )
    rows = "".join(
        f"<tr><td>{year}</td>"
        + "".join(
            f'<td><a href="{components.escape(source.landing_url)}" target="_blank" '
            f'rel="noopener">Original Ministry dataset, {year}, round {source.key[-1]}</a></td>'
            for source in SOURCES
            if source.key.startswith(f"official_{year}_")
        )
        + "</tr>"
        for year in sorted(
            {source.key.split("_")[1] for source in SOURCES if source.key.startswith("official_")}
        )
    )
    components.html(
        '<table class="plain-table"><thead><tr><th>Election</th><th>Round 1</th>'
        f"<th>Round 2</th></tr></thead><tbody>{rows}</tbody></table>"
    )
    st.caption(
        "The datasets are called 'Élection présidentielle … résultats par bureaux de "
        "vote'. For 2002 to 2012 one file has both rounds, so the two links go to the "
        "same dataset. We keep the original files unchanged and check them with a checksum."
    )
    components.html('<div id="keep"></div>')
    components.figure_head(
        "What we keep from each file",
        "The original column names are in French. We keep these counts for every polling "
        "station, then add them up by area (department, overseas territory or voters abroad).",
    )
    table = "".join(
        f"<tr><td><code>{components.escape(french)}</code></td><td>{components.escape(name)}"
        f"</td><td>{components.escape(text)}</td></tr>"
        for french, name, text in FIELDS
    )
    components.html(
        '<table class="plain-table"><thead><tr><th>In the file</th><th>On this site</th>'
        f"<th>What it counts</th></tr></thead><tbody>{table}</tbody></table>"
    )
    components.note(
        "Why registered voters.",
        "Most news sites give percentages of valid votes. We use shares of registered voters "
        "instead, because abstention and blank or invalid ballots are outcomes of the second "
        "round too, and our assumptions have to predict them.",
    )


def render(ctx) -> None:
    components.page_header(
        "The data: official results from 2002 to 2022",
        "First where the numbers come from and what we keep, then one election in detail.",
    )
    components.contents(
        [
            ("Where the data comes from", "provenance"),
            ("What we keep", "keep"),
            ("Both rounds side by side", "rounds"),
            ("One round in detail", "round"),
        ]
    )
    provenance()
    components.section(None, "Explore one election", "explore")
    components.election_picker(ctx)
    if ctx.partial_coverage and ctx.unit == "All units":
        st.warning(
            f"**Not national totals.** The {ctx.year} file does not include the voters abroad "
            "and some overseas areas, so these figures are a bit different from the national "
            "results you can find, for example, on Wikipedia."
        )
    roles = outcome_roles(ctx.results)
    names = finalist_names(ctx.results, roles)

    components.section(1, "Both rounds side by side", "rounds")
    both = rounds_side_by_side(ctx.selected, roles)
    shares = both.set_index(["row", "segment"]).pct
    components.figure_head(
        f"Abstention went from {fmt_pct(shares['Round 1', 'abstention'])} to "
        f"{fmt_pct(shares['Round 2', 'abstention'])} between the rounds; blank or invalid "
        f"ballots from {fmt_pct(shares['Round 1', 'blank_invalid'])} to "
        f"{fmt_pct(shares['Round 2', 'blank_invalid'])}",
        f"Share of registered voters in each round, {ctx.year}, {ctx.area}.",
    )
    components.outcome_key(names)
    charts.stacked_rows(both, names, "Share of registered voters (%)")
    components.source(
        "Source: Ministry of the Interior. Each round uses its own number of registered "
        "voters. These are totals, so they do not show how people moved between the rounds."
    )

    components.section(2, "One round in detail", "round")
    round_number = st.radio(
        "Round", [1, 2], format_func=lambda n: f"Round {n}", horizontal=True, key="round"
    )
    summary = round_summary(ctx.selected, round_number)
    components.stat_row(
        [
            (
                "Registered voters",
                fmt_int(summary["registered"]),
                "Everyone on the electoral roll in the selected areas and round.",
            ),
            (
                "Cast a ballot",
                fmt_pct(summary["turnout_pct"]),
                "Includes valid, blank and invalid ballots.",
            ),
            (
                "Did not vote",
                fmt_pct(summary["abstention_pct"]),
                "Abstention as a share of registered voters.",
            ),
        ]
    )
    basis = st.radio(
        "Show percentages of",
        ["Registered voters", "Valid votes"],
        captions=["Used by our models", "As usually reported"],
        horizontal=True,
        key="basis",
    )
    totals = summary["totals"].assign(role=summary["totals"].option.map(roles).fillna("other"))
    if basis == "Valid votes":
        candidates = totals.dropna(subset=["valid_share_pct"])
        leader = candidates.iloc[0]
        components.figure_head(
            f"{leader.outcome} received {fmt_pct(leader.valid_share_pct)} of valid votes, "
            f"which is {fmt_pct(leader.share_pct)} of registered voters",
            f"Round {round_number}, {ctx.year}, {ctx.area}. Share of ballots cast for a "
            "candidate, as results are usually reported. Abstention and blank or invalid "
            "ballots are left out, so this view cannot show the whole electorate.",
        )
        charts.round_bars(
            candidates.assign(value=candidates.valid_share_pct), "Share of valid votes (%)"
        )
        components.note(
            "How to read this.",
            f"Of every 100 valid votes in this selection, {leader.outcome} received about "
            f"{leader.valid_share_pct:.1f}. Out of all registered voters, the same votes are "
            f"{leader.share_pct:.1f}%.",
        )
    else:
        components.figure_head(
            f"{fmt_pct(summary['turnout_pct'])} of registered voters cast a ballot; "
            f"{fmt_pct(summary['abstention_pct'])} did not",
            f"Round {round_number}, {ctx.year}, {ctx.area}. Share of registered voters: the "
            "basis our models use, because abstention and blank ballots are outcomes too.",
        )
        charts.round_bars(totals.assign(value=totals.share_pct), "Share of registered voters (%)")
        components.note("How to read this.", summary["reading"])
    components.source(
        "Source: Ministry of the Interior. The finalists, blank or invalid ballots and "
        "abstention keep the same colour on every page; the other candidates are grey."
    )
    components.figure_head("Exact figures", f"Round {round_number}, {ctx.year}, {ctx.area}.")
    table = summary["totals"][["outcome", "count", "share_pct", "valid_share_pct"]].copy()
    table.columns = [
        "Outcome",
        "People / ballots",
        "Registered electorate (%)",
        "Valid votes (%)",
    ]
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Registered electorate (%)": st.column_config.NumberColumn(format="%.1f"),
            "Valid votes (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.download_button(
        "Download this round (CSV)",
        ctx.selected[ctx.selected["round"] == round_number].to_csv(index=False),
        file_name=f"election_{ctx.year}_{ctx.unit.replace(' ', '_')}_round_{round_number}.csv",
        mime="text/csv",
    )
