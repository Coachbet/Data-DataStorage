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
