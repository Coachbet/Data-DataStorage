from pathlib import Path

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
    assert app.metric[0].value == "300"
    app.sidebar.selectbox[1].select("01").run()
    assert not app.exception
    assert app.metric[0].value == "100"
    app.radio[0].set_value(2).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 4


def test_app_rejects_modified_processed_outputs(raw_dataset, monkeypatch):
    process_year(2022, raw_dataset)
    monkeypatch.setenv("VOTE_TRANSFER_DATA_DIR", str(raw_dataset))
    path = raw_dataset / "processed/2022/department_results.parquet"
    path.write_bytes(b"corrupt")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "do not match" in app.error[0].value


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
        if year in ("2002", "2007"):
            assert any("not all of France" in item.value for item in app.info)
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()
