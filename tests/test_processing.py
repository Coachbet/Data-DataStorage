from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.processing import aggregate_results, process_year, validate_results
from vote_transfer.infrastructure.official import parse_official


def read_round(root: Path, number: int = 1):
    return parse_official(root / "raw" / "official" / "2022" / f"round_{number}.txt", 2022, number)


def test_repeated_blocks_and_panel_changes_preserve_candidate_identity(raw_dataset):
    turnout, first = read_round(raw_dataset)
    _, second = read_round(raw_dataset, 2)
    assert len(turnout) == 2
    assert len(first) == 6  # all three candidate blocks, not only the published header
    assert set(turnout.department_code) == {"01", "2A"}
    assert set(turnout.station_code) == {"0001"}
    assert first[first.candidate_id == "test-alpha"].source_panel_number.unique().tolist() == ["1"]
    assert second[second.candidate_id == "test-alpha"].source_panel_number.unique().tolist() == [
        "2"
    ]


@pytest.mark.parametrize(
    "fault", ["duplicate", "negative", "fraction", "missing", "turnout", "votes", "orphan"]
)
def test_invalid_results_fail_closed(raw_dataset, fault):
    turnout, votes = read_round(raw_dataset)
    if fault == "duplicate":
        turnout = pd.concat([turnout, turnout.iloc[:1]])
    elif fault == "negative":
        votes.loc[0, "votes"] = -1
    elif fault == "fraction":
        votes["votes"] = votes.votes.astype(float)
        votes.loc[0, "votes"] = 1.5
    elif fault == "missing":
        turnout.loc[0, "department_code"] = None
    elif fault == "turnout":
        turnout.loc[0, "registered"] += 1
    elif fault == "votes":
        votes.loc[0, "votes"] += 1
    elif fault == "orphan":
        votes.loc[0, "station_code"] = "9999"
    with pytest.raises(ValueError):
        validate_results(turnout, votes)


def test_registered_denominator_and_mass_conservation(raw_dataset):
    table = aggregate_results(*read_round(raw_dataset))
    unit = table[table.department_code == "01"].set_index("option")
    assert unit.loc["candidate:test-alpha", "share"] == 0.3
    assert unit.loc["abstention", "share"] == 0.2
    assert unit.loc["blank_invalid", "share"] == 0.05
    assert unit.share.sum() == pytest.approx(1)


def test_schema_changes_are_not_silently_accepted(raw_dataset):
    path = raw_dataset / "raw" / "official" / "2022" / "round_1.txt"
    path.write_text(
        path.read_text(encoding="cp1252").replace("Inscrits", "Changed"), encoding="cp1252"
    )
    with pytest.raises(ValueError, match="schema"):
        read_round(raw_dataset)


def test_complete_pipeline_and_raw_integrity(raw_dataset):
    report = process_year(2022, raw_dataset)
    assert report["territorial_units"] == 2
    assert report["registered_by_round"] == {"1": 300, "2": 300}
    output = raw_dataset / "processed" / "2022" / "department_results.parquet"
    assert len(pd.read_parquet(output)) == 18  # 2 * (5 round-one + 4 round-two outcomes)
    previous = output.read_bytes()
    source = raw_dataset / "raw" / "official" / "2022" / "round_1.txt"
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum"):
        process_year(2022, raw_dataset)
    assert output.read_bytes() == previous  # a failed build does not replace valid outputs
