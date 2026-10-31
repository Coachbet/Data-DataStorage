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
                department_code="01",
                option="abstention",
                label="Abstention",
                registered=100,
                actual_share=0.1,
                predicted_share=0.2,
            ),
            dict(
                year=2022,
                department_code="02",
                option="abstention",
                label="Abstention",
                registered=300,
                actual_share=0.5,
                predicted_share=0.6,
            ),
        ]
    )

    def complete_outcomes(abstentions):
        rows = []
        for row in abstentions.to_dict("records"):
            rows.append(row)
            for candidate in ("a", "b"):
                rows.append(
                    {
                        **row,
                        "option": f"candidate:{candidate}",
                        "label": candidate,
                        "actual_share": (1 - row["actual_share"]) / 2,
                        "predicted_share": (1 - row["predicted_share"]) / 2,
                    }
                )
            rows.append(
                {
                    **row,
                    "option": "blank_invalid",
                    "label": "Blank/invalid",
                    "actual_share": 0,
                    "predicted_share": 0,
                }
            )
        return pd.DataFrame(rows)

    summary = model_summary(complete_outcomes(evaluation))
    assert summary["mean_error_pp"] == pytest.approx(5)
    assert summary["weighted_mean_error_pp"] == pytest.approx(5)
    assert "50.0% versus an observed 40.0%" in summary["reading"]
    assert "10.0 percentage points above" in summary["reading"]
    evaluation["predicted_share"] = evaluation.actual_share - 0.05
    assert "5.0 percentage points below" in model_summary(complete_outcomes(evaluation))["reading"]
