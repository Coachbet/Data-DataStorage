"""Synthetic historical formats; not observed election records."""

import csv
import json

import pytest
from vote_transfer.application.processing import aggregate_results, process_year
from vote_transfer.infrastructure.official import parse_official, sha256


def write_historical(path, year):
    rows = []
    for number in (1, 2):
        for code, scale in (("01", 1), ("2A", 2)):
            candidates = (
                [("ALPHA", 30), ("BETA", 20), ("GAMMA", 25)]
                if number == 1
                else [("GAMMA", 35), ("ALPHA", 40)]
            )
            for panel, (name, count) in enumerate(candidates, 1):
                row = [number, code, "001", "Synthetic commune"]
                if year == 2012:
                    row += ["01", "02"]
                row += [
                    "0001",
                    100 * scale,
                    80 * scale,
                    75 * scale,
                    panel,
                    name,
                    "Test",
                    "UNUSED",
                    count * scale,
                ]
                rows.append(row)
    with path.open("w", encoding="cp1252", newline="") as stream:
        if year != 2012:
            stream.write("-- Synthetic schema description\n--\n")
        csv.writer(stream, delimiter=";").writerows(rows)
    return rows


@pytest.mark.parametrize("year", [2002, 2007, 2012])
def test_historical_counts_are_not_multiplied_by_candidate_rows(tmp_path, year):
    path = tmp_path / "both_rounds.txt"
    write_historical(path, year)
    turnout, votes = parse_official(path, year, 1)
    assert len(turnout) == 2
    assert len(votes) == 6
    assert turnout.registered.sum() == 300
    assert turnout.blank_invalid.sum() == 15
    assert turnout[["blank", "invalid"]].isna().all().all()
    assert set(turnout.department_code) == {"01", "2A"}
    assert set(turnout.station_code) == {"0001"}
    assert aggregate_results(turnout, votes).groupby("department_code").share.sum().tolist() == [
        1,
        1,
    ]
    assert set(parse_official(path, year, 2)[1].candidate_id) == {"test-alpha", "test-gamma"}


@pytest.mark.parametrize("year", [2002, 2007, 2012])
def test_historical_end_to_end_uses_one_original_for_both_rounds(tmp_path, year):
    folder = tmp_path / "raw" / "official" / str(year)
    folder.mkdir(parents=True)
    path = folder / "both_rounds.txt"
    write_historical(path, year)
    records = [{"round": n, "file": path.name, "sha256": sha256(path)} for n in (1, 2)]
    (folder / "manifest.json").write_text(json.dumps({"year": year, "files": records}))
    report = process_year(year, tmp_path)
    assert report["registered_by_round"] == {"1": 300, "2": 300}
    assert report["ballot_detail"] == "combined_only"
    assert report["partial_national_coverage"] == (year < 2012)


def test_inconsistent_turnout_repeated_on_candidate_rows_fails(tmp_path):
    path = tmp_path / "both_rounds.txt"
    rows = write_historical(path, 2012)
    rows[1][7] += 1
    with path.open("w", encoding="cp1252", newline="") as stream:
        csv.writer(stream, delimiter=";").writerows(rows)
    with pytest.raises(ValueError, match="Turnout differs"):
        parse_official(path, 2012, 1)


def test_unexpected_historical_layout_fails(tmp_path):
    path = tmp_path / "both_rounds.txt"
    path.write_text("1;01;001;extra;columns\n")
    with pytest.raises(ValueError, match="Malformed historical"):
        parse_official(path, 2002, 1)


def test_2017_uses_the_verified_modern_layout(raw_dataset):
    path = raw_dataset / "raw/official/2022/round_1.txt"
    turnout, votes = parse_official(path, 2017, 1)
    assert set(turnout.year) == {2017}
    assert turnout.blank_invalid.sum() == 15
    assert len(votes) == 6
