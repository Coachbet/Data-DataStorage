"""Vote Transfer: the question, the evidence and the data, offline."""

from types import SimpleNamespace

import components
import loaders
import streamlit as st
from views import answer, evidence, explore, method
from vote_transfer.application.datasets import available_datasets, snapshot_drift
from vote_transfer.config import data_root

VIEWS = {
    "Home": answer,
    "Evidence": evidence,
    "Explore the data": explore,
    "Method & sources": method,
}
PAGES = tuple(VIEWS)
st.set_page_config(page_title="Vote Transfer", page_icon=str(components.LOGO_PATH), layout="wide")
components.inject_styles()

root = data_root()
datasets = available_datasets(root)
page = components.navigation(PAGES)

if not datasets:
    components.page_header(
        "No election data in this folder yet",
        "The site reads processed election tables; none was found.",
    )
    st.info(
        "No processed election is available yet. Restore the bundled data or build an election."
    )
    st.code(
        "uv run vote-transfer acquire --year 2022\nuv run vote-transfer process --year 2022",
        language="bash",
    )
    st.stop()

year = components.remembered("year", list(datasets), next(iter(datasets)))
try:
    results, evaluation, quality = loaders.dataset(datasets[year])
except (OSError, ValueError, KeyError) as error:
    st.error("This election could not be opened. Its data may be incomplete or modified.")
    with st.expander("Details for the project team"):
        st.code(str(error))
    st.stop()

stale_snapshots = snapshot_drift(root)
if stale_snapshots:
    st.warning(
        "Local processed data differ from the bundled snapshots ("
        + ", ".join(stale_snapshots)
        + "). This app shows the local build; a fresh clone would show the snapshots. "
        "Run `vote-transfer bundle --all-years` to align them."
    )

units = (
    results[["department_code", "department_name"]].drop_duplicates().sort_values("department_code")
)
unit_labels = dict(zip(units.department_code, units.department_name, strict=True))
unit = components.remembered("unit", ["All units", *unit_labels], "All units")
everything = unit == "All units"

VIEWS[page].render(
    SimpleNamespace(
        root=root,
        datasets=datasets,
        year=year,
        unit=unit,
        unit_labels=unit_labels,
        results=results,
        selected=results if everything else results[results.department_code == unit],
        selected_evaluation=(
            evaluation if everything else evaluation[evaluation.department_code == unit]
        ),
        quality=quality,
        area="all covered areas" if everything else f"{unit_labels[unit]} ({unit})",
        partial_coverage=bool(quality.get("partial_national_coverage")),
        evaluated=loaders.evaluated(root),
    )
)
components.footer()
