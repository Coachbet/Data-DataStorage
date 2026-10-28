import pandas as pd
import pytest
from vote_transfer.application.baseline import evaluate_h0, national_evaluation, predict_h0
from vote_transfer.application.processing import process_year


def test_h0_uses_first_round_only_and_conserves_mass():
    inputs = {
        "candidate:a": 0.3,
        "candidate:b": 0.2,
        "candidate:c": 0.25,
        "blank_invalid": 0.05,
        "abstention": 0.2,
    }
    prediction = predict_h0(inputs, ("candidate:a", "candidate:c"))
    assert prediction == pytest.approx(
        {"candidate:a": 0.375, "candidate:c": 0.3125, "blank_invalid": 0.0625, "abstention": 0.25}
    )
    assert sum(prediction.values()) == pytest.approx(1)
    assert inputs["candidate:b"] == 0.2


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1, 0.9])
def test_h0_rejects_invalid_input(bad):
    with pytest.raises(ValueError):
        predict_h0(
            {"candidate:a": bad, "candidate:b": 0.4, "blank_invalid": 0.1, "abstention": 0.1},
            ("candidate:a", "candidate:b"),
        )


def test_h0_requires_positive_retained_mass():
    with pytest.raises(ValueError, match="positive"):
        predict_h0(
            {
                "candidate:a": 0,
                "candidate:b": 0,
                "candidate:c": 1,
                "blank_invalid": 0,
                "abstention": 0,
            },
            ("candidate:a", "candidate:b"),
        )


def test_missing_second_round_unit_is_rejected(raw_dataset):
    process_year(2022, raw_dataset)
    results = pd.read_parquet(raw_dataset / "processed/2022/department_results.parquet")
    results = results[~((results["round"] == 2) & (results.department_code == "2A"))]
    with pytest.raises(ValueError, match="same territorial units"):
        evaluate_h0(results)


def test_national_aggregation_uses_registration_weights():
    data = pd.DataFrame(
        [
            dict(
                year=2022,
                option="x",
                label="X",
                registered=100,
                actual_share=0.1,
                predicted_share=0.2,
            ),
            dict(
                year=2022,
                option="x",
                label="X",
                registered=300,
                actual_share=0.5,
                predicted_share=0.6,
            ),
        ]
    )
    result = national_evaluation(data).iloc[0]
    assert result.actual_share == pytest.approx(0.4)
    assert result.predicted_share == pytest.approx(0.5)
    assert result.absolute_error_pp == pytest.approx(10)
