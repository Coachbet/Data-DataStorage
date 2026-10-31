"""Evaluate territorial accuracy before aggregation, using round-two registration."""

import math

import pandas as pd


def area_errors(evaluation: pd.DataFrame) -> pd.DataFrame:
    """Return four-outcome MAE and one registration weight per election and area."""
    keys = ["year", "department_code"]
    required = {*keys, "option", "registered", "actual_share", "predicted_share"}
    if not required <= set(evaluation) or evaluation.empty:
        raise ValueError("Expected nonempty territorial evaluation data.")
    if evaluation[list(required)].isna().any().any():
        raise ValueError("Evaluation keys and values cannot be missing.")
    if evaluation.duplicated([*keys, "option"]).any():
        raise ValueError("Duplicate territorial outcomes.")
    numeric = evaluation[["registered", "actual_share", "predicted_share"]]
    if not numeric.map(math.isfinite).all().all():
        raise ValueError("Evaluation values must be finite.")
    if (evaluation.registered <= 0).any():
        raise ValueError("Registered-voter weights must be positive.")
    if not evaluation[["actual_share", "predicted_share"]].map(lambda x: 0 <= x <= 1).all().all():
        raise ValueError("Evaluation shares must lie between zero and one.")
    for _, election in evaluation.groupby("year"):
        finalists = set(election.option) - {"abstention", "blank_invalid"}
        if len(finalists) != 2 or any(not x.startswith("candidate:") for x in finalists):
            raise ValueError("Expected two finalists plus abstention and blank/invalid.")
        for _, unit in election.groupby("department_code"):
            if set(unit.option) != finalists | {"abstention", "blank_invalid"}:
                raise ValueError("Each area must contain all four second-round outcomes.")
            if unit.registered.nunique() != 1:
                raise ValueError("An area's repeated registration totals must agree.")
            totals = unit[["actual_share", "predicted_share"]].sum()
            if not all(math.isclose(total, 1, abs_tol=1e-8) for total in totals):
                raise ValueError("Each area's observed and predicted shares must sum to one.")
    frame = evaluation.copy()
    frame["error_pp"] = (frame.predicted_share - frame.actual_share).abs() * 100
    errors = frame.groupby(keys, as_index=False).agg(
        registered=("registered", "first"), mean_error_pp=("error_pp", "mean")
    )
    errors["weight"] = errors.registered / errors.groupby("year").registered.transform("sum")
    errors["weighted_error_pp"] = errors.weight * errors.mean_error_pp
    return errors


def weighted_area_error(evaluation: pd.DataFrame) -> pd.DataFrame:
    """Average local errors; signed errors in different areas cannot cancel."""
    return (
        area_errors(evaluation)
        .groupby("year", as_index=False)
        .agg(
            weighted_mae_pp=("weighted_error_pp", "sum"),
            registered=("registered", "sum"),
            territorial_units=("department_code", "size"),
        )
    )
