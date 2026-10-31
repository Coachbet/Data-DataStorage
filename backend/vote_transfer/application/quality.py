"""Measured data-quality diagnostics: metrics and flags, never silent removal.

Rule checks in ``processing.validate_results`` stop the pipeline. The values here
need context: an unusual reporting area is flagged and retained, because extreme
turnout in an overseas territory can be the phenomenon rather than an error.
"""

from __future__ import annotations

import pandas as pd

from vote_transfer.infrastructure.official import STATION_KEY

IQR_FACTOR = 1.5


def iqr_outliers(values: pd.Series) -> pd.Series:
    """Tukey fences: a robust diagnostic flag, not a deletion rule."""
    q1, q3 = values.quantile([0.25, 0.75])
    spread = q3 - q1
    return (values < q1 - IQR_FACTOR * spread) | (values > q3 + IQR_FACTOR * spread)


def territory_type(code: str) -> str:
    """Ministry codes: ZZ is voters abroad, other Z* codes are overseas areas."""
    if code == "ZZ":
        return "abroad"
    return "overseas" if code.startswith("Z") else "metropolitan"


def station_diagnostics(turnout: pd.DataFrame, votes: pd.DataFrame) -> dict:
    """Completeness, uniqueness, validity and station-level unusual values per round."""
    report = {}
    for round_number, stations in turnout.groupby("round"):
        candidates = votes[votes["round"] == round_number]
        registered = stations.registered
        turnout_rate = (stations.voters / registered).where(registered > 0)
        report[str(round_number)] = {
            "station_rows": len(stations),
            "candidate_rows": len(candidates),
            "completeness_required_fields_pct": round(
                100 * stations[["registered", "voters", "valid"]].notna().all(axis=1).mean(), 2
            ),
            "completeness_blank_invalid_split_pct": round(
                100 * stations[["blank", "invalid"]].notna().all(axis=1).mean(), 2
            ),
            "duplicate_station_keys": int(stations.duplicated(STATION_KEY).sum()),
            "duplicate_candidate_keys": int(
                candidates.duplicated([*STATION_KEY, "candidate_id"]).sum()
            ),
            "stations_with_zero_registered": int((registered == 0).sum()),
            "stations_with_zero_voters": int(((stations.voters == 0) & (registered > 0)).sum()),
            "stations_with_zero_valid_votes": int(
                ((stations.valid == 0) & (stations.voters > 0)).sum()
            ),
            "registered_per_station": {
                "min": int(registered.min()),
                "median": float(registered.median()),
                "max": int(registered.max()),
            },
            "turnout_iqr_outlier_stations": int(iqr_outliers(turnout_rate.dropna()).sum()),
        }
    return report


def unit_flags(results: pd.DataFrame, evaluation: pd.DataFrame) -> pd.DataFrame:
    """One row per election and reporting area with context flags for analysis.

    Flags are computed within each election. The response is always to retain the
    area; analyses can compare results with and without flagged areas.
    """
    keys = ["year", "department_code"]
    units = results.drop_duplicates([*keys, "round"]).pivot_table(
        index=keys, columns="round", values="registered"
    )
    frame = pd.DataFrame(index=units.index)
    frame["registration_change_pct"] = 100 * (units[2] - units[1]) / units[1]
    abstention = results[(results.option == "abstention") & (results["round"] == 1)]
    frame["abstention_r1"] = abstention.set_index(keys).share
    errors = evaluation.groupby(keys).absolute_error_pp.mean()
    frame["h0_mean_error_pp"] = errors
    frame = frame.reset_index()
    frame["territory"] = frame.department_code.map(territory_type)
    for column, flag in (
        ("abstention_r1", "flag_abstention_r1"),
        ("registration_change_pct", "flag_registration_change"),
        ("h0_mean_error_pp", "flag_h0_error"),
    ):
        frame[flag] = frame.groupby("year")[column].transform(iqr_outliers).astype(bool)
    return frame


def unit_flag_summary(flags: pd.DataFrame) -> dict:
    """Compact, JSON-ready listing of flagged areas for the quality report."""
    summary = {"method": f"Tukey IQR fences (factor {IQR_FACTOR}) within each election"}
    summary["response"] = "flag and retain; no area is removed"
    summary["territories"] = flags.territory.value_counts().sort_index().to_dict()
    for flag in ("flag_abstention_r1", "flag_registration_change", "flag_h0_error"):
        summary[flag] = sorted(flags.loc[flags[flag], "department_code"].tolist())
    return summary
