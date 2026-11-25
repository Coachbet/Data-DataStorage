"""Evidence: what each assumption does, how close it gets, and where it misses."""

import charts
import components
import pandas as pd
import streamlit as st
from theme import OUTCOME_NAMES
from vote_transfer.application.analysis import MODEL_ORDER
from vote_transfer.application.exploration import model_summary
from vote_transfer.application.models import THRESHOLD
from vote_transfer.application.presentation import (
    answer,
    count_of,
    election_columns,
    fmt_pct,
    fmt_pp,
    join_years,
    outcome_roles,
)
from vote_transfer.application.quality import territory_type

SECTIONS = [
    ("What each assumption does", "ladder"),
    ("Which assumption is closest", "comparison"),
    ("Where each assumption misses", "errors"),
    ("What the threshold removes", "threshold"),
    ("Area by area", "areas"),
    ("Does the coding change the answer?", "sensitivity"),
    ("One election in detail: H0a", "h0a"),
]
BASELINES = ("H0a", "H0b")
NUMBER_WORDS = {8: "eight", 9: "nine", 10: "ten"}


def how_many(count: int) -> str:
    return NUMBER_WORDS.get(count, str(count))


def role_names(evaluated: dict, year: int) -> dict[str, str]:
    """Outcome names with the two finalists of one election named."""
    finalists = evaluated["finalists"][year]
    return OUTCOME_NAMES | {
        role: f"{OUTCOME_NAMES[role]}: {name}" for role, name in finalists.items()
    }


def ladder(evaluated: dict, status: str) -> None:
    components.section(
        1,
        *SECTIONS[0],
        lead=f"Six rules give {how_many(len(MODEL_ORDER))} assumptions: two baselines, three "
        "proximity rules (H2 in two variants) and one mixture with a fitted parameter.",
    )
    with st.expander("Recall: what each assumption does"):
        components.assumption_list()
    example, year = evaluated["ladder"], evaluated["ladder_year"]
    rows = example["rows"]
    rows = rows.loc[[model for model in MODEL_ORDER if model in rows.index]]
    one_piece = rows.loc["H1"].max() > 99.9 and rows.loc["H2-abst", "abstention"] > 99.9
    components.figure_head(
        "H1 sends this whole group to one finalist; H2 sends all of it to a non-vote"
        if one_piece
        else "The same group, a different destination under each assumption",
        f"Where each assumption sends the first-round supporters of {example['group_name']} "
        f"in {year} ({fmt_pct(example['group_pct'])} of registered voters, the largest "
        "eliminated group), in % of that group.",
    )
    names = role_names(evaluated, year)
    components.outcome_key({role: names[role] for role in rows.columns})
    frame = pd.DataFrame(
        [
            {"row": model, "segment": role, "pct": float(rows.loc[model, role])}
            for model in rows.index
            for role in rows.columns
        ]
    )
    charts.stacked_rows(frame, names, "Share of the group (%)")
    a, b = example["finalist_scores"]
    components.source(
        "One row of each transfer matrix, pooled over areas. On the poll-based scale "
        f"(0 = left, 1 = right) this candidate scores {example['group_score']:.2f} and the "
        f"finalists {a:.2f} and {b:.2f}. "
        f"H3 uses the share p fitted with {year} held out. {status.capitalize()}. "
        "A rule about a group is an assumption, not an observed transfer."
    )


def comparison(evaluated: dict) -> None:
    table, result = evaluated["comparison"], answer(evaluated["comparison"])
    components.section(
        2,
        *SECTIONS[1],
        lead="The score is the average gap, per area, between an assumption's predicted "
        "second-round shares and the observed ones, in percentage points (pp). Lower is closer.",
    )
    years = election_columns(table)
    wide = table[[*years, "mean", "mean_without_2002"]].T
    wide.index = [*years, "Mean", "Mean without 2002"]
    wide = wide.rename_axis("Election").reset_index()
    components.figure_head(
        result["headline"],
        "Average error per area in pp, by election. The lowest value of each row is in bold.",
    )
    components.data_table(wide, {m: "{:.1f}" for m in table.index}, best="row")
    components.source(
        "Weighted average area error in percentage points; lower is closer. "
        "H3 scores are held-out: the share p is fitted on four elections and tested on "
        "the fifth. H2 is reported in both variants; neither is selected by fit."
    )
    components.note("What this table shows.", result["sentences"][0])


def errors(evaluated: dict) -> str:
    table, pooled = evaluated["comparison"], evaluated["errors"]
    best = table["mean"].idxmin()
    others = [m for m in MODEL_ORDER if m not in BASELINES]
    components.section(
        3,
        *SECTIONS[2],
        lead="The score hides the direction of an error. Here each bar is predicted minus "
        "observed for one outcome: above zero, the assumption predicts too much of it.",
    )
    focus = st.selectbox(
        "Assumption shown beside the two baselines",
        others,
        index=others.index(best) if best in others else 0,
        key="compare_model",
    )
    abstention = pooled[(pooled.model == "H0a") & (pooled.role == "abstention")].signed_error_pp
    years = pooled.year.nunique()
    components.figure_head(
        f"H0a predicts too much abstention in {count_of(int((abstention > 0).sum()), years)} "
        f"elections, by up to {fmt_pp(abstention.max())}",
        "Predicted minus observed share of registered voters, pooled over covered areas, in "
        "percentage points (pp). The largest gap of each assumption is outlined.",
    )
    components.outcome_key({role: OUTCOME_NAMES[role] for role in OUTCOME_NAMES if role != "other"})
    shown = pooled[pooled.model.isin([*BASELINES, focus])]
    reach = float(shown.signed_error_pp.abs().max())
    limits = (-charts.nice_max(reach, 10), charts.nice_max(reach, 10))
    for model in [*BASELINES, focus]:
        panel = shown[shown.model == model]
        components.html(
            f'<p class="panel-label"><strong>{components.escape(model)}</strong> '
            f"{components.escape(components.assumption_summary(model))}. Largest gap, outlined: "
            f"{components.escape(charts.largest_error(panel))}.</p>"
        )
        charts.signed_errors(panel, limits)
    components.source(
        "Predicted minus observed share of registered voters, pooled over covered areas. "
        "Above zero: the assumption predicts too much of that outcome. Finalist A is the "
        "first-round leader. These are aggregate patterns, not individual transfers."
    )
    return focus


def threshold(evaluated: dict) -> None:
    table = evaluated["threshold"]
    top = table.sort_values("exactly_on_threshold_pct", ascending=False).head(2).sort_values("year")
    peak = table.loc[table.exactly_on_threshold_pct.idxmax()]
    components.section(
        4,
        *SECTIONS[3],
        lead="H2 sends every group at least one third of the scale away from both finalists "
        "to a non-vote. How many voters that is depends on where the finalists sit on the scale.",
    )
    components.figure_head(
        f"In {join_years([str(y) for y in top.year])}, the threshold takes "
        f"{' and '.join(fmt_pct(v) for v in top.beyond_threshold_pct)} of registered voters "
        "away from both finalists",
        "First-round share of registered voters in eliminated groups at least one third of "
        "the scale away from both finalists, on the poll-based scale (0 = left, 1 = right), "
        "by election.",
    )
    charts.threshold_bars(table)
    components.source(
        "Source: first-round results and polling institutes' left-to-right orders; "
        "our calculations."
    )
    components.note(
        "Why this happens.",
        f"In {peak.year} the finalists score {peak.finalist_a_score:.2f} and "
        f"{peak.finalist_b_score:.2f}. A group exactly one third of the scale from the nearer "
        "finalist falls under the rule all at once: "
        f"{fmt_pct(peak.exactly_on_threshold_pct)} of registered voters. A rule with a "
        f"threshold decides between all and none. The threshold ({THRESHOLD:.2f} of the scale, "
        "the same share as our original rule of two steps out of six) was fixed before any "
        "result was computed and was not tuned afterwards.",
    )


def areas(evaluated: dict, focus: str) -> None:
    predictions, table = evaluated["predictions"], evaluated["comparison"]
    years = election_columns(table)
    components.section(
        5,
        *SECTIONS[4],
        lead="The score is an average over areas. This view shows every area behind it.",
    )
    left, right = st.columns(2)
    year = left.selectbox("Election", years, index=len(years) - 1, key="scatter_year")
    model = right.selectbox(
        "Assumption", list(MODEL_ORDER), index=list(MODEL_ORDER).index(focus), key="scatter_model"
    )
    frame = predictions[(predictions.year == int(year)) & (predictions.model == model)].copy()
    frame["actual_pct"], frame["predicted_pct"] = (
        frame.actual_share * 100,
        frame.predicted_share * 100,
    )
    frame["Area"] = frame.area_code
    frame["Territory"] = [
        "Metropolitan" if territory_type(code) == "metropolitan" else "Overseas or abroad"
        for code in frame.area_code
    ]
    components.figure_head(
        f"{model} in {year}: {fmt_pp(table.loc[model, year])} average error per area",
        "Predicted against observed share of registered voters. One point per area and "
        "outcome; on the dashed line the prediction equals the observation.",
    )
    components.outcome_key(
        {r: n for r, n in role_names(evaluated, int(year)).items() if r != "other"},
        extra=[
            ("shape-circle", "Metropolitan area"),
            ("shape-triangle", "Overseas area or voters abroad"),
        ],
    )
    charts.scatter(frame[["Area", "Territory", "role", "actual_pct", "predicted_pct"]])
    components.source(
        "Source: Ministry of the Interior; our calculations. The 2002 and 2007 files omit "
        "some overseas areas and voters abroad."
    )


def sensitivity(evaluated: dict) -> None:
    report, table = evaluated["report"], evaluated["sensitivity"]
    table = table[table.tie == "split"].set_index(["positions", "model"])
    codings = {
        "polls": "Poll-based scale, main",
        "primary": "Hand-coded families",
        "alternative": "Hand-coded, alternative families",
    }
    means = {coding: table.loc[coding] for coding in codings}
    main = means["polls"]
    best = main["mean"].idxmin()
    hand_best = means["primary"]["mean"].idxmin()
    components.section(
        6,
        *SECTIONS[5],
        lead="H1, H1-soft, H2 and H3 depend on where each candidate is placed. The main "
        "results use the poll-based scale. As a check, every assumption was rerun with our "
        "earlier hand-coded seven-family scale, then with its alternative families.",
    )
    frame = pd.DataFrame({"Assumption": main.index})
    formats = {}
    for coding, label in codings.items():
        frame[f"{label} (pp)"] = means[coding]["mean"].reindex(main.index).to_numpy()
        frame[f"Rank, {label.lower()}"] = means[coding]["rank"].reindex(main.index).to_numpy()
        formats[f"{label} (pp)"] = "{:.1f}"
    components.figure_head(
        f"{best} has the lowest average on the poll-based and on the hand-coded scale"
        if best == hand_best
        else f"The lowest average is {best} on the poll-based scale and {hand_best} on the "
        "hand-coded one",
        "Average error over the five elections in pp, and rank among the "
        f"{how_many(len(main))} assumptions, under each way of placing the candidates.",
    )
    components.data_table(frame, formats)
    ties = evaluated["ties"]
    components.source(
        "The hand-coded columns are comparisons, not the main results. The alternative "
        "coding moves all listed rows at once, finalists included: it is one alternative "
        "scenario, not a per-candidate analysis. "
        + (
            "No eliminated candidate is equidistant from both finalists under any coding, "
            "so the tie rule never applies."
            if ties.empty
            else f"{len(ties)} eliminated candidacies are equidistant from both finalists "
            "under at least one coding; they split evenly."
        )
        + f" {report['coding_status'].capitalize()}."
    )
    with st.expander("H3: fitted share per held-out election"):
        folds = [
            {
                "Base": fold["base"],
                "Tested on": str(fold["test_year"]),
                "Trained on": ", ".join(map(str, fold["train_elections"])),
                "Fitted p": fold["p"],
                "Held-out score (pp)": fold["heldout_score_pp"],
            }
            for fold in report["h3_folds"]
            if fold["variant"] == report["main_variant"] and fold["test_year"]
        ]
        st.dataframe(
            folds,
            hide_index=True,
            width="stretch",
            key="h3_folds",
            column_config={
                "Fitted p": st.column_config.NumberColumn(format="%.2f"),
                "Held-out score (pp)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.caption(
            "p is the share of each eliminated group that splits as in H0b instead of "
            "following the base rule. Each test election is never used to fit its own p."
        )


def single_election(ctx) -> None:
    components.section(
        7,
        *SECTIONS[6],
        lead="The original baseline, applied to one election and one area, with its "
        "calculation. H0a uses first-round shares only; second-round counts are not inputs.",
    )
    components.election_picker(ctx)
    if ctx.partial_coverage:
        st.info(
            "Coverage note: this historical file omits some overseas areas and voters abroad. "
            "Combined totals describe the covered areas, not all of France."
        )
    model = model_summary(ctx.selected_evaluation)
    roles = outcome_roles(ctx.results)
    frame = model["comparison"].assign(role=model["comparison"].option.map(roles))
    largest = frame.loc[frame.absolute_error_pp.idxmax()]
    components.figure_head(
        f"H0a is furthest from the observed result on "
        f"{largest.outcome if largest.option.startswith('candidate:') else largest.outcome.lower()}"
        f": {fmt_pp(largest.absolute_error_pp)} apart",
        f"Round 2, {ctx.year}, {ctx.area}. Share of registered voters. "
        "Solid bar: observed. Outlined bar: H0a.",
    )
    charts.observed_vs_model(frame, "H0a")
    components.source(
        "Source: Ministry of the Interior; our calculations. A close aggregate fit is not "
        "evidence of individual transfers."
    )
    components.note("What this comparison shows.", model["reading"])
    components.stat_row(
        [
            (
                "Weighted average area error",
                fmt_pp(model["weighted_mean_error_pp"]),
                "Four-outcome error calculated in each area, then weighted by round-two "
                "registration. This is the score used everywhere on this site.",
            ),
            (
                "Gap in combined results",
                fmt_pp(model["mean_error_pp"]),
                "Average gap after pooling results. Opposite local errors can cancel here.",
            ),
        ]
    )
    components.prose(
        f"Across {len(model['area_errors'])} selected reporting area(s), the weighted "
        f"average error is {fmt_pp(model['weighted_mean_error_pp'])}. "
        "Larger registered electorates carry more weight. The score follows the area filter; "
        "the full selection includes overseas areas and voters abroad when available."
    )
    with st.expander("A small worked example"):
        st.write(
            "Illustration only, not real election data. Imagine 100 registered "
            "voters: 30 support finalist A, 20 support finalist B, 25 support eliminated "
            "candidates, 5 cast blank/invalid ballots and 20 abstain."
        )
        st.write(
            "The four retained groups total 75. H0a divides the 25 eliminated "
            "supporters in the ratio 30:20:5:20. "
            "The output is A: 40%, B: 26.7%, blank/invalid: 6.7%, abstention: 26.7% (rounded)."
        )
        st.caption(
            "This is a behavioural assumption. It does not tell us what those 25 "
            "people actually did."
        )
    with st.expander("Exact comparison, area errors and calculation details"):
        table = model["comparison"][
            ["outcome", "actual_share", "predicted_share", "absolute_error_pp"]
        ].copy()
        table[["actual_share", "predicted_share"]] *= 100
        table.columns = ["Outcome", "Observed (%)", "H0a (%)", "Gap (pp)"]
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                c: st.column_config.NumberColumn(format="%.1f") for c in table.columns[1:]
            },
        )
        area_errors = model["area_errors"].merge(
            ctx.selected_evaluation[["department_code", "department_name"]].drop_duplicates(),
            on="department_code",
            validate="one_to_one",
        )
        area_errors = area_errors[["department_code", "department_name", "mean_error_pp", "weight"]]
        area_errors["weight"] *= 100
        area_errors.columns = ["Area code", "Area", "Average gap (pp)", "Weight (%)"]
        st.dataframe(
            area_errors.sort_values("Average gap (pp)", ascending=False),
            hide_index=True,
            width="stretch",
            column_config={
                "Average gap (pp)": st.column_config.NumberColumn(format="%.1f"),
                "Weight (%)": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.write(
            "Combined predictions are weighted by each area's round-two registered electorate. "
            "The main score first computes the mean absolute error across the four outcomes "
            "in each area, then weights those errors by registered voters. Errors in different "
            "areas cannot cancel. The combined-results gap is shown separately and can be smaller."
        )
        st.latex(
            r"\mathrm{Score}=\sum_d\frac{R_{d,2}}{\sum_j R_{j,2}}"
            r"\left[\frac{1}{4}\sum_k100\lvert\hat{s}_{d,k}-s_{d,k}\rvert\right]"
        )
        st.caption(
            "R is the round-two registered electorate. Weights sum to one within the "
            "selected covered areas; a filtered score is not a score for all of France."
        )
        st.latex(
            r"q_k = x_k / \sum_{t \in K} x_t,\quad "
            r"K=\{A,B,\mathrm{blank/invalid},\mathrm{abstention}\}"
        )
        st.caption(
            "x denotes first-round shares; q denotes H0a's second-round shares. "
            "The rule has no fitted parameters and does not mobilise first-round abstainers."
        )
        st.download_button(
            "Download H0a comparison (CSV)",
            model["comparison"].to_csv(index=False),
            file_name=f"h0_{ctx.year}_{ctx.unit.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    components.candidate_reference(ctx.year)


def render(ctx) -> None:
    components.page_header(
        f"How {how_many(len(MODEL_ORDER))} assumptions compare with five observed second rounds",
        "Every assumption predicts each area's second round from its first round. This page "
        "shows the rules, their scores, and where and why they miss.",
    )
    evaluated = ctx.evaluated
    if evaluated is None:
        st.info(
            "Cross-election results are not available in this data folder. "
            "Run `vote-transfer evaluate --all-models --all-years`."
        )
        single_election(ctx)
        return
    components.coding_banner(evaluated["report"])
    st.info(
        "Coverage note: the 2002 and 2007 files omit some overseas areas and voters "
        "abroad. Scores describe the covered areas of each election."
    )
    components.contents(SECTIONS)
    ladder(evaluated, evaluated["report"]["coding_status"])
    comparison(evaluated)
    focus = errors(evaluated)
    threshold(evaluated)
    areas(evaluated, focus)
    sensitivity(evaluated)
    single_election(ctx)
    components.glossary()
