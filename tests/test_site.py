from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from vote_transfer.application.processing import process_year

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
    app.button(key="start_explore").click().run()
    assert not app.exception
    assert app.metric[0].value == "300"
    app.sidebar.selectbox[1].select("01").run()
    assert not app.exception
    assert app.metric[0].value == "100"
    app.radio(key="round").set_value(2).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 4


def test_app_rejects_modified_processed_outputs(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    path = raw_dataset / "processed/2022/department_results.parquet"
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
    assert set(app.sidebar.selectbox[0].options) == {"2002", "2007", "2012", "2017", "2022"}
    app.button(key="start_explore").click().run()
    app.radio(key="round").set_value(2).run()
    for year, registered in {
        "2002": "40,463,551",
        "2007": "43,320,654",
        "2012": "46,066,215",
        "2017": "47,568,693",
        "2022": "48,752,339",
    }.items():
        app.sidebar.selectbox[0].select(year).run()
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
        app.sidebar.radio(key="page").set_value("Understand the model").run()
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
        app.sidebar.radio(key="page").set_value("Sources & limits").run()
        assert not app.exception
        assert len(app.get("link_button")) == 2
        app.sidebar.radio(key="page").set_value("Start here").run()
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
    app.sidebar.selectbox(key="unit").select("ZZ").run()
    app.button(key="start_model").click().run()
    assert not app.exception
    assert app.sidebar.selectbox(key="unit").value == "ZZ"
    app.sidebar.selectbox(key="year").select("2002").run()
    assert not app.exception
    assert app.sidebar.selectbox(key="unit").value != "ZZ"


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
    app.sidebar.radio(key="page").set_value("Understand the model").run()
    assert not app.exception
    assert len(specs) == 2
