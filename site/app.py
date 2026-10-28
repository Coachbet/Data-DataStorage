"""English Streamlit frontend; all calculations live in the Python backend."""

import streamlit as st
from vote_transfer.application.baseline import national_evaluation
from vote_transfer.application.datasets import available_datasets, load_dataset
from vote_transfer.application.project_overview import get_project_overview
from vote_transfer.application.source_catalog import SOURCES
from vote_transfer.config import data_root

st.set_page_config(page_title="Vote Transfer Lab", page_icon="◈", layout="wide")

st.caption("FRENCH PRESIDENTIAL ELECTIONS  /  RESEARCH WORKSPACE")
st.title("Vote Transfer Lab")
st.write(get_project_overview()["research"]["question"])
st.caption("Observed results → explicit assumptions → measured errors")

root = data_root()
datasets = available_datasets(root)

with st.sidebar:
    st.header("Research controls")
    st.caption("Original Ministry files · registered-voter shares")

if not datasets:
    st.info("No processed election is available yet. Build the first dataset with these commands.")
    st.code(
        "uv run vote-transfer acquire --year 2022\nuv run vote-transfer process --year 2022",
        language="bash",
    )
    st.write(
        "The app reads validated local outputs. Acquisition runs separately from the interface."
    )
    st.stop()

with st.sidebar:
    year = st.selectbox("Election year", list(datasets))

folder = datasets[year]
st.caption(
    "Versioned aggregate snapshot · no download required"
    if folder.parent.name == "bundled"
    else "Locally processed original data"
)
try:
    results, evaluation, quality = load_dataset(folder)
except (OSError, ValueError) as error:
    st.error(f"Cannot read the processed election: {error}")
    st.stop()

if quality.get("partial_national_coverage"):
    st.info(
        "This historical file omits some overseas areas and voters abroad. "
        "Totals and model errors describe the covered units, not all of France."
    )

units = (
    results[["department_code", "department_name"]].drop_duplicates().sort_values("department_code")
)
unit_labels = dict(zip(units.department_code, units.department_name, strict=True))
with st.sidebar:
    unit = st.selectbox(
        "Geographic coverage",
        ["All units", *unit_labels],
        format_func=lambda value: (
            "All covered reporting units"
            if value == "All units"
            else f"{value} · {unit_labels[value]}"
        ),
    )
    st.divider()
    st.markdown("**Model status**")
    st.markdown("H0 · implemented\n\nH1–H5 · research backlog")
    st.caption("2027 is a future scenario exercise, not an election forecast.")

selected = results if unit == "All units" else results[results.department_code == unit]
selected_evaluation = (
    evaluation if unit == "All units" else evaluation[evaluation.department_code == unit]
)
comparison = national_evaluation(selected_evaluation)

round_two = selected[selected["round"] == 2]
registered = round_two.drop_duplicates("department_code").registered.sum()
abstentions = round_two.loc[round_two.option == "abstention", "count"].sum()
a, b, c, d = st.columns(4)
a.metric("Registered voters · round 2", f"{registered:,.0f}")
b.metric("Turnout · round 2", f"{(1 - abstentions / registered) * 100:.2f}%")
c.metric("Reporting units", selected.department_code.nunique())
d.metric("H0 mean absolute error", f"{comparison.absolute_error_pp.mean():.2f} pp")

explorer, model, provenance = st.tabs(
    ["Explore results", "Test assumption H0", "Data & methodology"]
)

with explorer:
    st.subheader("Where the registered electorate voted")
    round_number = st.radio("Election round", [1, 2], horizontal=True)
    current = selected[selected["round"] == round_number]
    totals = current.groupby(["option", "label"], as_index=False)["count"].sum()
    denominator = current.drop_duplicates("department_code").registered.sum()
    totals["Share of registered voters (%)"] = totals["count"] / denominator * 100
    totals = totals.sort_values("count", ascending=False)
    st.bar_chart(
        totals.set_index("label")[["Share of registered voters (%)"]],
        color="#246B61",
        horizontal=True,
    )
    st.dataframe(
        totals.rename(columns={"label": "Outcome", "count": "Votes / people"}).drop(
            columns="option"
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Share of registered voters (%)": st.column_config.NumberColumn(format="%.2f")
        },
    )
    st.caption(
        "Blank and invalid ballots form one model outcome. Abstention is included in the "
        "denominator."
    )
    st.download_button(
        "Download selected results (CSV)",
        selected.to_csv(index=False),
        file_name=f"election_{year}_{unit.replace(' ', '_')}.csv",
        mime="text/csv",
    )

with model:
    st.subheader("H0 · proportional redistribution")
    st.write(
        "Finalist supporters, abstainers and blank/invalid voters retain their option. "
        "Eliminated candidates' support is redistributed in proportion to those four groups' "
        "first-round shares. This is the initial operational definition of the naive baseline."
    )
    st.caption(
        "Finalist identities are known for retrospective evaluation; second-round vote shares "
        "never enter H0."
    )
    chart = comparison.set_index("label")[["actual_share", "predicted_share"]] * 100
    chart.columns = ["Observed (%)", "H0 (%)"]
    st.bar_chart(chart, stack=False, color=["#246B61", "#D39552"])
    table = comparison[["label", "actual_share", "predicted_share", "absolute_error_pp"]].copy()
    table[["actual_share", "predicted_share"]] *= 100
    table.columns = ["Outcome", "Observed (%)", "H0 (%)", "Absolute error (pp)"]
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(
        "The combined comparison weights unit predictions by round-two registered voters. "
        "Mean absolute error averages the four outcome errors. This differs from averaging "
        "unit errors."
    )
    with st.expander("Inspect errors by reporting unit"):
        errors = selected_evaluation.groupby(
            ["department_code", "department_name"], as_index=False
        ).absolute_error_pp.mean()
        st.dataframe(
            errors.sort_values("absolute_error_pp", ascending=False),
            hide_index=True,
            width="stretch",
        )
    st.warning("These are aggregate model outputs. Individual vote transfers are not observed.")

with provenance:
    st.subheader("Trace every result to its source")
    st.write(f"Built at {quality['processed_at_utc']} from original Ministry files.")
    st.write(f"Validated {quality['polling_station_round_rows']:,} polling-station/round records.")
    st.caption(
        "Reporting units preserve Ministry codes and include overseas territories and voters "
        "abroad. "
        "They are not all French departments. No historical geographic harmonisation is claimed."
    )
    for source in SOURCES:
        with st.expander(source.name):
            st.write(source.purpose)
            st.caption(source.notes)
            st.link_button("Open source", source.landing_url)
    with st.expander("Quality report and source checksums"):
        st.json(quality)
    if quality.get("ballot_detail") == "combined_only":
        st.info(
            "This historical source reports blank and invalid ballots together. "
            "Their separate counts are unavailable. Department labels show original codes."
        )
    st.subheader("Next research steps")
    st.markdown(
        "1. Compare historical results with the consolidated reference and audit coverage.\n"
        "2. Document candidate-to-party mappings and CHES positions for H1 and H2.\n"
        "3. Confirm fitting methods for H3/H5 and use election-level held-out evaluation.\n"
        "4. Study 2017 preference data for H4/H5 before building the 2027 scenario interface."
    )
    st.caption(
        "AI assistance: repository organisation, implementation, documentation and automated "
        "checks. "
        "The project team remains responsible for source verification and methodological decisions."
    )
