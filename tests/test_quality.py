from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.datasets import load_dataset
from vote_transfer.application.processing import process_year
from vote_transfer.application.quality import (
    iqr_outliers,
    station_diagnostics,
    territory_type,
    unit_flags,
)
from vote_transfer.infrastructure.official import parse_official

BUNDLED = Path(__file__).resolve().parents[1] / "data" / "bundled"


def test_iqr_flags_extreme_value_that_inflates_zscore():
    # The course example: one extreme value hides itself from a z-score rule.
    values = pd.Series([10, 10, 11, 10, 12, 11, 100])
    assert abs((values - values.mean()) / values.std()).max() < 3
    assert iqr_outliers(values).tolist() == [False] * 6 + [True]


def test_territory_codes():
    assert [territory_type(c) for c in ("01", "2A", "ZA", "ZZ")] == [
        "metropolitan",
        "metropolitan",
        "overseas",
        "abroad",
    ]


def test_station_diagnostics_measure_synthetic_fixture(raw_dataset):
    path = raw_dataset / "raw" / "official" / "2022" / "round_1.txt"
    turnout, votes = parse_official(path, 2022, 1)
    report = station_diagnostics(turnout, votes)["1"]
    assert report["station_rows"] == 2
    assert report["completeness_required_fields_pct"] == 100
    assert report["completeness_blank_invalid_split_pct"] == 100
    assert report["duplicate_station_keys"] == 0


def test_flags_retain_every_real_area():
    results, evaluation, _ = load_dataset(BUNDLED / "2022")
    flags = unit_flags(results, evaluation)
    assert len(flags) == results.department_code.nunique() == 107
    assert set(flags.territory) == {"metropolitan", "overseas", "abroad"}
    assert flags.registration_change_pct.abs().max() < 1
    # Overseas areas are unusual on abstention, but flagged rather than removed.
    flagged = set(flags.loc[flags.flag_abstention_r1, "department_code"])
    assert {"ZA", "ZZ"} <= flagged


def test_processing_report_lists_derived_fields_and_diagnostics(raw_dataset):
    report = process_year(2022, raw_dataset)
    assert report["derived_fields"] == {"blank_invalid": "blank + invalid"}
    assert "voters <= registered and valid <= voters" in report["checks"]
    assert set(report["diagnostics"]["stations_by_round"]) == {"1", "2"}
    assert report["diagnostics"]["reporting_units"]["response"].startswith("flag and retain")


@pytest.mark.parametrize("year", [2002, 2007, 2012, 2017, 2022])
def test_flags_run_on_every_bundled_election(year):
    flags = unit_flags(*load_dataset(BUNDLED / str(year))[:2])
    assert flags[["abstention_r1", "h0_mean_error_pp"]].notna().all().all()
