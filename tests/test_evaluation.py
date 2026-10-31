import pandas as pd
import pytest
from vote_transfer.application.baseline import national_evaluation
from vote_transfer.application.evaluation import area_errors, weighted_area_error


@pytest.fixture
def territorial_evaluation():
    rows = []
    for code, registered, delta in [("01", 100, 0.2), ("02", 300, -0.1)]:
        for option, actual, predicted in [
            ("candidate:a", 0.5, 0.5 + delta),
            ("candidate:b", 0.25, 0.25 - delta),
            ("blank_invalid", 0.05, 0.05),
            ("abstention", 0.2, 0.2),
        ]:
            rows.append(
                dict(
                    year=2022,
                    department_code=code,
                    registered=registered,
                    option=option,
                    label=option,
                    actual_share=actual,
                    predicted_share=predicted,
                )
            )
    return pd.DataFrame(rows)


def test_weighted_errors_do_not_cancel_and_count_electorates_once(territorial_evaluation):
    errors = area_errors(territorial_evaluation)
    assert errors.mean_error_pp.tolist() == pytest.approx([10, 5])
    assert errors.weight.tolist() == pytest.approx([0.25, 0.75])
    score = weighted_area_error(territorial_evaluation).iloc[0]
    assert score.weighted_mae_pp == pytest.approx(6.25)
    assert score.registered == 400
    assert score.territorial_units == 2
    pooled = national_evaluation(territorial_evaluation).absolute_error_pp.mean()
    assert pooled == pytest.approx(1.25)


def test_filters_renormalise_weights_and_elections_are_separate(territorial_evaluation):
    first = territorial_evaluation[territorial_evaluation.department_code == "01"]
    result = weighted_area_error(first).iloc[0]
    assert result.weighted_mae_pp == pytest.approx(10)
    assert result.registered == 100
    combined = pd.concat([territorial_evaluation, first.assign(year=2017)])
    result = weighted_area_error(combined).set_index("year")
    assert result.loc[2017, "weighted_mae_pp"] == pytest.approx(10)
    assert result.loc[2022, "weighted_mae_pp"] == pytest.approx(6.25)


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "weights", "nan", "shares"])
def test_weighted_score_rejects_incomplete_or_inconsistent_data(territorial_evaluation, corruption):
    data = territorial_evaluation.copy()
    if corruption == "missing":
        data = data.iloc[1:]
    elif corruption == "duplicate":
        data = pd.concat([data, data.iloc[[0]]])
    elif corruption == "weights":
        data.loc[0, "registered"] = 150
    elif corruption == "nan":
        data.loc[0, "predicted_share"] = float("nan")
    else:
        data.loc[0, "predicted_share"] = 0.1
    with pytest.raises(ValueError):
        weighted_area_error(data)
