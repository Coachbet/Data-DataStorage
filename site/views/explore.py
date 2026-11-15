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


def finalist_names(results, roles: dict[str, str]) -> dict[str, str]:
    """Outcome names for one election: the finalists by name, the rest as outcomes."""
    labels = results.drop_duplicates("option").set_index("option").label
    names = dict(OUTCOME_NAMES)
    for option, role in roles.items():
        if option.startswith("candidate:"):
            names[role] = labels[option].title()
    return names


def render(ctx) -> None:
    components.page_header(
        "The official results, election by election",
        "Official counts for one election: how registered voters split between candidates, "
        "blank or invalid ballots and abstention, in each round and each area.",
    )
    components.election_picker(ctx)
    if ctx.partial_coverage and ctx.unit == "All units":
        st.warning(
            f"**Not national totals.** The {ctx.year} source file omits voters abroad and some "
            "overseas areas. These totals cover only the areas in the file, so turnout and "
            "candidate figures differ slightly from official national results, for example "
            "those reported on Wikipedia."
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
        "Source: Ministry of the Interior. Each round uses its own registration total. "
        "These are totals at each round; they do not show how individual people moved "
        "between choices."
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
        "Source: Ministry of the Interior. Colours: the two finalists, blank or invalid "
        "ballots and abstention keep their colour on every page; other candidates are grey."
    )
    with st.expander("Exact figures and download"):
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
    components.glossary()
