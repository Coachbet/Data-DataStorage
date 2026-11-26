"""Where do the voters of eliminated candidates go? The project website.

Run from the repository root:  make app  (or uv run streamlit run site/app.py)
It reads the versioned snapshots only, so it works offline on a fresh clone.
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

import nav  # noqa: E402
import ui  # noqa: E402

st.set_page_config(
    page_title="Where do eliminated voters go?",
    page_icon="🗳️",
    layout="centered",
    initial_sidebar_state="expanded",
)
ui.setup()


def _page(p: nav.Page) -> st.Page:
    module = importlib.import_module(f"views.{p.key}")
    kwargs = {"title": f"{p.number}. {p.title}", "icon": p.icon}
    if p.url:
        kwargs["url_path"] = p.url
    else:
        kwargs["default"] = True
    return st.Page(module.render, **kwargs)


pages = {p.key: _page(p) for p in nav.PAGES}
current = st.navigation(list(pages.values()), position="hidden")
current_key = next(k for k, pg in pages.items() if pg.title == current.title)
ui.sidebar(pages, current_key)
current.run()
ui.pager(pages, current_key)
ui.footer()
