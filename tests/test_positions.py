from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.positions import (
    REFERENCE_DIR,
    load_candidate_positions,
    load_poll_scores,
)


def test_reference_exactly_covers_the_five_official_candidate_rosters():
    positions = load_candidate_positions()
    assert positions.groupby("year").size().to_dict() == {
        2002: 16,
        2007: 12,
        2012: 10,
        2017: 11,
        2022: 12,
    }
    root = Path(__file__).resolve().parents[1] / "data/bundled"
    for year, candidates in positions.groupby("year"):
        results = pd.read_parquet(root / str(year) / "outcomes.parquet")
        official = results.loc[
            (results["round"] == 1) & results.option.str.startswith("candidate:"), "option"
        ].str.removeprefix("candidate:")
        assert set(candidates.candidate_id) == set(official)
    assert positions.ideology_score.isna().sum() == 2
    assert set(positions.loc[positions.ideology_score.isna(), "candidate_id"]) == {
        "jacques-cheminade"
    }


def test_historical_affiliations_and_unreviewed_positions_are_explicit():
    positions = load_candidate_positions().set_index(["year", "candidate_id"])
    assert positions.loc[(2007, "francois-bayrou"), "party_abbreviation"] == "UDF"
    assert positions.loc[(2012, "nicolas-dupont-aignan"), "party_abbreviation"] == "DLR"
    assert positions.loc[(2017, "marine-le-pen"), "party_abbreviation"] == "FN"
    assert positions.loc[(2022, "marine-le-pen"), "party_abbreviation"] == "RN"
    assert positions.loc[(2017, "emmanuel-macron"), "party_abbreviation"] == "EM"
    assert positions.loc[(2022, "emmanuel-macron"), "party_abbreviation"] == "LREM"
    assert positions.loc[(2007, "gerard-schivardi"), "party_abbreviation"] == "IND"
    assert not positions.review_status.eq("reviewed").any()


@pytest.mark.parametrize("corruption", ["duplicate", "score", "source", "missing_as_centre"])
def test_reference_rejects_ambiguous_keys_and_misleading_codes(tmp_path, corruption):
    frame = pd.read_csv(REFERENCE_DIR / "candidate_positions.csv", keep_default_na=False)
    if corruption == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]])
    elif corruption == "score":
        frame.loc[0, "ideology_score"] = 1
    elif corruption == "source":
        frame.loc[0, "source_ids"] = "invented"
    else:
        frame.loc[frame.candidate_id == "jacques-cheminade", "ideology_score"] = 4
    frame.to_csv(tmp_path / "candidate_positions.csv", index=False)
    (tmp_path / "sources.json").write_bytes((REFERENCE_DIR / "sources.json").read_bytes())
    with pytest.raises(ValueError):
        load_candidate_positions(tmp_path)


def test_poll_based_scale_is_up_to_date_with_the_collected_polls():
    """Recompute the notebook's two passes; fails if polls change without `make scale`."""
    polls = pd.read_csv(REFERENCE_DIR / "polling_axes.csv")

    def scores(removed):
        positions = {}
        for poll in polls.itertuples():
            kept = [c for c in poll.order_left_to_right.split(";") if (poll.year, c) not in removed]
            for i, candidate in enumerate(kept):
                positions.setdefault((poll.year, candidate), []).append(i / (len(kept) - 1))
        return positions

    first = scores(set())
    unplaced = {
        key
        for key, values in first.items()
        if key[1] == "jacques-cheminade" or max(values) - min(values) > 0.4
    }
    second = scores(unplaced)
    shipped = load_poll_scores().set_index(["year", "candidate_id"])
    assert set(shipped.index) == set(first)
    assert set(shipped.index[shipped.status == "unplaced"]) == unplaced
    for key, values in second.items():
        assert shipped.loc[key, "score"] == pytest.approx(sum(values) / len(values), abs=1e-12)
