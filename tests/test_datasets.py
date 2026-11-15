import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.datasets import (
    available_datasets,
    build_predictions,
    bundle_predictions,
    bundle_year,
    load_dataset,
    load_predictions,
    snapshot_drift,
    stale_predictions,
)
from vote_transfer.application.evaluation import score_predictions, weighted_area_error
from vote_transfer.application.positions import REFERENCE_DIR
from vote_transfer.application.processing import process_year


def test_bundle_survives_removal_of_all_raw_and_processed_data(raw_dataset):
    process_year(2022, raw_dataset)
    report = bundle_year(2022, raw_dataset)
    assert report["bytes"] < 100_000
    shutil.rmtree(raw_dataset / "raw")
    shutil.rmtree(raw_dataset / "interim")
    shutil.rmtree(raw_dataset / "processed")
    folder = available_datasets(raw_dataset)["2022"]
    assert folder.parent.name == "bundled"
    results, evaluation, quality = load_dataset(folder)
    assert len(results) == 18
    assert len(evaluation) == 8
    assert quality["year"] == 2022


def test_complete_local_build_takes_precedence(raw_dataset):
    process_year(2022, raw_dataset)
    bundle_year(2022, raw_dataset)
    assert available_datasets(raw_dataset)["2022"].parent.name == "processed"


def test_bundle_export_rejects_corruption_without_replacing_previous_copy(raw_dataset):
    process_year(2022, raw_dataset)
    bundle_year(2022, raw_dataset)
    bundle = raw_dataset / "bundled/2022/outcomes.parquet"
    previous = bundle.read_bytes()
    (raw_dataset / "processed/2022/outcomes.parquet").write_bytes(b"bad data")
    with pytest.raises(ValueError, match="do not match"):
        bundle_year(2022, raw_dataset)
    assert bundle.read_bytes() == previous


@pytest.mark.parametrize("year", [2002, 2007, 2012, 2017, 2022])
def test_shipped_snapshot_reproduces_h0_from_aggregate_inputs(year):
    from pathlib import Path

    import pandas as pd
    from vote_transfer.application.baseline import evaluate_h0

    root = Path(__file__).resolve().parents[1] / "data" / "bundled" / str(year)
    results, stored, _ = load_dataset(root)
    reproduced = evaluate_h0(results)
    pd.testing.assert_frame_equal(reproduced, stored)


def test_snapshot_drift_names_files_that_differ_between_processed_and_bundled(raw_dataset):
    assert snapshot_drift(raw_dataset) == []  # nothing to compare yet
    process_year(2022, raw_dataset)
    assert snapshot_drift(raw_dataset) == []  # only one copy exists
    bundle_year(2022, raw_dataset)
    assert snapshot_drift(raw_dataset) == []
    stale = raw_dataset / "bundled/2022/outcomes.parquet"
    stale.write_bytes(stale.read_bytes() + b"x")
    assert snapshot_drift(raw_dataset) == ["2022/outcomes.parquet"]


# --- One long predictions table ---------------------------------------------------------

BUNDLED = Path(__file__).resolve().parents[1] / "data" / "bundled"


@pytest.fixture
def five_elections(tmp_path):
    """A data root holding only copies of the five bundled election snapshots."""
    for folder in BUNDLED.glob("[0-9][0-9][0-9][0-9]"):
        shutil.copytree(folder, tmp_path / "bundled" / folder.name)
    return tmp_path


def test_cross_election_evaluation_needs_all_five_elections(raw_dataset):
    process_year(2022, raw_dataset)
    with pytest.raises(ValueError, match="every election"):
        build_predictions(raw_dataset)
    assert load_predictions(raw_dataset) is None
    assert not stale_predictions(raw_dataset)


def test_predictions_are_written_once_verified_and_bundled(five_elections):
    summary = build_predictions(five_elections)
    assert summary["coding_status"] == "draft coding"
    predictions, report = load_predictions(five_elections)
    assert len(predictions) == summary["rows"] == report["rows"]
    assert set(report["inputs"]["elections"]) == {"2002", "2007", "2012", "2017", "2022"}
    assert not stale_predictions(five_elections)
    bundle_predictions(five_elections)
    assert snapshot_drift(five_elections) == []
    shutil.rmtree(five_elections / "processed")
    pd.testing.assert_frame_equal(load_predictions(five_elections)[0], predictions)


def test_modified_predictions_are_rejected(five_elections):
    build_predictions(five_elections)
    path = five_elections / "processed/predictions.parquet"
    frame = pd.read_parquet(path)
    frame.loc[0, "predicted_share"] += 0.01
    frame.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="do not match"):
        load_predictions(five_elections)
    with pytest.raises(ValueError, match="do not match"):
        bundle_predictions(five_elections)


def test_editing_the_candidate_table_marks_predictions_stale(five_elections, tmp_path):
    reference = tmp_path / "reference"
    shutil.copytree(REFERENCE_DIR, reference)
    build_predictions(five_elections, reference)
    assert not stale_predictions(five_elections, reference)
    table = reference / "candidate_positions.csv"
    table.write_text(table.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert stale_predictions(five_elections, reference)


def test_shipped_predictions_are_reproduced_from_the_shipped_inputs(five_elections):
    build_predictions(five_elections)
    rebuilt, report = load_predictions(five_elections)
    shipped, shipped_report = load_predictions(BUNDLED.parent)
    pd.testing.assert_frame_equal(rebuilt, pd.read_parquet(BUNDLED / "predictions.parquet"))
    bundled_report = json.loads((BUNDLED / "evaluation_report.json").read_text())
    assert report["h3_folds"] == bundled_report["h3_folds"]
    assert shipped_report["coding_status"] == "draft coding" and len(shipped)


def test_scores_from_the_long_table_match_the_per_election_h0a(five_elections):
    build_predictions(five_elections)
    predictions, _ = load_predictions(five_elections)
    scores = score_predictions(predictions).set_index(["model", "variant", "year"]).score_pp
    for year in (2002, 2007, 2012, 2017, 2022):
        _, evaluation, _ = load_dataset(BUNDLED / str(year))
        expected = weighted_area_error(evaluation).weighted_mae_pp.iloc[0]
        assert scores.loc[("H0a", "default", year)] == pytest.approx(expected, abs=1e-12)
