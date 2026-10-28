import pandas as pd
import pytest
from vote_transfer.application.exploration import model_summary, round_summary
from vote_transfer.application.processing import process_year


def test_round_reading_uses_registered_voters_and_selected_round(raw_dataset):
    process_year(2022, raw_dataset)
    results = pd.read_parquet(raw_dataset / "processed/2022/department_results.parquet")
    summary = round_summary(results, 1)
    assert summary["registered"] == 300
    assert summary["turnout_pct"] == 80
    assert summary["abstention_pct"] == 20
    assert summary["blank_invalid_pct"] == 5
    assert summary["totals"].share_pct.sum() == pytest.approx(100)
    assert "80.0 voted and 20.0 did not" in summary["reading"]
    second = round_summary(results[results.department_code == "01"], 2)
    assert second["registered"] == 100
    assert len(second["totals"]) == 4


def test_model_reading_reports_direction_and_weighted_gap():
    evaluation = pd.DataFrame(
        [
            dict(
                year=2022,
                option="abstention",
                label="Abstention",
                registered=100,
                actual_share=0.1,
                predicted_share=0.2,
            ),
            dict(
                year=2022,
                option="abstention",
                label="Abstention",
                registered=300,
                actual_share=0.5,
                predicted_share=0.6,
            ),
        ]
    )
    summary = model_summary(evaluation)
    assert summary["mean_error_pp"] == pytest.approx(10)
    assert "50.0% versus an observed 40.0%" in summary["reading"]
    assert "10.0 percentage points above" in summary["reading"]
    evaluation["predicted_share"] = evaluation.actual_share - 0.05
    assert "5.0 percentage points below" in model_summary(evaluation)["reading"]
