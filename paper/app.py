"""Where do the voters of eliminated candidates go? The paper site.

Run from the repository root:  uv run streamlit run paper/app.py
It reads the versioned snapshots only, so it works offline on a fresh clone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

import ui  # noqa: E402
from views import data_page, explore, hypotheses, intro, method, report, results  # noqa: E402

st.set_page_config(
    page_title="Where do eliminated voters go?",
    page_icon="🗳️",
    layout="centered",
)
ui.setup()

pages = [
    st.Page(intro.render, title="Introduction", default=True),
    st.Page(data_page.render, title="Data", url_path="data"),
    st.Page(hypotheses.render, title="Hypotheses", url_path="hypotheses"),
    st.Page(results.render, title="Results", url_path="results"),
    st.Page(explore.render, title="Explore", url_path="explore"),
    st.Page(method.render, title="Method & limits", url_path="method"),
    st.Page(report.render, title="Report", url_path="report"),
]
st.navigation(pages, position="top").run()
ui.footer()
