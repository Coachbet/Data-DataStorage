"""Presentation-ready summaries calculated from verified aggregate data."""

import pandas as pd

from vote_transfer.application.baseline import national_evaluation
from vote_transfer.application.evaluation import area_errors


def outcome_label(option: str, published_label: str) -> str:
    """Explain non-voting outcomes while retaining candidate names from the source."""
    return {
        "abstention": "Did not vote",
        "blank_invalid": "Blank or invalid ballot",
    }.get(option, published_label.title())


def round_summary(results: pd.DataFrame, round_number: int) -> dict:
    """Sum each territory's denominator once, rather than once per candidate."""
    current = results[results["round"] == round_number]
    registered = int(current.drop_duplicates("department_code").registered.sum())
    if registered <= 0:
        raise ValueError("No registered electorate is available for this selection.")
    totals = current.groupby(["option", "label"], as_index=False)["count"].sum()
    totals["share_pct"] = totals["count"] / registered * 100
    totals["outcome"] = [outcome_label(row.option, row.label) for row in totals.itertuples()]
    totals = totals.sort_values("count", ascending=False).reset_index(drop=True)
    abstention = float(totals.loc[totals.option == "abstention", "share_pct"].iloc[0])
    blank = float(totals.loc[totals.option == "blank_invalid", "share_pct"].iloc[0])
    return {
        "totals": totals,
        "registered": registered,
        "turnout_pct": 100 - abstention,
        "abstention_pct": abstention,
        "blank_invalid_pct": blank,
        "units": current.department_code.nunique(),
        "reading": (
            f"Out of every 100 registered voters in this selection, about "
            f"{100 - abstention:.1f} voted and {abstention:.1f} did not. "
            f"Of the full registered electorate, {blank:.1f}% cast a blank or invalid ballot."
        ),
    }


def model_summary(evaluation: pd.DataFrame) -> dict:
    """Describe weighted model errors without interpreting them as individual transfers."""
    errors = area_errors(evaluation)
    if errors.year.nunique() != 1:
        raise ValueError("Select one election for a model summary.")
    comparison = national_evaluation(evaluation)
    comparison["outcome"] = [
        outcome_label(row.option, row.label) for row in comparison.itertuples()
    ]
    largest = comparison.loc[comparison.absolute_error_pp.idxmax()]
    gap = float(largest.absolute_error_pp)
    direction = "above" if largest.predicted_share >= largest.actual_share else "below"
    label = largest.outcome if largest.option.startswith("candidate:") else largest.outcome.lower()
    reading = (
        f"The largest gap is for {label}: "
        f"H0 gives {largest.predicted_share * 100:.1f}% versus an observed "
        f"{largest.actual_share * 100:.1f}%. That is {gap:.1f} percentage points {direction} "
        "the observed share."
    )
    return {
        "comparison": comparison,
        "area_errors": errors,
        "weighted_mean_error_pp": float(errors.weighted_error_pp.sum()),
        "mean_error_pp": float(comparison.absolute_error_pp.mean()),
        "largest_error_pp": gap,
        "reading": reading,
    }
