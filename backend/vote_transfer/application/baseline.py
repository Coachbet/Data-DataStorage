"""A parameter-free, first-round-only operational definition of H0."""

import math

import pandas as pd


def predict_h0(first_round: dict[str, float], finalists: tuple[str, str]) -> dict[str, float]:
    """Keep retained groups; allocate eliminated support like the retained electorate.

    Retained options are the two finalists, blank/invalid and abstention.
    Their first-round shares determine allocation weights. No second-round vote
    counts or fitted parameters enter this baseline.
    """
    if len(set(finalists)) != 2 or any(not x.startswith("candidate:") for x in finalists):
        raise ValueError("Choose two distinct candidate finalists.")
    options = (*finalists, "blank_invalid", "abstention")
    if not set(options) <= first_round.keys():
        raise ValueError("First-round shares must contain both finalists and non-voting options.")
    if any(not math.isfinite(x) or x < 0 for x in first_round.values()):
        raise ValueError("Shares must be finite and nonnegative.")
    if not math.isclose(sum(first_round.values()), 1, abs_tol=1e-8):
        raise ValueError("First-round shares must sum to one.")
    retained = sum(first_round[option] for option in options)
    if retained <= 0:
        raise ValueError("H0 needs positive support among retained options.")
    return {option: first_round[option] / retained for option in options}


def evaluate_h0(results: pd.DataFrame) -> pd.DataFrame:
    """Compare per-unit shares; fail if either round or any reporting unit is missing."""
    if results.empty or results.duplicated(["year", "round", "department_code", "option"]).any():
        raise ValueError("Expected unique, nonempty department results.")
    rows = []
    for year, election in results.groupby("year"):
        first, second = election[election["round"] == 1], election[election["round"] == 2]
        if first.empty or set(first.department_code) != set(second.department_code):
            raise ValueError("Both rounds must cover the same territorial units.")
        finalists = tuple(
            sorted(second.loc[second.option.str.startswith("candidate:"), "option"].unique())
        )
        if len(finalists) != 2:
            raise ValueError("The second round must contain exactly two finalists.")
        for code, actual in second.groupby("department_code"):
            observed_options = set(actual.option)
            if observed_options != {*finalists, "blank_invalid", "abstention"}:
                raise ValueError("Incomplete second-round outcomes.")
            if not math.isclose(actual.share.sum(), 1, abs_tol=1e-8):
                raise ValueError("Second-round shares must sum to one.")
            inputs = first[first.department_code == code].set_index("option").share.to_dict()
            prediction = predict_h0(inputs, finalists)
            for record in actual.to_dict("records"):
                predicted = prediction[record["option"]]
                rows.append(
                    {
                        "year": year,
                        "department_code": code,
                        "department_name": record["department_name"],
                        "option": record["option"],
                        "label": record["label"],
                        "registered": record["registered"],
                        "actual_share": record["share"],
                        "predicted_share": predicted,
                        "absolute_error_pp": abs(predicted - record["share"]) * 100,
                    }
                )
    return pd.DataFrame(rows)


def national_evaluation(evaluation: pd.DataFrame) -> pd.DataFrame:
    """Weight both sets of shares by round-two registration within the covered units."""
    frame = evaluation.copy()
    for column in ("actual_share", "predicted_share"):
        frame[column] *= frame.registered
    result = frame.groupby(["year", "option", "label"], as_index=False)[
        ["registered", "actual_share", "predicted_share"]
    ].sum()
    for column in ("actual_share", "predicted_share"):
        result[column] /= result.registered
    result["absolute_error_pp"] = (result.predicted_share - result.actual_share).abs() * 100
    return result
