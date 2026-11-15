"""Transfer-matrix models on explicitly synthetic elections, plus invariants on real ones."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from vote_transfer.application.baseline import predict_h0
from vote_transfer.application.datasets import load_dataset
from vote_transfer.application.evaluation import weighted_area_error
from vote_transfer.application.models import (
    BASES,
    MAIN_VARIANT,
    P_GRID,
    build_election,
    election_scores,
    evaluate_models,
    fit_p,
    mix,
    predict,
    primary_score,
    proximity_row,
    transfer_matrix,
    transfer_tensor,
)
from vote_transfer.application.positions import load_candidate_positions

BUNDLED = Path(__file__).resolve().parents[1] / "data" / "bundled"
YEARS = (2002, 2007, 2012, 2017, 2022)
A, B, BLANK, ABST = np.eye(4)


def synthetic_results(year=2022, second=None, areas=(("01", 100), ("02", 300))):
    """Two areas; a and b are finalists; c, d and e are eliminated. Not real data."""
    first = {
        "candidate:a": 30,
        "candidate:b": 20,
        "candidate:c": 10,
        "candidate:d": 10,
        "candidate:e": 5,
        "blank_invalid": 5,
        "abstention": 20,
    }
    second = second or {"candidate:a": 45, "candidate:b": 30, "blank_invalid": 5, "abstention": 20}
    rows = []
    for code, registered in areas:
        for round_number, counts in ((1, first), (2, second)):
            for option, per_hundred in counts.items():
                rows.append(
                    dict(
                        year=year,
                        round=round_number,
                        department_code=code,
                        option=option,
                        label=option,
                        count=per_hundred * registered // 100,
                        department_name=f"Synthetic {code}",
                        registered=registered,
                        polling_stations=1,
                        share=per_hundred / 100,
                    )
                )
    return pd.DataFrame(rows)


SCORES = {
    "candidate:a": 4,
    "candidate:b": 7,
    "candidate:c": 2,
    "candidate:d": 6,
    "candidate:e": None,
}


@pytest.fixture
def election():
    return build_election(synthetic_results())


def test_election_orders_finalists_by_first_round_support(election):
    assert election.finalists == ("candidate:a", "candidate:b")
    assert election.outcomes == ("candidate:a", "candidate:b", "blank_invalid", "abstention")
    assert election.registered_r2.tolist() == [100, 300]
    assert election.first.sum(axis=1) == pytest.approx([1, 1])


# --- Row rules (D3, D4) ---------------------------------------------------------------


@pytest.mark.parametrize(
    "score, finalists, expected",
    [
        (3, (4, 7), A),
        (6, (4, 7), B),
        (1, (4, 7), A),  # H1 has no threshold: far voters still go to the nearer finalist
        (4, (3, 5), (A + B) / 2),  # equidistant: 50/50 between the two finalists
        (4, (2, 6), (A + B) / 2),
    ],
)
def test_h1_sends_each_group_to_the_nearer_finalist(score, finalists, expected):
    assert proximity_row(score, *finalists, tie="split", far=None) == pytest.approx(expected)


def test_h1_tie_variant_sends_equidistant_groups_to_abstention():
    assert proximity_row(4, 3, 5, tie="abstention", far=None) == pytest.approx(ABST)
    # The variant changes ties only.
    assert proximity_row(3, 4, 7, tie="abstention", far=None) == pytest.approx(A)


@pytest.mark.parametrize("far, non_vote", [("abstention", ABST), ("blank_invalid", BLANK)])
def test_h2_threshold_applies_at_distance_two_exactly(far, non_vote):
    # d = 2 to A and 5 to B: at least two from both, so a non-vote.
    assert proximity_row(2, 4, 7, tie="split", far=far) == pytest.approx(non_vote)
    # d = 2 to A but 1 to B: not far from both, so the nearer finalist.
    assert proximity_row(6, 4, 7, tie="split", far=far) == pytest.approx(B)
    # d = 1 to A: nearer finalist.
    assert proximity_row(3, 4, 7, tie="split", far=far) == pytest.approx(A)
    # d = 2 to both: the threshold takes precedence over the tie rule.
    assert proximity_row(4, 2, 6, tie="split", far=far) == pytest.approx(non_vote)
    # Tie below the threshold: split as in H1.
    assert proximity_row(4, 3, 5, tie="split", far=far) == pytest.approx((A + B) / 2)


def test_missing_score_has_no_proximity_row():
    assert proximity_row(None, 4, 7, tie="split", far=None) is None


@pytest.mark.parametrize("tie", ["random", ""])
def test_unknown_tie_rule_is_rejected(tie):
    with pytest.raises(ValueError):
        proximity_row(4, 3, 5, tie=tie, far=None)


# --- Matrices -------------------------------------------------------------------------


def test_h0a_matrix_reproduces_the_existing_baseline(election):
    predicted = predict(election, transfer_tensor(election, "H0a"))
    for i in range(len(election.areas)):
        shares = dict(zip(election.groups, election.first[i], strict=True))
        expected = predict_h0(shares, election.finalists)
        assert predicted[i] == pytest.approx([expected[o] for o in election.outcomes], abs=1e-12)


def test_h0b_never_sends_eliminated_support_to_abstention(election):
    matrix = transfer_matrix(election, "H0b", "01")
    row = matrix.loc["candidate:c"]
    assert row["abstention"] == 0
    # 30 : 20 : 5 among finalist a, finalist b and blank/invalid.
    assert row[["candidate:a", "candidate:b", "blank_invalid"]].tolist() == pytest.approx(
        [30 / 55, 20 / 55, 5 / 55]
    )
    predicted = predict(election, transfer_tensor(election, "H0b"))
    assert predicted[0, 3] == pytest.approx(0.20)  # abstention keeps only its identity row
    assert predicted.sum(axis=1) == pytest.approx([1, 1])


@pytest.mark.parametrize("model", ["H0a", "H0b", "H1", "H2-abst", "H2-blank"])
def test_retained_groups_keep_identity_rows(election, model):
    matrix = transfer_matrix(election, model, "02", SCORES)
    for option in election.outcomes:
        expected = [1.0 if column == option else 0.0 for column in election.outcomes]
        assert matrix.loc[option].tolist() == expected


def test_candidate_without_score_falls_back_to_the_h0b_row(election):
    h0b = transfer_matrix(election, "H0b", "01")
    for model in ("H1", "H2-abst", "H2-blank"):
        matrix = transfer_matrix(election, model, "01", SCORES)
        assert matrix.loc["candidate:e"].tolist() == pytest.approx(h0b.loc["candidate:e"].tolist())
    assert transfer_matrix(election, "H1", "01", SCORES).loc["candidate:c"].tolist() == [1, 0, 0, 0]
    far = transfer_matrix(election, "H2-blank", "01", SCORES).loc["candidate:c"]
    assert far.tolist() == [0, 0, 1, 0]


def test_scored_models_need_scores_for_both_finalists_and_every_candidate(election):
    with pytest.raises(ValueError, match="finalist"):
        transfer_tensor(election, "H1", SCORES | {"candidate:a": None})
    incomplete = {k: v for k, v in SCORES.items() if k != "candidate:d"}
    with pytest.raises(ValueError, match="reference"):
        transfer_tensor(election, "H1", incomplete)
    with pytest.raises(ValueError, match="Unknown model"):
        transfer_tensor(election, "H9", SCORES)


@pytest.mark.parametrize("year", YEARS)
@pytest.mark.parametrize("coding", ["primary", "alternative"])
@pytest.mark.parametrize("tie", ["split", "abstention"])
def test_every_real_matrix_is_row_stochastic(year, coding, tie):
    results, _, _ = load_dataset(BUNDLED / str(year))
    election = build_election(results)
    scores = election_scores(load_candidate_positions(), year, coding)
    h0b = transfer_tensor(election, "H0b")
    for model in ("H0a", "H0b", "H1", "H2-abst", "H2-blank"):
        tensor = transfer_tensor(election, model, scores, tie)
        for candidate in (tensor, mix(tensor, h0b, 0.37)):  # 0.37: an arbitrary H3 mixture
            assert (candidate >= 0).all()
            assert np.allclose(candidate.sum(axis=2), 1, atol=1e-12)
            for k, option in enumerate(election.outcomes):
                row = candidate[:, election.groups.index(option), :]
                assert np.array_equal(row, np.tile(np.eye(4)[k], (len(election.areas), 1)))
            predicted = predict(election, candidate)
            assert np.allclose(predicted.sum(axis=1), 1, atol=1e-9)


def test_alternative_coding_replaces_only_rows_that_list_an_alternative():
    positions = load_candidate_positions()
    primary = election_scores(positions, 2022, "primary")
    alternative = election_scores(positions, 2022, "alternative")
    assert primary["candidate:emmanuel-macron"] == 4
    assert alternative["candidate:emmanuel-macron"] == 5  # Centre-right alternative
    assert alternative["candidate:marine-le-pen"] == primary["candidate:marine-le-pen"] == 7
    assert election_scores(positions, 2017, "alternative")["candidate:jacques-cheminade"] is None
    with pytest.raises(ValueError):
        election_scores(positions, 2022, "best-fit")


# --- Scoring and H3 -------------------------------------------------------------------


def test_numpy_score_matches_the_shared_evaluation_code(election):
    predicted = predict(election, transfer_tensor(election, "H1", SCORES))
    rows = [
        dict(
            year=election.year,
            department_code=code,
            option=option,
            registered=election.registered_r2[i],
            actual_share=election.actual[i, k],
            predicted_share=predicted[i, k],
        )
        for i, code in enumerate(election.areas)
        for k, option in enumerate(election.outcomes)
    ]
    expected = weighted_area_error(pd.DataFrame(rows)).weighted_mae_pp.iloc[0]
    assert primary_score(predicted, election) == pytest.approx(expected, abs=1e-12)


def test_h3_is_a_mixture_and_p_bounds_recover_its_parts(election):
    base = transfer_tensor(election, "H1", SCORES)
    h0b = transfer_tensor(election, "H0b")
    assert np.array_equal(mix(base, h0b, 0), base)
    assert np.array_equal(mix(base, h0b, 1), h0b)
    half = mix(base, h0b, 0.5)
    assert predict(election, half) == pytest.approx(
        mix(predict(election, base), predict(election, h0b), 0.5)
    )
    assert P_GRID[0] == 0 and P_GRID[-1] == 1 and len(P_GRID) == 101
    assert np.allclose(np.diff(P_GRID), 0.01)


def test_fit_recovers_a_known_mixture_on_the_grid(election):
    base = predict(election, transfer_tensor(election, "H1", SCORES))
    h0b = predict(election, transfer_tensor(election, "H0b"))
    truth = replace(election, actual=mix(base, h0b, 0.30))
    p, score = fit_p([(base, h0b, truth)])
    assert p == pytest.approx(0.30)
    assert score == pytest.approx(0, abs=1e-9)


@pytest.fixture(scope="module")
def real_inputs():
    return {
        year: load_dataset(BUNDLED / str(year))[0] for year in YEARS
    }, load_candidate_positions()


@pytest.fixture(scope="module")
def real_evaluation(real_inputs):
    return evaluate_models(*real_inputs)


def test_predictions_table_has_the_documented_schema(real_evaluation):
    predictions, report = real_evaluation
    assert list(predictions.columns) == [
        "year",
        "area_code",
        "model",
        "variant",
        "train_elections",
        "outcome",
        "predicted_share",
        "actual_share",
        "registered_r2",
    ]
    assert set(predictions.model) == {
        "H0a",
        "H0b",
        "H1",
        "H2-abst",
        "H2-blank",
        "H3(H1)",
        "H3(H2-abst)",
        "H3(H2-blank)",
    }
    assert set(predictions.year) == set(YEARS)
    key = ["year", "area_code", "model", "variant", "outcome"]
    assert not predictions.duplicated(key).any()
    sums = predictions.groupby(key[:-1]).predicted_share.sum()
    assert np.allclose(sums, 1, atol=1e-9)
    main = predictions[predictions.variant.isin(["default", MAIN_VARIANT])]
    assert main.groupby(["model", "year"]).area_code.nunique().min() >= 100
    assert report["coding_status"] == "draft coding"


def test_leave_one_election_out_never_trains_on_the_test_election(real_evaluation):
    predictions, report = real_evaluation
    fitted = predictions[predictions.model.str.startswith("H3")]
    assert len(fitted)
    for (year, trained), _ in fitted.groupby(["year", "train_elections"]):
        trained_years = [int(y) for y in trained.split(",")]
        assert year not in trained_years
        assert sorted(trained_years) == sorted(set(YEARS) - {year})
    parameter_free = predictions[~predictions.model.str.startswith("H3")]
    assert set(parameter_free.train_elections) == {""}
    folds = [fold for fold in report["h3_folds"] if fold["test_year"] is not None]
    assert len(folds) == len(YEARS) * len(BASES) * 3  # three variants
    assert all(fold["test_year"] not in fold["train_elections"] for fold in folds)


def test_held_out_results_cannot_influence_the_fitted_parameter(real_inputs, real_evaluation):
    results, positions = real_inputs
    _, report = real_evaluation
    # Replace the 2017 second round with an absurd outcome: everyone abstains.
    tampered = results[2017].copy()
    second = tampered["round"] == 2
    tampered.loc[second, "share"] = (tampered.loc[second, "option"] == "abstention").astype(float)
    _, changed = evaluate_models(results | {2017: tampered}, positions)

    def parameters(source, test_year):
        return [
            (f["base"], f["variant"], f["p"])
            for f in source["h3_folds"]
            if f["test_year"] == test_year
        ]

    assert parameters(changed, 2017) == parameters(report, 2017)  # test fold: unaffected
    assert parameters(changed, 2022) != parameters(report, 2022)  # 2017 is training data there


def test_evaluation_report_records_fallbacks_and_finalists(real_evaluation):
    _, report = real_evaluation
    assert report["elections"]["2002"]["finalist_a"] == "candidate:jacques-chirac"
    assert report["elections"]["2002"]["finalist_b"] == "candidate:jean-marie-le-pen"
    assert report["elections"]["2022"]["finalist_a"] == "candidate:emmanuel-macron"
    assert sorted((f["year"], f["option"]) for f in report["h0b_fallbacks"]) == [
        (2012, "candidate:jacques-cheminade"),
        (2017, "candidate:jacques-cheminade"),
    ]
    full = [fold for fold in report["h3_folds"] if fold["test_year"] is None]
    assert len(full) == len(BASES) * 3
    assert all(0 <= fold["p"] <= 1 for fold in report["h3_folds"])
