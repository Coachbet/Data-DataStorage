from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from vote_transfer.application.processing import process_year
from vote_transfer.application.scenario import SCENARIO_MODELS

APP = Path(__file__).resolve().parents[1] / "site" / "app.py"


def test_empty_state_without_local_data(tmp_path, monkeypatch):
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "No processed election" in app.info[0].value


def test_loaded_app_filters_round_and_territory(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert not app.metric  # The introduction is not a wall of statistics.
    assert not app.sidebar.radio
    assert not app.sidebar.selectbox
    assert app.radio(key="page").options == [
        "Home",
        "Explore",
        "Understand the model",
        "Compare models",
        "2027 scenarios",
        "Sources & limits",
    ]
    assert app.radio(key="page").proto.horizontal
    assert app.selectbox(key="year").label == "Year"
    assert app.selectbox(key="unit").label == "Area"
    app.button(key="start_explore").click().run()
    assert not app.exception
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


def test_shipped_five_year_app_runs_without_raw_data_or_network(tmp_path, monkeypatch):
    import shutil

    shutil.copytree(APP.parent.parent / "data/bundled", tmp_path / "bundled")
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))

    def reject_network(*args, **kwargs):
        raise AssertionError("The offline app must not make HTTP acquisition requests.")

    monkeypatch.setattr("requests.Session.request", reject_network)
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert set(app.selectbox(key="year").options) == {"2002", "2007", "2012", "2017", "2022"}
    app.button(key="start_explore").click().run()
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
            assert any("82.1" in item.value for item in app.markdown)
            app.radio(key="basis").set_value("Registered voters").run()
        app.radio(key="page").set_value("Understand the model").run()
        assert not app.exception
        assert app.metric[0].label == "Weighted average area error"
        assert app.metric[1].label == "Gap in combined results"
        candidates = app.dataframe[-1].value
        assert len(candidates) == {"2002": 16, "2007": 12, "2012": 10, "2017": 11, "2022": 12}[year]
        assert "Score (1–7)" in candidates
        assert any(
            button.label == "Download all candidate positions (CSV)"
            for button in app.get("download_button")
        )
        app.radio(key="page").set_value("Sources & limits").run()
        assert not app.exception
        assert len(app.get("link_button")) == 2
        app.radio(key="page").set_value("Home").run()
        assert not app.exception
        app.button(key="start_explore").click().run()
        app.radio(key="round").set_value(2).run()
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()


def test_navigation_preserves_area_and_handles_unavailable_area_after_year_change(
    tmp_path, monkeypatch
):
    import shutil

    shutil.copytree(APP.parent.parent / "data/bundled", tmp_path / "bundled")
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    app.selectbox(key="year").select("2017").run()
    app.selectbox(key="unit").select("ZZ").run()
    for page in ["Explore", "Understand the model", "Sources & limits", "Home"]:
        app.radio(key="page").set_value(page).run()
        assert not app.exception
        assert app.selectbox(key="unit").value == "ZZ"
        assert app.selectbox(key="year").value == "2017"
    app.selectbox(key="year").select("2002").run()
    assert not app.exception
    assert app.selectbox(key="unit").value == "All units"


def test_exploration_charts_have_valid_vega_schema(raw_dataset, monkeypatch):
    import altair as alt
    import streamlit as st

    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    original = st.vega_lite_chart
    specs = []

    def validated_chart(data, spec, **kwargs):
        alt.LayerChart.from_dict({**spec, "data": {"values": data.to_dict("records")}})
        specs.append(spec)
        return original(data, spec, **kwargs)

    monkeypatch.setattr(st, "vega_lite_chart", validated_chart)
    app = AppTest.from_file(str(APP)).run(timeout=20)
    app.button(key="start_explore").click().run()
    assert not app.exception
    app.radio(key="page").set_value("Understand the model").run()
    assert not app.exception
    assert len(specs) == 2


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


def test_compare_page_shows_every_model_with_honesty_notes(offline_app):
    app = offline_app
    app.radio(key="page").set_value("Compare models").run(timeout=30)
    assert not app.exception
    table = app.dataframe[0].value
    assert table.Model.tolist() == [
        "H0a",
        "H0b",
        "H1",
        "H2-abst",
        "H2-blank",
        "H3(H1)",
        "H3(H2-abst)",
        "H3(H2-blank)",
    ]
    assert {"2002", "2007", "2012", "2017", "2022", "Mean", "Mean without 2002"} <= set(table)
    assert round(table.set_index("Model").loc["H0a", "2022"], 2) == 6.12
    assert any("Draft coding" in item.value for item in app.warning)
    assert any("not individual transfers" in item.value for item in app.warning)
    assert any("2002 and 2007" in item.value for item in app.info)
    assert app.selectbox(key="compare_model").value == table.loc[table.Mean.idxmin(), "Model"]
    app.selectbox(key="compare_model").select("H2-blank").run(timeout=30)
    assert not app.exception
    folds = app.dataframe[1].value
    assert len(folds) == 15 and set(folds["Tested on"]) == {"2002", "2007", "2012", "2017", "2022"}


def test_scenario_page_works_offline_with_permanent_banner(offline_app):
    app = offline_app
    app.radio(key="page").set_value("2027 scenarios").run(timeout=30)
    assert not app.exception

    def banner():
        return [item.value for item in app.warning if "not a forecast" in item.value]

    assert banner() and "2022 electorate" in banner()[0] and "Draft coding" in banner()[0]
    assert app.selectbox(key="scenario_a").value == "candidate:emmanuel-macron"
    assert app.selectbox(key="scenario_b").value == "candidate:marine-le-pen"
    # Team decision: H0b is the default, with the reason stated on the page.
    assert app.selectbox(key="scenario_model").value == "H0b"
    assert any("H0b is the default" in c.value and "2002" in c.value for c in app.caption)
    assert any("candidates only" in c.value and "no map" in c.value for c in app.caption)
    national = app.dataframe[0].value
    assert list(national.columns) == ["Outcome", "H0b (%)"]
    assert national["H0b (%)"].sum() == pytest.approx(100)
    app.checkbox(key="scenario_all").check().run(timeout=30)
    assert not app.exception and banner()
    national = app.dataframe[0].value
    assert list(national.columns) == ["Outcome", *(f"{m} (%)" for m in SCENARIO_MODELS)]
    assert national.drop(columns="Outcome").sum().tolist() == pytest.approx([100] * 8)
    app.checkbox(key="scenario_all").uncheck().run(timeout=30)
    assert national.Outcome.tolist()[:2] == ["Emmanuel Macron", "Marine Le Pen"]
    assert len(app.dataframe[1].value) == 107  # area-level table
    assert any(b.label == "Download this scenario (CSV)" for b in app.get("download_button"))

    app.selectbox(key="scenario_b").select("candidate:jean-luc-melenchon").run(timeout=30)
    app.selectbox(key="scenario_model").select("H3(H1)").run(timeout=30)
    assert not app.exception and banner()
    national = app.dataframe[0].value
    assert national.Outcome.tolist()[:2] == ["Emmanuel Macron", "Jean-Luc Mélenchon"]
    assert list(national.columns) == ["Outcome", "H3(H1) (%)", "H0b (%)"]
    assert any("fitted on the five historical elections" in c.value for c in app.caption)

    app.selectbox(key="scenario_model").select("H0b").run(timeout=30)
    assert list(app.dataframe[0].value.columns) == ["Outcome", "H0b (%)"]
    app.selectbox(key="scenario_b").select("candidate:emmanuel-macron").run(timeout=30)
    assert not app.exception and banner()
    assert any("two different candidates" in item.value for item in app.error)


def test_new_pages_explain_missing_evaluation_instead_of_failing(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    for page in ("Compare models", "2027 scenarios"):
        app.radio(key="page").set_value(page).run(timeout=20)
        assert not app.exception
        assert any("vote-transfer evaluate" in item.value for item in app.info)
    assert any("not a forecast" in item.value for item in app.warning)


def test_signed_error_chart_has_a_valid_vega_schema(offline_app, monkeypatch):
    import altair as alt
    import streamlit as st

    original = st.vega_lite_chart
    specs = []

    def validated_chart(data, spec, **kwargs):
        if "facet" in spec:
            alt.FacetChart.from_dict({**spec, "data": {"values": data.to_dict("records")}})
            specs.append((spec, data))
        return original(data, spec, **kwargs)

    monkeypatch.setattr(st, "vega_lite_chart", validated_chart)
    offline_app.radio(key="page").set_value("Compare models").run(timeout=30)
    assert not offline_app.exception
    ((spec, data),) = specs
    assert set(data.model) == {"H0a", "H0b", offline_app.selectbox(key="compare_model").value}
    assert len(data) == 3 * 5 * 4  # three models, five elections, four outcomes
