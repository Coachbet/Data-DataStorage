"""Validation and aggregation shared by the CLI and the Streamlit application."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from vote_transfer.infrastructure.official import (
    COUNTS,
    STATION_KEY,
    parse_official,
    raw_filename,
    sha256,
)


def validate_results(turnout: pd.DataFrame, votes: pd.DataFrame) -> None:
    """Fail closed on missing identifiers, duplicate rows and inconsistent totals."""
    for frame, columns in (
        (turnout, [*STATION_KEY, "department_name", *COUNTS]),
        (votes, [*STATION_KEY, "candidate_id", "candidate", "votes"]),
    ):
        missing = set(columns) - set(frame.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        if frame.empty or frame[columns].isna().any().any():
            raise ValueError("Results must be nonempty and have no missing required values.")
        if (frame.select_dtypes(include="object").eq("")).any().any():
            raise ValueError("Empty identifiers or labels are not allowed.")
    if (
        turnout.duplicated(STATION_KEY).any()
        or votes.duplicated([*STATION_KEY, "candidate_id"]).any()
    ):
        raise ValueError("Duplicate station or candidate records.")
    for frame, columns in ((turnout, COUNTS), (votes, ["votes"])):
        counts = frame[columns]
        if not all(pd.api.types.is_numeric_dtype(counts[c]) for c in columns):
            raise ValueError("Counts must be numeric integers.")
        if (counts < 0).any().any() or (counts % 1 != 0).any().any():
            raise ValueError("Counts must be nonnegative integers.")
    # Meaningful for every year, including 2002-2012 where the identities below hold
    # by construction because abstentions and blank/invalid are derived.
    if (turnout.voters > turnout.registered).any():
        raise ValueError("Voters cannot exceed registered voters at a station.")
    if (turnout.valid > turnout.voters).any():
        raise ValueError("Valid ballots cannot exceed voters at a station.")
    if not (turnout.registered == turnout.abstentions + turnout.voters).all():
        raise ValueError("Registered voters must equal abstentions plus voters.")
    if not (turnout.voters == turnout.blank_invalid + turnout.valid).all():
        raise ValueError("Voters must equal blank, invalid and valid ballots.")
    if {"blank", "invalid"} <= set(turnout.columns):
        split = turnout[["blank", "invalid"]]
        if (split.isna().any(axis=1) != split.isna().all(axis=1)).any():
            raise ValueError("Blank and invalid splits must both be present or both be missing.")
        known = split.dropna()
        if (known < 0).any().any() or (known % 1 != 0).any().any():
            raise ValueError("Split ballot counts must be nonnegative integers.")
        if not (known.sum(axis=1) == turnout.loc[known.index, "blank_invalid"]).all():
            raise ValueError("Blank and invalid counts must equal the combined total.")
    summed = votes.groupby(STATION_KEY).votes.sum().rename("candidate_total")
    joined = turnout.set_index(STATION_KEY).join(summed, how="outer")
    if joined[["valid", "candidate_total"]].isna().any().any():
        raise ValueError("Turnout and candidate coverage differ.")
    if not (joined.valid == joined.candidate_total).all():
        raise ValueError("Candidate votes must sum to valid ballots at every station.")
    for frame, key, label in (
        (turnout, ["year", "department_code"], "department_name"),
        (votes, ["year", "candidate_id"], "candidate"),
    ):
        if (frame.groupby(key)[label].nunique() != 1).any():
            raise ValueError(f"Inconsistent {label} for the same identifier.")


def aggregate_results(turnout: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
    """Long-form department results, with every share divided by registered voters."""
    validate_results(turnout, votes)
    keys = ["year", "round", "department_code"]
    totals = turnout.groupby(keys, as_index=False).agg(
        **{column: (column, "sum") for column in COUNTS},
        department_name=("department_name", "first"),
        polling_stations=("station_code", "size"),
    )
    if (totals.registered <= 0).any():
        raise ValueError("Cannot calculate shares for a unit with no registered voters.")
    candidates = votes.groupby([*keys, "candidate_id", "candidate"], as_index=False).votes.sum()
    candidates["option"] = "candidate:" + candidates.candidate_id
    candidates = candidates.rename(columns={"candidate": "label", "votes": "count"})
    rows = [candidates[[*keys, "option", "label", "count"]]]
    for option, label, counts in (
        ("blank_invalid", "Blank / invalid", totals.blank_invalid),
        ("abstention", "Abstention", totals.abstentions),
    ):
        row = totals[keys].copy()
        row["option"], row["label"], row["count"] = option, label, counts
        rows.append(row)
    result = pd.concat(rows, ignore_index=True).merge(
        totals[[*keys, "department_name", "registered", "polling_stations"]],
        on=keys,
        validate="many_to_one",
    )
    result["share"] = result["count"] / result.registered
    return result.sort_values([*keys, "option"]).reset_index(drop=True)


def process_year(year: int, root: Path) -> dict:
    """Publish validated outputs only after both rounds and the baseline succeed."""
    from vote_transfer.application.baseline import evaluate_h0
    from vote_transfer.application.quality import (
        station_diagnostics,
        unit_flag_summary,
        unit_flags,
    )

    source = root / "raw" / "official" / str(year)
    manifest = json.loads((source / "manifest.json").read_text())
    records = {item["round"]: item for item in manifest["files"]}
    turnouts, candidates = [], []
    for round_number in (1, 2):
        path = source / raw_filename(year, round_number)
        if round_number not in records or sha256(path) != records[round_number]["sha256"]:
            raise ValueError(f"Raw checksum mismatch or missing provenance: {path}")
        turnout, votes = parse_official(path, year, round_number)
        turnouts.append(turnout)
        candidates.append(votes)
    turnout, votes = (
        pd.concat(turnouts, ignore_index=True),
        pd.concat(candidates, ignore_index=True),
    )
    results = aggregate_results(turnout, votes)
    evaluation = evaluate_h0(results)
    coverage = turnout.groupby(["round", "department_code"]).registered.sum().unstack("round")
    report = {
        "year": year,
        "processed_at_utc": datetime.now(UTC).isoformat(),
        "source": "Ministry original files",
        "schema_version": 2,
        "territorial_units": int(results.department_code.nunique()),
        "polling_station_round_rows": len(turnout),
        "candidate_rows": len(votes),
        "registered_by_round": {
            str(k): int(v) for k, v in turnout.groupby("round").registered.sum().items()
        },
        "units_with_registration_change": int((coverage[1] != coverage[2]).sum()),
        "checks": [
            "source checksums",
            "unique station and candidate keys",
            "nonnegative integer counts",
            "voters <= registered and valid <= voters",
            *(
                ["repeated station totals agree across candidate rows"]
                if year <= 2012
                else ["turnout accounting against published abstentions, blank and invalid"]
            ),
            "candidate vote sums",
            "two-round territorial coverage",
        ],
        "derived_fields": (
            {
                "abstentions": "registered - voters",
                "blank_invalid": "voters - valid",
            }
            if year <= 2012
            else {"blank_invalid": "blank + invalid"}
        ),
        "diagnostics": {
            "stations_by_round": station_diagnostics(turnout, votes),
            "reporting_units": unit_flag_summary(unit_flags(results, evaluation)),
        },
        "input_files": records,
        "ballot_detail": "combined_only" if year <= 2012 else "separate_blank_and_invalid",
        "geographic_labels": "codes_only" if year <= 2012 else "published_names",
        "geographic_coverage": "All reporting units in the source; coverage differs by year.",
        "reporting_unit_codes": sorted(results.department_code.unique().tolist()),
        "partial_national_coverage": year in (2002, 2007),
        "limitations": [
            "Aggregate patterns, not individual voter behaviour.",
            "Ministry codes include overseas territories and voters abroad.",
            "Shares use each round's own registered electorate; registration can change.",
            "H0 is a provisional operational definition, not a fitted transfer estimate.",
        ],
    }
    if year <= 2012:
        report["limitations"].extend(
            [
                "Historical blank/invalid splits are unavailable and remain null.",
                "Historical labels use source department codes; no modern geography join.",
            ]
        )
    if year in (2002, 2007):
        report["limitations"].append(
            "Partial national coverage: some overseas areas and voters abroad are absent. "
            "Aggregated results describe only the covered units."
        )
    parent = root / "processed"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / str(year)
    # An existing complete build is kept until all validation and staging succeed.
    with tempfile.TemporaryDirectory(dir=parent, prefix=".build-") as temporary:
        staging = Path(temporary)
        results.to_parquet(staging / "department_results.parquet", index=False)
        evaluation.to_parquet(staging / "h0_evaluation.parquet", index=False)
        report["outputs"] = {p.name: sha256(p) for p in staging.glob("*.parquet")}
        (staging / "quality_report.json").write_text(json.dumps(report, indent=2) + "\n")
        target.mkdir(exist_ok=True)
        for path in staging.iterdir():
            path.replace(target / path.name)
    interim = root / "interim" / str(year)
    interim.mkdir(parents=True, exist_ok=True)
    for name, frame in (("turnout", turnout), ("candidate_votes", votes)):
        temporary = interim / f"{name}.parquet.part"
        frame.to_parquet(temporary, index=False)
        temporary.replace(interim / f"{name}.parquet")
    return report
