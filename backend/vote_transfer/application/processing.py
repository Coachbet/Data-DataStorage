"""Validation and aggregation shared by the CLI and the Streamlit application."""

from __future__ import annotations

import json
import tempfile
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


AREA_KEY = ["year", "round", "area_code"]


def aggregate_tables(
    turnout: pd.DataFrame, votes: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Normalised area-level tables: each fact is stated once.

    ``areas`` holds what belongs to an area and round (its denominator, its number
    of stations, the published blank/invalid split). ``outcomes`` holds one count per
    option. ``options`` holds each option's display label. Shares are not stored.
    """
    validate_results(turnout, votes)
    stations = turnout.rename(columns={"department_code": "area_code"})
    grouped = stations.groupby(AREA_KEY)
    totals = grouped.agg(
        **{column: (column, "sum") for column in COUNTS},
        area_name=("department_name", "first"),
        polling_stations=("station_code", "size"),
    )
    for column in ("blank", "invalid"):
        # min_count keeps "not published" (null) distinct from a published zero.
        totals[column] = (
            grouped[column].sum(min_count=1).astype("Int64")
            if column in stations
            else pd.array([pd.NA] * len(totals), dtype="Int64")
        )
    totals = totals.reset_index()
    if (totals.registered <= 0).any():
        raise ValueError("Cannot calculate shares for a unit with no registered voters.")
    candidates = (
        votes.rename(columns={"department_code": "area_code"})
        .groupby([*AREA_KEY, "candidate_id", "candidate"], as_index=False)
        .votes.sum()
    )
    candidates["option"] = "candidate:" + candidates.candidate_id
    candidates = candidates.rename(columns={"candidate": "label", "votes": "count"})
    rows = [candidates[[*AREA_KEY, "option", "count"]]]
    labels = [candidates[["year", "option", "label"]].drop_duplicates()]
    for option, label, counts in (
        ("blank_invalid", "Blank / invalid", totals.blank_invalid),
        ("abstention", "Abstention", totals.abstentions),
    ):
        row = totals[AREA_KEY].copy()
        row["option"], row["count"] = option, counts
        rows.append(row)
        labels.append(
            pd.DataFrame({"year": totals.year.unique(), "option": option, "label": label})
        )
    areas = totals[[*AREA_KEY, "area_name", "registered", "polling_stations", "blank", "invalid"]]
    outcomes = pd.concat(rows, ignore_index=True).sort_values([*AREA_KEY, "option"])
    options = pd.concat(labels, ignore_index=True).sort_values(["year", "option"])
    tables = (
        areas.reset_index(drop=True),
        outcomes.reset_index(drop=True),
        options.reset_index(drop=True),
    )
    validate_tables(*tables)
    return tables


def validate_tables(areas: pd.DataFrame, outcomes: pd.DataFrame, options: pd.DataFrame) -> None:
    """Enforce the keys and identities a relational schema would declare."""
    if areas.empty or outcomes.empty or options.empty:
        raise ValueError("Processed tables must be nonempty.")
    if areas.duplicated(AREA_KEY).any():
        raise ValueError("Duplicate area and round.")
    if outcomes.duplicated([*AREA_KEY, "option"]).any():
        raise ValueError("Duplicate outcome for an area and round.")
    if options.duplicated(["year", "option"]).any():
        raise ValueError("Duplicate option label.")
    if (areas.registered <= 0).any() or (outcomes["count"] < 0).any():
        raise ValueError("Registered voters must be positive and counts nonnegative.")
    labelled = outcomes[["year", "option"]].merge(options, how="left", on=["year", "option"])
    if labelled.label.isna().any():
        raise ValueError("Every outcome option needs a label.")
    totals = outcomes.groupby(AREA_KEY, as_index=False)["count"].sum()
    joined = areas.merge(totals, how="outer", on=AREA_KEY, indicator=True)
    if (joined._merge != "both").any():
        raise ValueError("Areas and outcomes cover different areas or rounds.")
    if (joined["count"] != joined.registered).any():
        raise ValueError("Outcome counts must sum to registered voters in every area.")
    split = areas[["blank", "invalid"]]
    if (split.isna().any(axis=1) != split.isna().all(axis=1)).any():
        raise ValueError("Blank and invalid counts must both be present or both be missing.")
    combined = outcomes[outcomes.option == "blank_invalid"].set_index(AREA_KEY)["count"]
    published = areas.dropna(subset=["blank", "invalid"]).set_index(AREA_KEY)
    if (published.blank + published.invalid != combined.reindex(published.index)).any():
        raise ValueError("Blank and invalid counts must equal the combined outcome.")


def results_view(
    areas: pd.DataFrame, outcomes: pd.DataFrame, options: pd.DataFrame
) -> pd.DataFrame:
    """The wide table used by the app: one row per outcome, with its share computed.

    This is a view. ``registered`` repeats on every outcome row here, so sum it once
    per area and round, or read it from ``areas`` instead.
    """
    validate_tables(areas, outcomes, options)
    view = outcomes.merge(options, on=["year", "option"], validate="many_to_one").merge(
        areas[[*AREA_KEY, "area_name", "registered", "polling_stations"]],
        on=AREA_KEY,
        validate="many_to_one",
    )
    view = view.rename(columns={"area_code": "department_code", "area_name": "department_name"})
    view["share"] = view["count"] / view.registered
    keys = ["year", "round", "department_code"]
    columns = [*keys, "option", "label", "count", "department_name", "registered"]
    return (
        view[[*columns, "polling_stations", "share"]]
        .sort_values([*keys, "option"])
        .reset_index(drop=True)
    )


def aggregate_results(turnout: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
    """Long-form area results, with every share divided by registered voters."""
    return results_view(*aggregate_tables(turnout, votes))


def process_year(year: int, root: Path) -> dict:
    """Publish validated outputs only after both rounds and the baseline succeed."""
    from vote_transfer.application.baseline import evaluate_h0
    from vote_transfer.application.quality import (
        station_diagnostics,
        unit_flag_summary,
        unit_flags,
    )

    source = root / "raw" / "official" / str(year)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
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
    areas, outcomes, options = aggregate_tables(turnout, votes)
    results = results_view(areas, outcomes, options)
    evaluation = evaluate_h0(results)  # for the diagnostics only; not stored
    coverage = turnout.groupby(["round", "department_code"]).registered.sum().unstack("round")
    report = {
        "year": year,
        "source": "Ministry original files",
        # No wall-clock time: a rebuild from the same raw bytes must be byte-identical.
        # Provenance is the raw hashes and retrieval dates in the acquisition manifests.
        "schema_version": 4,
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
        for name, table in (("areas", areas), ("outcomes", outcomes), ("options", options)):
            table.to_parquet(staging / f"{name}.parquet", index=False)
        report["outputs"] = {p.name: sha256(p) for p in staging.glob("*.parquet")}
        (staging / "quality_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
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
