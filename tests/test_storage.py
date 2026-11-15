"""Normalised processed tables and the wide view derived from them."""

import json
from pathlib import Path

import pandas as pd
import pytest
from test_historical import write_historical
from vote_transfer.application.datasets import load_dataset, load_tables
from vote_transfer.application.evaluation import weighted_area_error
from vote_transfer.application.processing import (
    aggregate_results,
    aggregate_tables,
    process_year,
    results_view,
    validate_tables,
)
from vote_transfer.infrastructure.official import parse_official, sha256

BUNDLED = Path(__file__).resolve().parents[1] / "data" / "bundled"
# Primary H0 scores computed from the per-year h0_evaluation.parquet files on
# 15 November 2026, before the storage refactor. They pin "H0a did not change".
H0A_BEFORE_REFACTOR = {
    2002: 19.035389337146054,
    2007: 4.341688079590604,
    2012: 5.558151170546881,
    2017: 8.601412777860654,
    2022: 6.120531569056327,
}


@pytest.fixture
def tables(raw_dataset):
    rounds = [
        parse_official(raw_dataset / f"raw/official/2022/round_{n}.txt", 2022, n) for n in (1, 2)
    ]
    turnout = pd.concat([r[0] for r in rounds], ignore_index=True)
    votes = pd.concat([r[1] for r in rounds], ignore_index=True)
    return aggregate_tables(turnout, votes), (turnout, votes)


def test_area_table_states_each_denominator_exactly_once(tables):
    (areas, outcomes, options), _ = tables
    assert list(areas.columns) == [
        "year",
        "round",
        "area_code",
        "area_name",
        "registered",
        "polling_stations",
        "blank",
        "invalid",
    ]
    assert len(areas) == 4  # two areas, two rounds
    assert not areas.duplicated(["year", "round", "area_code"]).any()
    assert areas.registered.sum() == 600  # safe to sum: no repetition across options
    assert list(outcomes.columns) == ["year", "round", "area_code", "option", "count"]
    assert "share" not in outcomes and "registered" not in outcomes
    assert set(options.option) == {
        "candidate:test-alpha",
        "candidate:test-beta",
        "candidate:test-gamma",
        "blank_invalid",
        "abstention",
    }


def test_outcome_counts_partition_the_registered_electorate(tables):
    (areas, outcomes, _), _ = tables
    totals = outcomes.groupby(["year", "round", "area_code"])["count"].sum()
    registered = areas.set_index(["year", "round", "area_code"]).registered
    assert totals.eq(registered).all()


def test_blank_and_invalid_are_kept_separately_when_published(tables):
    (areas, outcomes, _), _ = tables
    first = areas[(areas["round"] == 1) & (areas.area_code == "2A")].iloc[0]
    assert (first.blank, first.invalid) == (4, 6)
    combined = outcomes[
        (outcomes["round"] == 1)
        & (outcomes.area_code == "2A")
        & (outcomes.option == "blank_invalid")
    ]["count"].iloc[0]
    assert combined == first.blank + first.invalid


@pytest.mark.parametrize("year", [2002, 2012])
def test_blank_and_invalid_stay_null_before_2017(tmp_path, year):
    path = tmp_path / "both_rounds.txt"
    write_historical(path, year)
    areas, _, _ = aggregate_tables(*parse_official(path, year, 1))
    assert areas[["blank", "invalid"]].isna().all().all()
    assert str(areas.blank.dtype) == "Int64"


def test_wide_view_is_derived_and_shares_are_computed(tables):
    (areas, outcomes, options), (turnout, votes) = tables
    view = results_view(areas, outcomes, options)
    assert list(view.columns) == [
        "year",
        "round",
        "department_code",
        "option",
        "label",
        "count",
        "department_name",
        "registered",
        "polling_stations",
        "share",
    ]
    pd.testing.assert_frame_equal(view, aggregate_results(turnout, votes))
    unit = view[(view.department_code == "01") & (view["round"] == 1)].set_index("option")
    assert unit.loc["candidate:test-alpha", "share"] == 0.3
    assert unit.share.sum() == pytest.approx(1)


@pytest.mark.parametrize("fault", ["duplicate_area", "orphan_outcome", "sum", "label", "split"])
def test_inconsistent_tables_are_rejected(tables, fault):
    (areas, outcomes, options), _ = tables
    if fault == "duplicate_area":
        areas = pd.concat([areas, areas.iloc[[0]]])
    elif fault == "orphan_outcome":
        outcomes = pd.concat([outcomes, outcomes.iloc[[0]].assign(area_code="99")])
    elif fault == "sum":
        outcomes.loc[0, "count"] += 1
    elif fault == "label":
        options = options.iloc[1:]
    else:
        areas.loc[0, "blank"] += 1
    with pytest.raises(ValueError):
        validate_tables(areas, outcomes, options)


def test_process_writes_normalised_tables_with_recorded_hashes(raw_dataset):
    report = process_year(2022, raw_dataset)
    folder = raw_dataset / "processed" / "2022"
    assert sorted(p.name for p in folder.iterdir()) == [
        "areas.parquet",
        "options.parquet",
        "outcomes.parquet",
        "quality_report.json",
    ]
    assert report["outputs"] == {p.name: sha256(p) for p in folder.glob("*.parquet")}
    areas, outcomes, options, quality = load_tables(folder)
    assert len(areas) == 4 and len(outcomes) == 18 and quality["year"] == 2022
    results, evaluation, _ = load_dataset(folder)
    assert len(results) == 18 and len(evaluation) == 8


def test_loading_rejects_a_modified_table(raw_dataset):
    process_year(2022, raw_dataset)
    path = raw_dataset / "processed/2022/outcomes.parquet"
    frame = pd.read_parquet(path)
    frame.loc[0, "count"] += 1
    frame.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="do not match"):
        load_tables(path.parent)


@pytest.mark.parametrize("year", sorted(H0A_BEFORE_REFACTOR))
def test_h0a_scores_are_unchanged_by_the_storage_refactor(year):
    _, evaluation, _ = load_dataset(BUNDLED / str(year))
    score = weighted_area_error(evaluation).weighted_mae_pp.iloc[0]
    assert score == pytest.approx(H0A_BEFORE_REFACTOR[year], abs=1e-12)


@pytest.mark.parametrize("year", [2017, 2022])
def test_bundled_snapshots_keep_the_blank_invalid_split(year):
    areas, outcomes, _, quality = load_tables(BUNDLED / str(year))
    assert areas[["blank", "invalid"]].notna().all().all()
    combined = outcomes[outcomes.option == "blank_invalid"].set_index(["round", "area_code"])[
        "count"
    ]
    split = areas.set_index(["round", "area_code"])[["blank", "invalid"]].sum(axis=1)
    assert combined.eq(split.astype("int64")).all()
    assert json.dumps(quality)  # provenance stays JSON-serialisable


def test_bundled_snapshots_before_2017_have_no_split():
    areas, _, _, _ = load_tables(BUNDLED / "2012")
    assert areas[["blank", "invalid"]].isna().all().all()
