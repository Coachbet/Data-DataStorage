"""2027 scenarios: what an assumption implies for a runoff on the 2022 electorate."""

import charts
import components
import loaders
import pandas as pd
import streamlit as st
from theme import OUTCOME_NAMES
from vote_transfer.application.presentation import ROLES, fmt_pct
from vote_transfer.application.scenario import (
    BANNER,
    DEFAULT_MODEL,
    LIMITS,
    SCENARIO_MODELS,
    SCENARIO_YEAR,
    scenario_candidates,
)

FRAME_LABEL = "Hypothetical · 2022 electorate · not a forecast"


def render(ctx) -> None:
    components.page_header(
        "A hypothetical runoff on the 2022 electorate",
        "Choose two 2022 first-round candidates as stand-ins for the finalists and one "
        "assumption. The page applies that assumption to the 2022 first-round results of "
        "every area. It uses no 2027 data and no polls.",
    )
    evaluated = ctx.evaluated
    status = evaluated["report"]["coding_status"] if evaluated else "draft coding"
    st.warning(
        f"**{BANNER}** {status.capitalize()}. Aggregate assumptions, not individual transfers."
    )
    if evaluated is None or str(SCENARIO_YEAR) not in ctx.datasets:
        st.info(
            "Scenarios need the 2022 election and the cross-election evaluation in this "
            "data folder. Run `vote-transfer evaluate --all-models --all-years`."
        )
        return

    folder = ctx.datasets[str(SCENARIO_YEAR)]
    electorate = loaders.dataset(folder)[0]
    candidates = scenario_candidates(electorate)
    names = {row.option: row.label.title() for row in candidates.itertuples()}
    ranks = evaluated["comparison"]
    best_model = ranks["mean"].idxmin()

    with st.container(border=True, key="scenario_frame"):
        components.html(f'<p class="frame-label">{components.escape(FRAME_LABEL)}</p>')
        a, b, c = st.columns(3)
        first_choice = a.selectbox(
            "First finalist", list(names), index=0, key="scenario_a", format_func=names.get
        )
        second_choice = b.selectbox(
            "Second finalist", list(names), index=1, key="scenario_b", format_func=names.get
        )
        model_choice = c.selectbox(
            "Assumption",
            SCENARIO_MODELS,
            index=SCENARIO_MODELS.index(DEFAULT_MODEL),
            key="scenario_model",
        )
        default_rank = ranks.loc[DEFAULT_MODEL]
        st.caption(
            f"{DEFAULT_MODEL} is the default: it needs no candidate coding and ranks "
            f"{int(default_rank['rank'])} of {len(ranks)} with 2002 and "
            f"{int(default_rank['rank_without_2002'])} without it"
            + (
                f", while {best_model}, the lowest five-election mean, owes its lead to 2002 "
                f"and ranks {int(ranks.loc[best_model, 'rank_without_2002'])} without it."
                if best_model != DEFAULT_MODEL
                else "."
            ),
        )
        show_all = st.checkbox(
            "Show all models side by side",
            key="scenario_all",
            help="Every evaluated assumption for this runoff. The spread between them is the "
            "message: none is clearly best.",
        )
        if first_choice == second_choice:
            st.error("Choose two different candidates.")
            return

        pair = (first_choice, second_choice)
        chosen = loaders.scenario(folder, ctx.root, pair, model_choice)
        baseline = loaders.scenario(folder, ctx.root, pair, DEFAULT_MODEL)
        labels = {
            "finalist_a": names[chosen["finalist_a"]],
            "finalist_b": names[chosen["finalist_b"]],
            "blank_invalid": "Blank or invalid ballot",
            "abstention": "Did not vote",
        }
        if show_all:
            every = loaders.scenario(folder, ctx.root, pair)
            columns = {model: every[model] for model in every}
        elif model_choice != DEFAULT_MODEL:
            columns = {model_choice: chosen["pooled_pct"], DEFAULT_MODEL: baseline["pooled_pct"]}
        else:
            columns = {model_choice: chosen["pooled_pct"]}

        versus = f"{labels['finalist_a']} against {labels['finalist_b']}"
        spread = [values["finalist_a"] for values in columns.values()]
        components.figure_head(
            f"If the 2022 electorate faced {versus}: {labels['finalist_a']} between "
            f"{fmt_pct(min(spread))} and {fmt_pct(max(spread))} of registered voters, "
            "depending on the assumption"
            if len(columns) > 1
            else f"If the 2022 electorate faced {versus}, {model_choice} would imply "
            f"{fmt_pct(spread[0])} of registered voters for {labels['finalist_a']}",
            "Hypothetical, not a forecast. Implied share of 2022 first-round registered "
            "voters, all areas pooled, under each assumption shown.",
        )
        key_names = OUTCOME_NAMES | {
            "finalist_a": labels["finalist_a"],
            "finalist_b": labels["finalist_b"],
        }
        components.outcome_key({role: key_names[role] for role in ROLES})
        charts.stacked_rows(
            pd.DataFrame(
                [
                    {"row": model, "segment": role, "pct": float(values[role])}
                    for model, values in columns.items()
                    for role in ROLES
                ]
            ),
            key_names,
            "Implied share of registered voters (%)",
        )
        national = pd.DataFrame(
            {"Outcome": list(labels.values())}
            | {f"{model} (%)": [values[k] for k in labels] for model, values in columns.items()}
        )
        components.data_table(national, {c: "{:.1f}" for c in national.columns[1:]})
        st.caption(
            "Hypothetical, not a forecast. Shares of 2022 first-round registered voters, "
            "all areas pooled. "
            f"Among the two finalists only, {model_choice} gives {labels['finalist_a']} "
            f"{chosen['finalist_a_valid_pct']:.1f}%"
            + (
                f" and {DEFAULT_MODEL} gives {baseline['finalist_a_valid_pct']:.1f}%. "
                f"{DEFAULT_MODEL} is always shown for comparison."
                if model_choice != DEFAULT_MODEL
                else "."
            )
            + (
                f" H3 uses p = {chosen['p']:.2f}, fitted on the five historical elections."
                if chosen["p"] is not None
                else ""
            )
        )
        components.note(
            "How to read this.",
            "This is what the chosen assumption implies if the 2022 first-round electorate "
            "faced this runoff. It is not a prediction for 2027: the candidates, the "
            "electorate and the campaign will differ, and no 2027 data enters this page.",
        )
        with st.expander("Area-level table and download"):
            areas = chosen["areas"].rename(
                columns={
                    "area_code": "Area code",
                    "area_name": "Area",
                    "registered": "Registered (2022 R1)",
                    "finalist_a_pct": f"{labels['finalist_a']} (%)",
                    "finalist_b_pct": f"{labels['finalist_b']} (%)",
                    "blank_invalid_pct": "Blank / invalid (%)",
                    "abstention_pct": "Abstention (%)",
                }
            )
            st.dataframe(
                areas,
                hide_index=True,
                width="stretch",
                key="scenario_areas",
                column_config={
                    k: st.column_config.NumberColumn(format="%.1f")
                    for k in areas.columns
                    if k.endswith("(%)")
                },
            )
            st.download_button(
                "Download this scenario (CSV)",
                areas.to_csv(index=False),
                file_name=f"scenario_{model_choice}.csv",
                mime="text/csv",
                key="scenario_download",
            )
        st.caption(LIMITS)
