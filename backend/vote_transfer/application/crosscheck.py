"""Compare our station-level aggregation with independently published totals."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from vote_transfer.infrastructure.official import sha256
from vote_transfer.infrastructure.reference import parse_national_summary


def national_totals(turnout: pd.DataFrame, votes: pd.DataFrame) -> dict[int, dict[str, int]]:
    """Sum validated station rows once per round, in the published summary's terms."""
    totals = {}
    for round_number, stations in turnout.groupby("round"):
        counts = {
            name: int(stations[name].sum())
            for name in ("registered", "abstentions", "voters", "blank", "invalid", "valid")
        }
        candidates = votes[votes["round"] == round_number].groupby("candidate_id").votes.sum()
        counts |= {f"candidate:{cid}": int(total) for cid, total in candidates.items()}
        totals[int(round_number)] = counts
    return totals


def crosscheck_national(year: int, root: Path) -> dict:
    """Write and return a field-by-field comparison; differences are reported, not fixed."""
    folder = root / "raw" / "reference" / f"national_{year}"
    manifest = json.loads((folder / "manifest.json").read_text())
    interim = root / "interim" / str(year)
    if not (interim / "turnout.parquet").exists():
        raise ValueError(f"Run `vote-transfer process --year {year}` before the cross-check.")
    ours = national_totals(
        pd.read_parquet(interim / "turnout.parquet"),
        pd.read_parquet(interim / "candidate_votes.parquet"),
    )
    rows = []
    for record in manifest["files"]:
        path = folder / record["file"]
        if sha256(path) != record["sha256"]:
            raise ValueError(f"Reference checksum mismatch: {path}")
        published = parse_national_summary(path)
        round_number = record["round"]
        for field in sorted(published.keys() | ours[round_number].keys()):
            ours_value = ours[round_number].get(field)
            rows.append(
                {
                    "round": round_number,
                    "field": field,
                    "published": published.get(field),
                    "ours": ours_value,
                    "matches": published.get(field) == ours_value,
                }
            )
    report = {
        "year": year,
        "reference": "Ministry national summary files (resultats-par-niveau-fe)",
        "fields_compared": len(rows),
        "all_match": all(row["matches"] for row in rows),
        "comparisons": rows,
    }
    target = root / "processed" / str(year)
    target.mkdir(parents=True, exist_ok=True)
    (target / "national_crosscheck.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
