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
    non_votes = {"abstention", "blank_invalid"}
    for _, options in evaluation.groupby("year").option.unique().items():
        finalists = set(options) - non_votes
        if len(finalists) != 2 or any(not x.startswith("candidate:") for x in finalists):
            raise ValueError("Expected two finalists plus abstention and blank/invalid.")
        if not non_votes <= set(options):
            raise ValueError("Expected two finalists plus abstention and blank/invalid.")
    units = evaluation.groupby(keys).agg(
        outcomes=("option", "size"),
        registrations=("registered", "nunique"),
        actual=("actual_share", "sum"),
        predicted=("predicted_share", "sum"),
    )
    # With unique keys and exactly four options per election, four rows means all four.
    if (units.outcomes != 4).any():
        raise ValueError("Each area must contain all four second-round outcomes.")
    if (units.registrations != 1).any():
        raise ValueError("An area's repeated registration totals must agree.")
    if ((units[["actual", "predicted"]] - 1).abs() > 1e-8).any().any():
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


def score_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Primary score per model, variant and election, from the long predictions table.

    Every model goes through ``weighted_area_error``: one scoring rule for all.
    """
    # ``weighted_area_error`` expects the column names of the wide results table.
    renamed = predictions.rename(
        columns={"area_code": "department_code", "outcome": "option", "registered_r2": "registered"}
    )
    scores = [
        weighted_area_error(frame).assign(model=model, variant=variant)
        for (model, variant), frame in renamed.groupby(["model", "variant"], sort=True)
    ]
    table = pd.concat(scores, ignore_index=True).rename(columns={"weighted_mae_pp": "score_pp"})
    return table[["model", "variant", "year", "score_pp", "registered", "territorial_units"]]
