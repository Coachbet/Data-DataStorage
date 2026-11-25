"""Site wording and chart shapes must follow the generated results, never lead them."""

import json
from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.analysis import (
    comparison_table,
    national_errors,
    setting_predictions,
    threshold_table,
    with_roles,
)
from vote_transfer.application.datasets import available_datasets, load_dataset, load_predictions
from vote_transfer.application.models import build_election
from vote_transfer.application.positions import load_candidate_positions
from vote_transfer.application.presentation import (
    ROLES,
    answer,
    count_of,
    fmt_int,
    fmt_pct,
    fmt_pp,
    key_findings,
    ladder_example,
    outcome_roles,
    rounds_side_by_side,
)

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"


@pytest.fixture(scope="module")
def loaded():
    predictions, report = load_predictions(DATA)
    predictions = with_roles(predictions, report)
    elections = {
        int(year): build_election(load_dataset(folder)[0])
        for year, folder in available_datasets(DATA).items()
    }
    return predictions, report, elections, load_candidate_positions()


def test_numbers_have_one_format():
    assert fmt_pp(4.348) == "4.3 pp"
    assert fmt_pp(-12.06, signed=True) == "−12.1 pp"
    assert fmt_pp(30.0, signed=True) == "+30.0 pp"
    assert fmt_pct(38.46) == "38.5%"
    assert fmt_int(48752339.0) == "48,752,339"
    assert [count_of(5, 5), count_of(1, 5), count_of(0, 5)] == [
        "all five",
        "one of five",
        "none of the five",
    ]


def test_answer_matches_the_generated_numbers(loaded):
    comparison = comparison_table(loaded[0])
    numbers = json.loads((PROJECT / "reports/results/numbers.json").read_text(encoding="utf-8"))
    result = answer(comparison)
    assert result["best"] == numbers["best.model"]
    assert result["best_without_outlier"] == numbers["best_without_2002.model"]
    text = " ".join(result["sentences"])
    assert f"{numbers['best.mean']:.1f} pp" in text
    assert f"ranks {numbers['best.rank_without_2002']} of {numbers['n.models']}" in text
    assert f"{numbers['score.H0b.mean']:.1f} pp against {numbers['score.H0a.mean']:.1f} pp" in text
    assert numbers["wins.H0b.vs_H0a"] == 5 and "all five elections" in text
    assert result["headline"] == "No assumption explains every election best."
    assert result["chart_title"].endswith("H1 leads only in 2002")


def test_answer_changes_its_wording_when_one_model_is_stable():
    table = pd.DataFrame(
        {
            "2002": [9.0, 3.0, 5.0],
            "2007": [8.0, 2.0, 4.0],
            "mean": [8.5, 2.5, 4.5],
            "mean_without_2002": [8.0, 2.0, 4.0],
            "rank": [3, 1, 2],
            "rank_without_2002": [3, 1, 2],
        },
        index=["H0a", "H0b", "H1"],
    )
    result = answer(table)
    assert result["stable"] and result["headline"].startswith("H0b is the closest assumption")
    assert "No assumption" not in " ".join([result["headline"], *result["sentences"]])


def test_findings_quote_the_tables(loaded):
    predictions, _, elections, positions = loaded
    comparison = comparison_table(predictions)
    errors = national_errors(setting_predictions(predictions))
    findings = key_findings(comparison, errors, threshold_table(elections, positions))
    assert len(findings) == 3 and all(f["evidence"].startswith("Evidence") for f in findings)
    numbers = json.loads((PROJECT / "reports/results/numbers.json").read_text(encoding="utf-8"))
    assert f"{numbers['signed_max.H0a.abstention']:.1f} pp" in findings[0]["body"]
    assert f"{numbers['score.H1.2002']:.1f} pp" in findings[1]["body"]
    assert f"{numbers['h2.2022.on_threshold_pct']:.1f}%" in findings[2]["body"]


def test_ladder_example_rows_are_shares_of_one_real_group(loaded):
    _, report, elections, positions = loaded
    example = ladder_example(elections[2022], positions, report)
    rows = example["rows"]
    assert example["group"] == "candidate:jean-luc-melenchon"
    assert list(rows.columns) == list(ROLES) and len(rows) == 8
    assert rows.sum(axis=1).tolist() == pytest.approx([100] * 8)
    assert rows.loc["H0b", "abstention"] == pytest.approx(0)
    assert rows.loc["H1"].max() == pytest.approx(100)  # the whole group to one finalist
    assert rows.loc["H2-abst", "abstention"] == pytest.approx(100)
    assert rows.loc["H2-blank", "blank_invalid"] == pytest.approx(100)
    assert set(example["p"]) == {"H3(H1)", "H3(H2-abst)", "H3(H2-blank)"}


def test_rounds_side_by_side_account_for_every_registered_voter(loaded):
    results = load_dataset(DATA / "bundled" / "2022")[0]
    roles = outcome_roles(results)
    assert roles["candidate:emmanuel-macron"] == "finalist_a"
    assert roles["candidate:marine-le-pen"] == "finalist_b"
    table = rounds_side_by_side(results, roles)
    totals = table.groupby("row").pct.sum()
    assert totals.tolist() == pytest.approx([100, 100])
    round_two = table[table.row == "Round 2"].set_index("segment").pct
    assert round_two["other"] == 0
