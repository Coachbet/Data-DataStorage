"""Cached loading. Keys include file sizes and times, so a rebuilt file is read again."""

from pathlib import Path

import streamlit as st
from vote_transfer.application.analysis import (
    comparison_table,
    national_errors,
    sensitivity_table,
    setting_predictions,
    threshold_table,
    tied_groups,
    with_roles,
)
from vote_transfer.application.datasets import available_datasets, load_dataset, load_predictions
from vote_transfer.application.models import build_election
from vote_transfer.application.positions import (
    REFERENCE_DIR,
    load_candidate_positions,
    load_position_sources,
)
from vote_transfer.application.presentation import ladder_example
from vote_transfer.application.scenario import simulate_all, simulate_runoff


def stamp(*folders: Path) -> tuple:
    """Identity of the files under some folders: path, size and modification time."""
    files = [p for folder in folders for p in sorted(Path(folder).rglob("*")) if p.is_file()]
    return tuple((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in files)


def root_stamp(root: Path) -> tuple:
    return stamp(root / "processed", root / "bundled", REFERENCE_DIR)


@st.cache_data(show_spinner=False, max_entries=24)
def _dataset(folder: str, version: tuple):
    return load_dataset(Path(folder))


def dataset(folder: Path):
    """Results view, H0a evaluation and quality report of one election."""
    return _dataset(str(folder), stamp(folder))


@st.cache_data(show_spinner=False, max_entries=4)
def _positions(version: tuple):
    return load_candidate_positions(), load_position_sources()


def positions():
    return _positions(stamp(REFERENCE_DIR))


@st.cache_data(show_spinner=False, max_entries=4)
def _evaluated(root: str, version: tuple) -> dict | None:
    try:
        loaded = load_predictions(Path(root))
    except (OSError, ValueError, KeyError):
        return None
    if loaded is None:
        return None
    predictions, report = loaded
    predictions = with_roles(predictions, report)
    main = setting_predictions(predictions)
    table = comparison_table(predictions)
    reference = load_candidate_positions()
    elections = {
        int(year): build_election(load_dataset(folder)[0])
        for year, folder in available_datasets(Path(root)).items()
        if year in report["elections"]
    }
    latest = max(elections)
    names = reference.set_index(["year", "candidate_id"]).candidate_name

    def name(year: int, option: str) -> str:
        return names[(year, option.removeprefix("candidate:"))]

    finalists = {
        int(year): {role: name(int(year), election[role]) for role in ("finalist_a", "finalist_b")}
        for year, election in report["elections"].items()
    }
    ladder = ladder_example(elections[latest], reference, report)
    ladder["group_name"] = name(latest, ladder["group"])
    return {
        "predictions": main,
        "report": report,
        "comparison": table,
        "errors": national_errors(main),
        "sensitivity": sensitivity_table(predictions),
        "ties": tied_groups(reference, report),
        "threshold": threshold_table(elections, reference),
        "ladder": ladder,
        "finalists": finalists,
        "ladder_year": latest,
    }


def evaluated(root: Path) -> dict | None:
    """Everything derived from the cross-election predictions, or None without them."""
    return _evaluated(str(root), root_stamp(root))


@st.cache_data(show_spinner=False, max_entries=64)
def _scenario(folder: str, root: str, pair: tuple, model: str | None, version: tuple):
    results = load_dataset(Path(folder))[0]
    reference = load_candidate_positions()
    report = load_predictions(Path(root))[1]
    if model is None:
        return simulate_all(results, pair, reference, report)
    return simulate_runoff(results, pair, model, reference, report)


def scenario(folder: Path, root: Path, pair: tuple[str, str], model: str | None = None):
    """One assumption's implied runoff, or every assumption's pooled shares when model is None."""
    return _scenario(str(folder), str(root), pair, model, root_stamp(root))
