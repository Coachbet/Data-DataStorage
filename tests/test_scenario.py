from pathlib import Path

import pytest
from vote_transfer.application.datasets import load_dataset, load_predictions
from vote_transfer.application.positions import load_candidate_positions
from vote_transfer.application.scenario import (
    SCENARIO_MODELS,
    scenario_candidates,
    scenario_election,
    simulate_runoff,
)

DATA = Path(__file__).resolve().parents[1] / "data"
MACRON, LE_PEN = "candidate:emmanuel-macron", "candidate:marine-le-pen"
MELENCHON = "candidate:jean-luc-melenchon"


@pytest.fixture(scope="module")
def inputs():
    results, _, _ = load_dataset(DATA / "bundled" / "2022")
    _, report = load_predictions(DATA)
    return results, load_candidate_positions(), report


def test_candidates_are_the_twelve_first_round_candidates_largest_first(inputs):
    candidates = scenario_candidates(inputs[0])
    assert len(candidates) == 12
    assert candidates.option.tolist()[:3] == [MACRON, LE_PEN, MELENCHON]


@pytest.mark.parametrize("model", SCENARIO_MODELS)
def test_every_model_gives_shares_that_sum_to_one_hundred(inputs, model):
    scenario = simulate_runoff(inputs[0], (LE_PEN, MELENCHON), model, *inputs[1:])
    areas = scenario["areas"]
    assert len(areas) == 107
    shares = areas[[c for c in areas if c.endswith("_pct")]]
    assert (shares >= 0).all().all()
    assert shares.sum(axis=1).tolist() == pytest.approx([100] * 107)
    assert sum(scenario["pooled_pct"].values()) == pytest.approx(100)
    # Finalist A is the one with more first-round votes, whatever order was given.
    assert (scenario["finalist_a"], scenario["finalist_b"]) == (LE_PEN, MELENCHON)
    assert (scenario["p"] is not None) == model.startswith("H3")


def test_scenario_uses_only_first_round_inputs(inputs):
    results, positions, report = inputs
    first_only = results[results["round"] == 1]
    full = simulate_runoff(results, (MACRON, LE_PEN), "H1", positions, report)
    partial = simulate_runoff(first_only, (MACRON, LE_PEN), "H1", positions, report)
    assert full["pooled_pct"] == partial["pooled_pct"]
    assert scenario_election(results, (MACRON, LE_PEN)).actual.size == 107 * 4


def test_the_real_2022_pair_reproduces_the_evaluated_h0b_prediction(inputs):
    results, positions, report = inputs
    predictions, _ = load_predictions(DATA)
    stored = predictions[
        (predictions.year == 2022) & (predictions.model == "H0b") & (predictions.outcome == MACRON)
    ].set_index("area_code")
    scenario = simulate_runoff(results, (MACRON, LE_PEN), "H0b", positions, report)
    simulated = scenario["areas"].set_index("area_code").finalist_a_pct / 100
    assert simulated.tolist() == pytest.approx(
        stored.predicted_share.reindex(simulated.index).tolist()
    )


def test_invalid_finalists_and_models_are_rejected(inputs):
    with pytest.raises(ValueError, match="two different"):
        simulate_runoff(inputs[0], (MACRON, MACRON), "H0b", *inputs[1:])
    with pytest.raises(ValueError, match="two different"):
        simulate_runoff(inputs[0], (MACRON, "blank_invalid"), "H0b", *inputs[1:])
    with pytest.raises(ValueError, match="Unknown model"):
        simulate_runoff(inputs[0], (MACRON, LE_PEN), "H9", *inputs[1:])
