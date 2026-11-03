"""A guided, offline-first introduction to the vote-transfer research project."""

import base64
from html import escape
from pathlib import Path

import streamlit as st
from vote_transfer.application.datasets import available_datasets, load_dataset
from vote_transfer.application.exploration import model_summary, round_summary
from vote_transfer.application.positions import load_candidate_positions, load_position_sources
from vote_transfer.application.source_catalog import SOURCES
from vote_transfer.config import data_root

PAGES = ("Home", "Explore", "Understand the model", "Sources & limits")
OBSERVED, MODEL = "#0071E3", "#E35D00"
SITE_DIR = Path(__file__).resolve().parent
LOGO_PATH = SITE_DIR / "assets" / "logo.svg"
LOGO_URI = "data:image/svg+xml;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")

st.set_page_config(page_title="Vote Transfer Lab", page_icon=str(LOGO_PATH), layout="wide")
st.markdown(f"<style>{(SITE_DIR / 'styles.css').read_text()}</style>", unsafe_allow_html=True)


def go_to(page):
    st.session_state["page"] = page


def intro(kicker, title, lead):
    """Centred page opening: short kicker, large headline, one supporting sentence."""
    st.markdown(
        f'<header class="intro"><p class="eyebrow">{escape(kicker)}</p>'
        f'<h1 class="intro-title">{escape(title)}</h1>'
        f'<p class="intro-lead">{escape(lead)}</p></header>',
        unsafe_allow_html=True,
    )


def section(title, lead=None):
    body = f'<p class="section-lead">{escape(lead)}</p>' if lead else ""
    st.markdown(
        f'<div class="section-head"><h2 class="section-title">{escape(title)}</h2>{body}</div>',
        unsafe_allow_html=True,
    )


def reading(text, title="How to read this"):
    st.markdown(
        f'<div class="reading"><strong>{escape(title)}</strong>{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def steps(items):
    for column, (number, title, body) in zip(
        st.columns(len(items), gap="large"), items, strict=True
    ):
        with column:
            st.markdown(
                f'<section class="step"><span class="step-number">{escape(number)}</span>'
                f"<h3>{escape(title)}</h3><p>{escape(body)}</p></section>",
                unsafe_allow_html=True,
            )


def glossary():
    with st.expander("A few useful definitions"):
        st.markdown(
            "**Registered voters** — everyone on the electoral roll, whether or not they voted.\n\n"
            "**Abstention** — a registered voter did not cast a ballot.\n\n"
            "**Blank or invalid ballot** — a ballot was cast but did not count for a candidate. "
            "We group these together for consistent comparisons across years.\n\n"
            "**Percentage point (pp)** — the difference between two percentages. "
            "A model share of 30% and an observed share of 25% differ by 5 percentage points.\n\n"
            "**Reporting area** — an area used in the official files: usually a department, "
            "but sometimes an overseas territory or the electorate abroad."
        )


def candidate_reference(year):
    with st.expander("Candidate parties and political families"):
        st.write(
            "Our manual reference links each candidate to their party at that election. "
            "The scale runs from 1 (Far left) to 7 (Far right), with Centre at 4. "
            "The team has agreed on this scale; the individual classifications are drafts "
            "for review. H0 does not use these scores."
        )
        try:
            positions = load_candidate_positions()
            sources = load_position_sources()
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
        st.dataframe(table, hide_index=True, width="stretch")
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
            source = sources[key]
            st.markdown(f"- [{source['title']}]({source['url']}) — {source['publisher']}")
        st.caption(
            "Sources document affiliations and background. The seven-category coding is "
            "our research choice, not an official classification."
        )


def bar_chart(frame, comparison=False, basis="registered voters"):
    """Label both marks and tooltips; colour is never the only source of meaning."""
    chart = frame.copy()
    if comparison:
        chart = chart.melt(
            id_vars="outcome",
            value_vars=["actual_share", "predicted_share"],
            var_name="series",
            value_name="value",
        )
        chart["value"] *= 100
        chart["series"] = chart.series.map(
            {"actual_share": "Observed result", "predicted_share": "H0 model"}
        )
    else:
        chart = chart.rename(columns={"share_pct": "value"})
        chart["series"] = "Observed result"
    chart["value_label"] = chart.value.map(lambda x: f"{x:.1f}%")
    order = frame.outcome.tolist()
    enc = {
        "y": {
            "field": "outcome",
            "type": "nominal",
            "sort": order,
            "axis": {
                "title": None,
                "labelLimit": 180,
                "labelFontSize": 12,
                "ticks": False,
                "domain": False,
            },
        },
        "x": {
            "field": "value",
            "type": "quantitative",
            "scale": {"domain": [0, min(100, max(10, float(chart.value.max()) * 1.2))]},
            "axis": {
                "title": f"Share of {basis} (%)",
                "tickCount": 5,
                "gridColor": "#ececf0",
            },
        },
        "color": {
            "field": "series",
            "type": "nominal",
            "scale": {"domain": ["Observed result", "H0 model"], "range": [OBSERVED, MODEL]},
            "legend": {"title": None, "orient": "top"} if comparison else None,
        },
        "tooltip": [
            {"field": "outcome", "title": "Outcome"},
            {"field": "series", "title": "Series"},
            {"field": "value_label", "title": f"Of {basis}"},
        ],
    }
    if comparison:
        enc["yOffset"] = {"field": "series", "sort": ["Observed result", "H0 model"]}
    spec = {
        "height": max(190, len(order) * (62 if comparison else 31)),
        "encoding": enc,
        "layer": [
            {"mark": {"type": "bar", "cornerRadiusEnd": 5, "size": 14 if comparison else 18}},
            {
                "mark": {
                    "type": "text",
                    "align": "left",
                    "dx": 5,
                    "fontSize": 11,
                    "color": "#1d1d1f",
                },
                "encoding": {"text": {"field": "value_label"}, "color": {"value": "#1d1d1f"}},
            },
        ],
        "config": {
            "view": {"stroke": None},
            "background": "transparent",
            "font": "-apple-system, BlinkMacSystemFont, Helvetica Neue, sans-serif",
            "axis": {
                "labelColor": "#6e6e73",
                "titleColor": "#6e6e73",
                "titleFontWeight": 500,
                "titlePadding": 15,
            },
            "legend": {"labelColor": "#1d1d1f", "labelFontSize": 12, "symbolType": "circle"},
        },
    }
    st.vega_lite_chart(chart, spec, width="stretch", theme=None)


def snapshot(results, year):
    summaries = [round_summary(results, n) for n in (1, 2)]
    finalists = summaries[1]["totals"].query("option.str.startswith('candidate:')", engine="python")
    keys = finalists.option.tolist()
    labels = finalists.outcome.tolist() + ["Other candidates", "Blank or invalid", "Did not vote"]
    colours = ["#0071E3", "#8E44D9", "#C7C7CC", "#6E6E73", "#E5E5EA"]
    bars, distributions = [], []
    for number, summary in enumerate(summaries, 1):
        table = summary["totals"].set_index("option")
        values = [float(table.loc[key, "share_pct"]) for key in keys]
        values += [
            float(
                table.loc[
                    table.index.str.startswith("candidate:") & ~table.index.isin(keys), "share_pct"
                ].sum()
            ),
            summary["blank_invalid_pct"],
            summary["abstention_pct"],
        ]
        distributions.append(values)
        segments = "".join(
            f'<span class="segment" style="width:{value:.6f}%;background:{colour}" '
            f'title="{escape(label)}: {value:.1f}%"></span>'
            for value, colour, label in zip(values, colours, labels, strict=True)
        )
        description = "; ".join(
            f"{label}: {value:.1f}%" for label, value in zip(labels, values, strict=True)
        )
        bars.append(
            f'<div class="round-label"><strong>Round {number}</strong><span>100% of '
            f"registered voters</span></div>"
            f'<div class="segment-bar" role="img" '
            f'aria-label="{escape(description)}">{segments}</div>'
        )
    legend = "".join(
        f'<tr><th scope="row"><i class="swatch" style="background:{colour}"></i>'
        f"{escape(label)}</th><td>{first:.1f}%</td><td>{second:.1f}%</td></tr>"
        for label, colour, first, second in zip(labels, colours, *distributions, strict=True)
    )
    st.markdown(
        f'<section class="snapshot"><p class="snapshot-kicker">Observed · {escape(year)}</p>'
        f"<h3>Two snapshots of an electorate.</h3><p>Same categories. Different results.</p>"
        f'{"".join(bars)}<table class="snapshot-table"><thead><tr>'
        '<th scope="col">Outcome</th><th scope="col">R1</th><th scope="col">R2</th>'
        f"</tr></thead><tbody>{legend}</tbody></table>"
        '<p class="snapshot-note">These are totals at each round. '
        "Each round uses its own registration total. They do not show how individual "
        "people moved between choices.</p></section>",
        unsafe_allow_html=True,
    )


datasets = available_datasets(data_root())
# Preserve an open session when upgrading from the sidebar navigation.
legacy_pages = {"Start here": "Home", "Explore results": "Explore"}
if st.session_state.get("page") in legacy_pages:
    st.session_state["page"] = legacy_pages[st.session_state["page"]]

with st.container(key="topbar"):
    brand_column, navigation_column, year_column, area_column = st.columns(
        [1.15, 3.3, 0.7, 1.6], gap="small", vertical_alignment="bottom"
    )
    with brand_column:
        st.markdown(
            f'<div class="brand"><img src="{LOGO_URI}" alt="" width="30" height="30">'
            '<span class="brand-wordmark">Vote Transfer <span>Lab</span></span></div>',
            unsafe_allow_html=True,
        )
    with navigation_column:
        page = st.radio(
            "Main navigation", PAGES, key="page", horizontal=True, label_visibility="collapsed"
        )
    with year_column:
        year = st.selectbox(
            "Year",
            list(datasets),
            key="year",
            disabled=not datasets,
            label_visibility="collapsed",
            help="Choose an election. Your selection applies on every page.",
        )
    area_slot = area_column.empty()

if not datasets:
    area_slot.selectbox("Area", [], disabled=True, label_visibility="collapsed")
    intro(
        "Vote Transfer Lab",
        "Welcome.",
        "French presidential elections, read round by round.",
    )
    st.info(
        "No processed election is available yet. Restore the bundled data or build an election."
    )
    st.code(
        "uv run vote-transfer acquire --year 2022\nuv run vote-transfer process --year 2022",
        language="bash",
    )
    st.stop()

try:
    results, evaluation, quality = load_dataset(datasets[year])
except (OSError, ValueError, KeyError) as error:
    area_slot.selectbox("Area", [], disabled=True, label_visibility="collapsed")
    st.error("This election could not be opened. Its data may be incomplete or modified.")
    with st.expander("Details for the project team"):
        st.code(str(error))
    st.stop()

units = (
    results[["department_code", "department_name"]].drop_duplicates().sort_values("department_code")
)
unit_labels = dict(zip(units.department_code, units.department_name, strict=True))
if st.session_state.get("unit", "All units") not in {"All units", *unit_labels}:
    st.session_state["unit"] = "All units"
with area_slot.container():
    unit = st.selectbox(
        "Area",
        ["All units", *unit_labels],
        key="unit",
        label_visibility="collapsed",
        help="Choose all covered areas or one reporting area, usually a department. "
        "Your selection applies on every page.",
        format_func=lambda x: (
            "All covered areas" if x == "All units" else f"{x} · {unit_labels[x]}"
        ),
    )

selected = results if unit == "All units" else results[results.department_code == unit]
selected_evaluation = (
    evaluation if unit == "All units" else evaluation[evaluation.department_code == unit]
)
area = "All covered areas" if unit == "All units" else f"{unit_labels[unit]} ({unit})"
partial_coverage = quality.get("partial_national_coverage") and unit == "All units"
if quality.get("partial_national_coverage") and page != "Explore":
    st.info(
        "Coverage note: this historical file omits some overseas areas and voters abroad. "
        "Combined totals describe the covered areas, not all of France."
    )

if page == "Home":
    st.markdown(
        '<header class="hero"><p class="eyebrow">French presidential elections · 2002–2022</p>'
        '<h1 class="hero-title">Two rounds. One electorate. <br><em>What changes?</em></h1>'
        '<p class="lead">When candidates leave the race, where might their support go? '
        "Explore official election results and test a simple explanation for the "
        "second round.</p></header>",
        unsafe_allow_html=True,
    )
    with st.container(horizontal=True, gap="small", key="hero_actions"):
        st.button(
            "Explore the results",
            type="primary",
            on_click=go_to,
            args=(PAGES[1],),
            key="start_explore",
        )
        st.button(
            "Understand the model ›",
            type="tertiary",
            on_click=go_to,
            args=(PAGES[2],),
            key="start_model",
        )
    with st.container(key="hero_visual"):
        snapshot(selected, year)
        st.caption(f"Your view: {year} · {area}. Change it using the menus at the top.")
    section("The project, in three steps.", "Observe. Explain. Check.")
    steps(
        [
            (
                "01 / OBSERVE",
                "Read the election",
                "In the elections studied here, voters first choose among all "
                "candidates. The two leading candidates then contest a second round.",
            ),
            (
                "02 / EXPLAIN",
                "Make an assumption",
                "We propose a rule for how support might be redistributed, including "
                "abstention and blank or invalid ballots.",
            ),
            (
                "03 / CHECK",
                "Compare with reality",
                "We compare the rule's output with the recorded second-round totals. "
                "A smaller gap means a closer fit, not proof of individual behaviour.",
            ),
        ]
    )
    section(
        "What are we trying to understand?",
        "Which assumptions about voter behaviour best explain second-round results in "
        "French presidential elections?",
    )
    reading(
        "We know the totals before and after the second round. We do not know how "
        "each person voted. "
        "This project tests explanations for aggregate patterns; it cannot track "
        "individual voters.",
        "The essential distinction",
    )
    st.caption(
        "Available now: five historical elections and one baseline model (H0). "
        "Additional hypotheses are planned."
    )
    glossary()

elif page == "Explore":
    intro(
        "Observe · official results",
        "Start with what happened.",
        "See how the registered electorate is distributed across candidates, blank or "
        "invalid ballots, and abstention.",
    )
    st.markdown(f'<p class="context-pill">{escape(f"{year} · {area}")}</p>', unsafe_allow_html=True)
    round_number = st.radio(
        "Which round?", [1, 2], format_func=lambda n: f"Round {n}", horizontal=True, key="round"
    )
    summary = round_summary(selected, round_number)
    if partial_coverage:
        st.warning(
            f"**Not national totals.** The {year} source file omits voters abroad and some "
            "overseas areas. These totals cover only the areas in the file, so turnout and "
            "candidate figures differ slightly from official national results, for example "
            "those reported on Wikipedia."
        )
    a, b, c = st.columns(3)
    a.metric(
        "Registered voters",
        f"{summary['registered']:,}",
        help="Everyone on the electoral roll in the selected areas and round.",
    )
    b.metric(
        "Cast a ballot",
        f"{summary['turnout_pct']:.1f}%",
        help="Includes valid, blank and invalid ballots.",
    )
    c.metric(
        "Did not vote",
        f"{summary['abstention_pct']:.1f}%",
        help="Abstention as a share of registered voters.",
    )
    basis = st.radio(
        "Show percentages of",
        ["Registered voters", "Valid votes"],
        captions=["Used by our models", "As usually reported"],
        horizontal=True,
        key="basis",
    )
    if basis == "Valid votes":
        st.subheader(f"Round {round_number} · out of 100 valid votes")
        st.caption(
            "The usual way results are reported: each candidate's share of ballots cast "
            "for a candidate. Abstention and blank or invalid ballots are left out, so "
            "this view cannot show the whole electorate."
        )
        candidates = summary["totals"].dropna(subset=["valid_share_pct"])
        bar_chart(candidates.assign(share_pct=candidates.valid_share_pct), basis="valid votes")
        leader = candidates.iloc[0]
        reading(
            f"Of every 100 valid votes in this selection, {leader.outcome} received about "
            f"{leader.valid_share_pct:.1f}. Out of all registered voters, the same votes are "
            f"{leader.share_pct:.1f}%."
        )
    else:
        st.subheader(f"Round {round_number} · out of 100 registered voters")
        st.caption(
            "Each bar uses the full registered electorate, which our models need because "
            "abstention and blank ballots are outcomes too. Switch to valid votes to compare "
            "with the shares usually quoted in election coverage."
        )
        bar_chart(summary["totals"])
        reading(summary["reading"])
    with st.expander("See exact figures and download the data"):
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
                "Registered electorate (%)": st.column_config.NumberColumn(format="%.2f"),
                "Valid votes (%)": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.download_button(
            "Download this round (CSV)",
            selected[selected["round"] == round_number].to_csv(index=False),
            file_name=f"election_{year}_{unit.replace(' ', '_')}_round_{round_number}.csv",
            mime="text/csv",
        )
    glossary()
    st.button(
        "Next: can a simple model explain round two? →",
        on_click=go_to,
        args=(PAGES[2],),
        type="primary",
    )

elif page == "Understand the model":
    intro(
        "Explain & check · H0 baseline",
        "One simple rule. A measurable gap.",
        "A model is an explicit assumption we can test. H0 is our starting rule, called a "
        "baseline: more elaborate explanations will need to improve on it.",
    )
    steps(
        [
            (
                "INPUT",
                "Begin with round one",
                "Use each area's first-round shares and the identities of the two "
                "finalists. Second-round vote counts are not inputs.",
            ),
            (
                "ASSUMPTION",
                "Redistribute proportionally",
                "Supporters of eliminated candidates split in proportion to the "
                "first-round sizes of the two finalists, blank/invalid voters and abstainers.",
            ),
            (
                "COMPARISON",
                "Check round two",
                "The model retains the other groups in their original choices. "
                "Compare its four output shares with the observed second-round shares.",
            ),
        ]
    )
    with st.expander("Walk through a small example"):
        st.write(
            "Illustration only — not real election data. Imagine 100 registered "
            "voters: 30 support finalist A, "
            "20 support finalist B, 25 support eliminated candidates, 5 cast "
            "blank/invalid ballots and 20 abstain."
        )
        st.write(
            "The four retained groups total 75. H0 divides the 25 eliminated "
            "supporters in the ratio 30:20:5:20. "
            "The output is A: 40%, B: 26.7%, blank/invalid: 6.7%, abstention: 26.7% (rounded)."
        )
        st.caption(
            "This is a behavioural assumption. It does not tell us what those 25 "
            "people actually did."
        )
    section("How close does H0 get?")
    st.caption(f"Round 2 · {year} · {area} · share of registered voters")
    model = model_summary(selected_evaluation)
    bar_chart(model["comparison"], comparison=True)
    reading(model["reading"], "What this comparison shows")
    a, b = st.columns(2)
    a.metric(
        "Weighted average area error",
        f"{model['weighted_mean_error_pp']:.2f} pp",
        help="Four-outcome error calculated in each area, then weighted by round-two registration.",
    )
    b.metric(
        "Gap in combined results",
        f"{model['mean_error_pp']:.2f} pp",
        help="Average gap after pooling results. Opposite local errors can cancel here.",
    )
    st.write(
        f"Across {len(model['area_errors'])} selected reporting area(s), the weighted "
        f"average error is {model['weighted_mean_error_pp']:.2f} percentage points. "
        "Larger registered electorates carry more weight. The score follows the area filter; "
        "the full selection includes overseas areas and voters abroad when available."
    )
    st.caption(
        "pp = percentage points. For example, 30% versus 25% is a gap of 5 points. "
        "Closer to zero means a closer fit; it does not establish the true voter-transfer pattern."
    )
    with st.expander("Exact comparison, area errors and calculation details"):
        table = model["comparison"][
            ["outcome", "actual_share", "predicted_share", "absolute_error_pp"]
        ].copy()
        table[["actual_share", "predicted_share"]] *= 100
        table.columns = ["Outcome", "Observed (%)", "H0 (%)", "Gap (pp)"]
        st.dataframe(table, hide_index=True, width="stretch")
        errors = model["area_errors"].merge(
            selected_evaluation[["department_code", "department_name"]].drop_duplicates(),
            on="department_code",
            validate="one_to_one",
        )
        errors = errors[["department_code", "department_name", "mean_error_pp", "weight"]]
        errors["weight"] *= 100
        errors.columns = ["Area code", "Area", "Average gap (pp)", "Weight (%)"]
        st.dataframe(
            errors.sort_values("Average gap (pp)", ascending=False),
            hide_index=True,
            width="stretch",
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
            "x denotes first-round shares; q denotes H0's second-round shares. "
            "The rule has no fitted parameters and does not mobilise first-round abstainers."
        )
        st.download_button(
            "Download H0 comparison (CSV)",
            model["comparison"].to_csv(index=False),
            file_name=f"h0_{year}_{unit.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    st.warning(
        "A close aggregate fit is not evidence of individual transfers. H0 is a "
        "provisional baseline; H1–H5 have not yet been implemented."
    )
    candidate_reference(year)
    st.button("Next: check the sources and limitations →", on_click=go_to, args=(PAGES[3],))

else:
    intro(
        "Verify · sources & limitations",
        "Know what sits behind the numbers.",
        "The figures come from original French Ministry of the Interior polling-station files. "
        "We check the counts, aggregate them by reporting area, then calculate the "
        "same outcomes for every election.",
    )
    st.subheader(f"Your selected source · {year}")
    for source in SOURCES:
        if source.key.startswith(f"official_{year}_"):
            st.link_button(
                f"Original Ministry dataset · round {source.key[-1]}", source.landing_url
            )
    st.caption(
        "The 2002–2012 source files contain both rounds together. Links for those "
        "rounds lead to the same dataset."
    )
    st.subheader("Four things to keep in mind")
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
        "4. **H0 is a starting assumption.** It has not been compared with H1–H5. "
        "A future 2027 feature will explore hypothetical scenarios, not forecast an election."
    )
    if quality.get("geographic_labels") == "codes_only":
        st.info(
            "This year's source does not provide department names. We display its "
            "original reporting-area codes rather than attach unverified modern names."
        )
    with st.expander("Data checks and reproducibility"):
        st.write(
            f"This build contains {quality['polling_station_round_rows']:,} "
            f"polling-station/round records "
            f"across {quality['territorial_units']} reporting areas."
        )
        st.write(
            "Checks cover source-file integrity, duplicate records, nonnegative "
            "counts, turnout accounting, "
            "candidate vote totals and matching area coverage between rounds."
        )
        st.caption(
            "Using a bundled aggregate snapshot."
            if datasets[year].parent.name == "bundled"
            else "Using a complete local processed dataset."
        )
        st.code(
            f"uv run vote-transfer acquire --year {year}\nuv run vote-transfer process "
            f"--year {year}",
            language="bash",
        )
        st.json(quality, expanded=False)
    with st.expander("What comes next in the research?"):
        st.markdown(
            "- Compare historical results against the consolidated reference dataset.\n"
            "- Review the manual candidate positions and define ties and distance thresholds "
            "before testing ideological explanations (H1/H2).\n"
            "- Define and review the methods for noise, strategic voting and learned "
            "transfers (H3–H5).\n"
            "- Evaluate fitted methods on held-out elections before developing 2027 scenarios."
        )
    candidate_reference(year)
    glossary()
    st.caption(
        "AI assisted with development, documentation and tests. The project team is "
        "responsible for source verification, methodological decisions and interpretation."
    )

st.markdown(
    '<footer class="footer"><p class="footer-note">Observed totals. Explicit assumptions. '
    "No individual voting histories.</p><p>Vote Transfer Lab · Historical election research "
    "· French presidential elections 2002–2022</p></footer>",
    unsafe_allow_html=True,
)
