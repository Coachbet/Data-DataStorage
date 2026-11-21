from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from vote_transfer.application.processing import process_year

PAGES = ["The answer", "Evidence", "Explore the data", "Method & sources"]
MODELS = [
    "H0a",
    "H0b",
    "H1",
    "H1-soft",
    "H2-abst",
    "H2-blank",
    "H3(H1)",
    "H3(H2-abst)",
    "H3(H2-blank)",
]
APP = Path(__file__).resolve().parents[1] / "site" / "app.py"


def test_empty_state_without_local_data(tmp_path, monkeypatch):
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "No processed election" in app.info[0].value


def go(app, page, timeout=30):
    app.radio(key="page").set_value(page).run(timeout=timeout)
    assert not app.exception
    return app


def page_text(app) -> str:
    """Everything a reader can read on the page, as one string."""
    parts = [*app.markdown, *app.warning, *app.info, *app.caption, *app.error]
    return " ".join(item.value for item in parts)


def validate_charts(monkeypatch) -> list:
    """Check every chart against the Vega-Lite schema as it is drawn; return the specs."""
    import altair as alt
    import streamlit as st

    original = st.vega_lite_chart
    drawn = []

    def validated_chart(data, spec, **kwargs):
        alt.LayerChart.from_dict({**spec, "data": {"values": data.to_dict("records")}})
        drawn.append((spec, data))
        return original(data, spec, **kwargs)

    monkeypatch.setattr(st, "vega_lite_chart", validated_chart)
    return drawn


def test_loaded_app_filters_round_and_territory(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert not app.metric  # The first page is not a wall of statistics.
    assert not app.sidebar.radio
    assert not app.sidebar.selectbox
    assert app.radio(key="page").options == PAGES
    assert app.radio(key="page").proto.horizontal
    assert not app.selectbox  # Pickers appear only on the pages they change.
    go(app, "Explore the data")
    assert app.selectbox(key="year").label == "Election"
    assert app.selectbox(key="unit").label == "Area"
    assert app.metric[0].value == "300"
    app.selectbox(key="unit").select("01").run()
    assert not app.exception
    assert app.metric[0].value == "100"
    app.radio(key="round").set_value(2).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 4


def test_app_rejects_modified_processed_outputs(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    path = raw_dataset / "processed/2022/outcomes.parquet"
    path.write_bytes(b"corrupt")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "could not be opened" in app.error[0].value
    assert any("do not match" in code.value for code in app.code)


def test_shipped_five_year_app_runs_without_raw_data_or_network(offline_app):
    app = go(offline_app, "Explore the data")
    assert set(app.selectbox(key="year").options) == {"2002", "2007", "2012", "2017", "2022"}
    app.radio(key="round").set_value(2).run()
    for year, registered in {
        "2002": "40,463,551",
        "2007": "43,320,654",
        "2012": "46,066,215",
        "2017": "47,568,693",
        "2022": "48,752,339",
    }.items():
        app.selectbox(key="year").select(year).run()
        assert not app.exception
        assert app.metric[0].value == registered
        coverage = [item.value for item in app.warning if "Not national totals" in item.value]
        assert bool(coverage) == (year in ("2002", "2007"))
        if year == "2002":
            app.radio(key="basis").set_value("Valid votes").run()
            assert not app.exception
            figures = app.dataframe[0].value.set_index("Outcome")
            assert round(figures.loc["Jacques Chirac", "Valid votes (%)"], 2) == 82.14
            assert figures["Valid votes (%)"].sum() == pytest.approx(100)
            assert "82.1" in page_text(app)
            app.radio(key="basis").set_value("Registered voters").run()
        go(app, "Evidence")
        assert app.metric[0].label == "Weighted average area error"
        assert app.metric[1].label == "Gap in combined results"
        candidates = app.dataframe[-1].value
        assert len(candidates) == {"2002": 16, "2007": 12, "2012": 10, "2017": 11, "2022": 12}[year]
        assert "Score (1–7)" in candidates
        assert any(
            button.label == "Download all candidate positions (CSV)"
            for button in app.get("download_button")
        )
        go(app, "Method & sources")
        assert app.selectbox(key="year").value == year
        assert f"Original Ministry dataset, {year}" in page_text(app)
        go(app, "Explore the data")
        assert app.radio(key="round").value == 2 or app.radio(key="round").set_value(2).run()


def test_pickers_keep_their_value_across_pages_and_recover_from_a_missing_area(offline_app):
    app = go(offline_app, "Explore the data")
    app.selectbox(key="year").select("2017").run()
    app.selectbox(key="unit").select("ZZ").run()
    for page in ["The answer", "Evidence", "Explore the data"]:
        go(app, page)
    assert app.selectbox(key="unit").value == "ZZ"
    assert app.selectbox(key="year").value == "2017"
    app.selectbox(key="year").select("2002").run()
    assert not app.exception
    assert app.selectbox(key="unit").value == "All units"


def test_every_chart_on_every_page_has_a_valid_vega_schema(offline_app, monkeypatch):
    drawn = validate_charts(monkeypatch)
    counts = {}
    for page in PAGES:
        before = len(drawn)
        go(offline_app, page)
        counts[page] = len(drawn) - before
    assert counts["The answer"] == 1  # one chart carries the answer
    assert counts["Evidence"] >= 7 and counts["Explore the data"] == 2
    assert counts["Method & sources"] == 0
    for spec, _ in drawn:
        assert "layer" in spec and "facet" not in spec


def test_signed_error_panels_cover_both_baselines_and_the_chosen_assumption(
    offline_app, monkeypatch
):
    drawn = validate_charts(monkeypatch)
    app = go(offline_app, "Evidence")
    panels = [data for _, data in drawn if "signed_error_pp" in data]
    assert [set(panel.model) for panel in panels] == [
        {"H0a"},
        {"H0b"},
        {app.selectbox(key="compare_model").value},
    ]
    for panel in panels:
        assert len(panel) == 5 * 4  # five elections, four outcomes
        assert panel.largest.sum() == 1  # the outlined bar is the one named in words
    worst = panels[0].loc[panels[0].largest].iloc[0]
    assert f"{worst.signed_error_pp:+.1f}".replace("-", "−") in page_text(app)


def test_app_warns_when_processed_and_bundled_copies_differ(raw_dataset, monkeypatch):
    from vote_transfer.application.datasets import bundle_year

    process_year(2022, raw_dataset)
    bundle_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not any("differ from the bundled" in item.value for item in app.warning)
    stale = raw_dataset / "bundled/2022/outcomes.parquet"
    stale.write_bytes(stale.read_bytes() + b"x")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert any("differ from the bundled" in item.value for item in app.warning)


@pytest.fixture
def offline_app(tmp_path, monkeypatch):
    """The app on bundled snapshots only, with HTTP blocked: a fresh clone, offline."""
    import shutil

    shutil.copytree(APP.parent.parent / "data/bundled", tmp_path / "bundled")
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))

    def reject_network(*args, **kwargs):
        raise AssertionError("The offline app must not make HTTP requests.")

    monkeypatch.setattr("requests.Session.request", reject_network)
    return AppTest.from_file(str(APP)).run(timeout=30)


def test_answer_page_states_the_answer_from_the_generated_results(offline_app):
    import json

    from vote_transfer.application.presentation import fmt_pp

    app = offline_app
    assert app.radio(key="page").value == "The answer"
    numbers = json.loads((APP.parent.parent / "reports/results/numbers.json").read_text())
    text = page_text(app)
    assert "Which assumptions about voter behaviour best explain" in text
    assert "No assumption explains every election best." in text
    for model in ("H1", "H0b", "H0a"):
        assert fmt_pp(numbers[f"score.{model}.mean"]) in text
    assert not app.metric and not app.selectbox
    status = app.warning[0].value
    for phrase in ("Poll-based scale", "polling", "[PENDING", "2002 and 2007", "not individual"):
        assert phrase in status
    app.button(key="finding_1").click().run(timeout=30)
    assert not app.exception
    assert app.radio(key="page").value == "Evidence"


def test_evidence_page_shows_every_model_with_honesty_notes(offline_app):
    app = go(offline_app, "Evidence")
    table = app.table[0].value.set_index("Election")
    assert list(table.columns) == MODELS
    assert list(table.index) == [
        "2002",
        "2007",
        "2012",
        "2017",
        "2022",
        "Mean",
        "Mean without 2002",
    ]
    assert round(table.loc["2022", "H0a"], 2) == 6.12
    assert any("Poll-based scale" in item.value for item in app.warning)
    assert any("not individual transfers" in item.value for item in app.warning)
    assert any("2002 and 2007" in item.value for item in app.info)
    assert app.selectbox(key="compare_model").value == table.loc["Mean"].idxmin()
    app.selectbox(key="compare_model").select("H2-blank").run(timeout=30)
    assert not app.exception
    sensitivity = app.table[1].value
    assert sensitivity.Assumption.tolist() == MODELS
    folds = app.dataframe[0].value
    assert len(folds) == 15 and set(folds["Tested on"]) == {"2002", "2007", "2012", "2017", "2022"}


def test_method_page_keeps_the_limits_and_the_disclosure_sentence(offline_app):
    app = go(offline_app, "Method & sources")
    text = page_text(app)
    assert "Totals are not personal voting histories" in text
    assert "an order, not a measured ideological distance" in text
    assert any(
        c.value == "AI assisted with development, documentation and tests. The project team is "
        "responsible for source verification, methodological decisions and interpretation."
        for c in app.caption
    )


def test_every_page_says_results_are_aggregate_not_individual(offline_app):
    for page in PAGES:
        assert "not individual transfers" in page_text(go(offline_app, page))


def test_pages_explain_missing_evaluation_instead_of_failing(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    for page in ("The answer", "Evidence"):
        go(app, page, timeout=20)
        assert any("vote-transfer evaluate" in item.value for item in app.info)


def test_text_colours_meet_wcag_aa_on_the_page_background():
    import sys

    sys.path.insert(0, str(APP.parent))
    import theme

    def luminance(colour):
        channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast(a, b):
        hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    c = theme.COLOUR
    for name in ("ink", "muted", "accent", "accent-strong"):
        assert contrast(c[name], c["paper"]) >= 4.5, name
        assert contrast(c[name], c["wash"]) >= 4.5, name
    assert contrast(c["note-ink"], c["note-bg"]) >= 4.5
    assert contrast("#FFFFFF", c["accent"]) >= 4.5
    for role, (_, outline) in theme.OUTCOME.items():
        assert contrast(outline, c["paper"]) >= 3, role  # non-text marks
