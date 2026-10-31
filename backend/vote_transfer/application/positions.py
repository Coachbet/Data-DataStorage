"""Read the versioned manual reference without changing observed election data."""

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
    return frame
