"""Hypothetical runoffs on the 2022 first-round electorate. Not a forecast.

No 2027 first-round data exists. A scenario takes the 2022 first-round results by
area as the electorate, lets the user name two 2022 candidates as stand-ins for
the finalists, and applies one evaluated assumption. The output says what that
assumption implies for that electorate, nothing about a future election.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vote_transfer.application.models import (
    BASES,
    MAIN_CODING,
    MAIN_VARIANT,
    NON_VOTE,
    PARAMETER_FREE,
    Election,
    election_scores,
    h3_name,
    mix,
    predict,
    transfer_tensor,
)

SCENARIO_YEAR = 2022
SCENARIO_MODELS = (*PARAMETER_FREE, *(h3_name(base) for base in BASES))
# Team decision: the default is not the lowest five-election mean (H1), because that
# lead comes from one election. H0b needs no candidate coding and no fitted parameter.
DEFAULT_MODEL = "H0b"
LIMITS = (
    "Limits of this page: finalists are chosen among 2022 candidates only, not political "
    "families, and no map is shown because the repository holds no boundary data."
)
BANNER = (
    "Hypothetical scenario on the 2022 electorate — not a forecast. It applies one "
    "assumption to 2022 first-round results; it uses no 2027 data and no polls."
)


def scenario_candidates(results: pd.DataFrame) -> pd.DataFrame:
    """First-round candidates of the scenario electorate, largest first."""
    first = results[(results["round"] == 1) & results.option.str.startswith("candidate:")]
    return (
        first.groupby(["option", "label"], as_index=False)["count"]
        .sum()
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )


def scenario_election(results: pd.DataFrame, finalists: tuple[str, str]) -> Election:
    """The first round as an election whose finalists are chosen, with no second round."""
    first = results[results["round"] == 1]
    candidates = set(first.option[first.option.str.startswith("candidate:")])
    if len(set(finalists)) != 2 or not set(finalists) <= candidates:
        raise ValueError("Choose two different first-round candidates as finalists.")
    support = first[first.option.isin(finalists)].groupby("option")["count"].sum()
    ordered = tuple(support.sort_values(ascending=False, kind="stable").index)
    wide = first.pivot(index="department_code", columns="option", values="share")
    registered = first.drop_duplicates("department_code").set_index("department_code").registered
    return Election(
        year=int(first.year.iloc[0]),
        finalists=ordered,
        groups=tuple(wide.columns),
        areas=tuple(wide.index),
        first=wide.to_numpy(float),
        actual=np.full((len(wide), 4), np.nan),  # nothing was observed: it never happened
        # No second round exists, so areas are weighted by first-round registration.
        registered_r2=registered.reindex(wide.index).to_numpy(float),
    )


def simulate_runoff(
    results: pd.DataFrame,
    finalists: tuple[str, str],
    model: str,
    positions: pd.DataFrame,
    report: dict,
) -> dict:
    """Area-level and pooled shares implied by one assumption for a chosen runoff.

    H3 uses the share ``p`` fitted on all five historical elections, read from the
    evaluation report. Scores come from the 2022 rows of the candidate table.
    """
    if model not in SCENARIO_MODELS:
        raise ValueError(f"Unknown model: {model!r}.")
    election = scenario_election(results, finalists)
    scores = election_scores(positions, election.year, MAIN_CODING)
    h0b = predict(election, transfer_tensor(election, "H0b"))
    p = None
    if model.startswith("H3"):
        base = model[3:-1]
        p = next(
            fold["p"]
            for fold in report["h3_folds"]
            if fold["base"] == base
            and fold["variant"] == MAIN_VARIANT
            and fold["test_year"] is None
        )
        predicted = mix(predict(election, transfer_tensor(election, base, scores)), h0b, p)
    else:
        predicted = predict(election, transfer_tensor(election, model, scores))
    names = (
        results.drop_duplicates("department_code")
        .set_index("department_code")
        .department_name.reindex(election.areas)
    )
    columns = ["finalist_a", "finalist_b", *NON_VOTE]
    areas = pd.DataFrame(predicted * 100, columns=[f"{c}_pct" for c in columns])
    areas.insert(0, "registered", election.registered_r2.astype("int64"))
    areas.insert(0, "area_name", names.to_numpy())
    areas.insert(0, "area_code", election.areas)
    weights = election.registered_r2 / election.registered_r2.sum()
    pooled = dict(zip(columns, (weights @ predicted * 100).tolist(), strict=True))
    valid = pooled["finalist_a"] + pooled["finalist_b"]
    return {
        "model": model,
        "p": p,
        "finalist_a": election.finalists[0],
        "finalist_b": election.finalists[1],
        "pooled_pct": pooled,
        "finalist_a_valid_pct": 100 * pooled["finalist_a"] / valid,
        "areas": areas,
    }


def simulate_all(
    results: pd.DataFrame,
    finalists: tuple[str, str],
    positions: pd.DataFrame,
    report: dict,
) -> pd.DataFrame:
    """Pooled shares (%) under every assumption: one row per outcome, one column per model."""
    columns = {
        model: simulate_runoff(results, finalists, model, positions, report)["pooled_pct"]
        for model in SCENARIO_MODELS
    }
    return pd.DataFrame(columns)
