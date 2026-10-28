import shutil

import pytest
from vote_transfer.application.datasets import available_datasets, bundle_year, load_dataset
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
    bundle = raw_dataset / "bundled/2022/department_results.parquet"
    previous = bundle.read_bytes()
    (raw_dataset / "processed/2022/department_results.parquet").write_bytes(b"bad data")
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
