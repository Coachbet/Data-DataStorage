"""The website in site/: it starts offline on the bundled snapshots and every page renders."""

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

SITE = Path(__file__).resolve().parents[1] / "site"
APP = SITE / "app.py"


def load_nav():
    spec = importlib.util.spec_from_file_location("site_nav", SITE / "nav.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["site_nav"] = module
    spec.loader.exec_module(module)
    return module


NAV = load_nav()


@pytest.fixture
def offline(tmp_path, monkeypatch):
    """Bundled snapshots only, with HTTP blocked: a fresh clone, offline."""
    shutil.copytree(SITE.parent / "data/bundled", tmp_path / "bundled")
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))

    def reject_network(*args, **kwargs):
        raise AssertionError("The site must not make HTTP requests.")

    monkeypatch.setattr("requests.Session.request", reject_network)


def test_every_page_in_the_table_of_contents_has_a_view_with_render():
    keys = [page.key for page in NAV.PAGES]
    assert len(keys) == len(set(keys))
    assert [page.number for page in NAV.PAGES] == list(range(1, len(keys) + 1))
    assert sum(page.url == "" for page in NAV.PAGES) == 1  # exactly one home page
    anchors = [anchor for page in NAV.PAGES for anchor, _ in page.sections]
    assert len(anchors) == len(set(anchors))
    for key in keys:
        assert (SITE / "views" / f"{key}.py").is_file(), key


def test_app_starts_offline_on_the_bundled_snapshots(offline):
    app = AppTest.from_file(str(APP)).run(timeout=120)
    assert not app.exception


PAGE_SCRIPT = """
import importlib
import sys

sys.path.insert(0, {site!r})
import ui

ui.setup()
importlib.import_module("views.{key}").render()
"""


@pytest.mark.parametrize("key", [page.key for page in NAV.PAGES])
def test_every_page_renders_without_error(offline, key):
    app = AppTest.from_string(PAGE_SCRIPT.format(site=str(SITE), key=key)).run(timeout=180)
    assert not app.exception, [e.value for e in app.exception]
    if key == "report":  # the final report is shown as a PDF, with download buttons
        labels = [button.label for button in app.get("download_button")]
        assert "Download the report (PDF)" in labels
    else:
        assert len(app.markdown) > 3  # the page has real content, not only its frame
