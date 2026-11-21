"""Read the versioned candidate references without changing observed election data.

Two references place candidates on a left-right axis:

- ``candidate_scores.csv``: the main scale, built by ``notebooks/candidate_scale.ipynb``
  from the polling institutes' left-to-right orders in ``polling_axes.csv``
  (0 = leftmost, 1 = rightmost; empty for candidates we cannot place).
- ``candidate_positions.csv``: the earlier hand-coded 1-7 families, kept as a comparison.
"""

import json
from pathlib import Path

import pandas as pd

from vote_transfer.config import PROJECT_ROOT

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
FAMILY_SCORES = {
    "Far left": 1,
    "Left": 2,
    "Centre-left": 3,
    "Centre": 4,
    "Centre-right": 5,
    "Right": 6,
    "Far right": 7,
}


POLL_STATUSES = ("placed", "unplaced")


def family_to_unit(score: float) -> float:
    """Put a 1-7 family score on the 0-1 scale of the poll-based scores (1 -> 0, 7 -> 1).

    Two steps out of six become one third, so one H2 threshold serves both scales.
    """
    return (score - 1) / 6


def load_poll_scores(folder: Path = REFERENCE_DIR) -> pd.DataFrame:
    """Validate the poll-based scale written by ``notebooks/candidate_scale.ipynb``."""
    frame = pd.read_csv(folder / "candidate_scores.csv", dtype={"candidate_id": str})
    required = {"year", "candidate_id", "score", "n_institutes", "range", "status", "reason"}
    if not required <= set(frame) or frame.empty:
        raise ValueError("The poll-based scale must contain all documented columns and rows.")
    if frame.duplicated(["year", "candidate_id"]).any():
        raise ValueError("Duplicate keys in the poll-based scale.")
    if not frame.status.isin(POLL_STATUSES).all():
        raise ValueError("Unknown status in the poll-based scale.")
    placed = frame.status.eq("placed")
    if not frame.score.notna().equals(placed):
        raise ValueError("Placed candidates need a score and unplaced ones must have none.")
    if not frame.loc[placed, "score"].between(0, 1).all():
        raise ValueError("Poll-based scores must lie between 0 and 1.")
    return frame


def load_position_sources(folder: Path = REFERENCE_DIR) -> dict:
    """Return citation metadata shipped alongside the manually coded rows."""
    return json.loads((folder / "sources.json").read_text(encoding="utf-8"))


def load_candidate_positions(folder: Path = REFERENCE_DIR) -> pd.DataFrame:
    """Validate explicit family codes and nullable scores; never impute missing positions."""
    frame = pd.read_csv(
        folder / "candidate_positions.csv",
        keep_default_na=False,
        dtype={"candidate_id": str},
    )
    required = {
        "year",
        "candidate_id",
        "candidate_name",
        "party_abbreviation",
        "party_name",
        "political_family",
        "ideology_score",
        "alternative_family",
        "review_status",
        "classification_note",
        "source_ids",
    }
    if not required <= set(frame) or frame.empty:
        raise ValueError("The candidate reference must contain all documented columns and rows.")
    if frame.duplicated(["year", "candidate_id"]).any():
        raise ValueError("Duplicate candidate-election reference keys.")
    if not frame.year.isin([2002, 2007, 2012, 2017, 2022]).all():
        raise ValueError("Unexpected reference election year.")
    for column in required - {"ideology_score", "alternative_family", "year"}:
        if frame[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"Missing candidate reference field: {column}.")
    if not frame.candidate_id.str.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*").all():
        raise ValueError("Invalid candidate identifier.")
    if not frame.political_family.isin([*FAMILY_SCORES, "Unclassified"]).all():
        raise ValueError("Unknown political family.")
    if not frame.alternative_family.isin([*FAMILY_SCORES, ""]).all():
        raise ValueError("Unknown alternative political family.")
    frame["ideology_score"] = pd.to_numeric(
        frame.ideology_score.replace("", pd.NA), errors="raise"
    ).astype("Int64")
    expected = frame.political_family.map(FAMILY_SCORES).astype("Int64")
    if not frame.ideology_score.equals(expected.rename("ideology_score")):
        raise ValueError("Political families and 1-to-7 scores disagree.")
    if not frame.review_status.isin(["draft", "reviewed", "unresolved"]).all():
        raise ValueError("Unknown candidate review status.")
    if not frame.review_status.eq("unresolved").equals(frame.ideology_score.isna()):
        raise ValueError("Unresolved positions must have no score and be flagged explicitly.")
    sources = load_position_sources(folder)
    for identifiers in frame.source_ids:
        if not set(identifiers.split(";")) <= sources.keys():
            raise ValueError("Unknown candidate reference source.")
    polls = load_poll_scores(folder)[["year", "candidate_id", "score", "status"]]
    polls = polls.rename(columns={"score": "poll_score", "status": "poll_status"})
    merged = frame.merge(polls, on=["year", "candidate_id"], how="left", validate="1:1")
    if merged.poll_status.isna().any() or len(polls) != len(frame):
        raise ValueError("The poll-based scale and the candidate table must list the same rows.")
    return merged
