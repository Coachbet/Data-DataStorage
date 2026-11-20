"""Every behavioural assumption as a transfer matrix, evaluated by one shared path.

A transfer matrix maps first-round groups (rows) to the four second-round outcomes
(columns: finalist A, finalist B, blank/invalid, abstention). Rows are nonnegative
and sum to one. Predictions are first-round shares multiplied by the matrix.

These are aggregate assumptions. A matrix that fits well does not show how any
individual voted.

Glossary
    group       a first-round option: a candidate, ``blank_invalid`` or ``abstention``
    outcome     one of the four second-round options
    retained    a group that is also an outcome; it keeps an identity row
    eliminated  a first-round candidate who is not a finalist
    finalist A  the finalist with more first-round votes over the covered areas
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from vote_transfer.application.positions import FAMILY_SCORES, family_to_unit

NON_VOTE = ("blank_invalid", "abstention")
# H2: "far" means at least this distance from both finalists, on the 0-1 scale.
# It is the original rule (two steps out of six on the 1-7 scale, decision D4), fixed
# before any poll-based result was seen.
THRESHOLD = 1 / 3
TOLERANCE = 1e-9  # scores are fractions: distances that are equal on paper must count as ties
FAR_OUTCOME = {"H1": None, "H2-abst": "abstention", "H2-blank": "blank_invalid"}
BASES = tuple(FAR_OUTCOME)  # models that read candidate scores; each is an H3 base
PARAMETER_FREE = ("H0a", "H0b", *BASES)
TIES = ("split", "abstention")
# "polls" is the main scale (candidate_scores.csv); "primary" and "alternative" are the
# hand-coded 1-7 families and their alternatives, kept as comparisons.
CODINGS = ("polls", "primary", "alternative")
MAIN_CODING = CODINGS[0]
# (coding, tie) pairs evaluated for every scored model. The first is the main analysis.
SETTINGS = (
    ("polls", "split"),
    ("polls", "abstention"),
    ("primary", "split"),
    ("primary", "abstention"),
    ("alternative", "split"),
    ("alternative", "abstention"),
)
P_GRID = np.arange(101) / 100
PREDICTION_COLUMNS = [
    "year",
    "area_code",
    "model",
    "variant",
    "train_elections",
    "outcome",
    "predicted_share",
    "actual_share",
    "registered_r2",
]


def variant_name(coding: str, tie: str) -> str:
    return f"positions={coding};tie={tie}"


MAIN_VARIANT = variant_name(*SETTINGS[0])
NO_VARIANT = "default"  # H0a and H0b read neither scores nor tie rules


def h3_name(base: str) -> str:
    return f"H3({base})"


@dataclass(frozen=True)
class Election:
    """One election as arrays: areas by first-round groups, areas by outcomes."""

    year: int
    finalists: tuple[str, str]
    groups: tuple[str, ...]
    areas: tuple[str, ...]
    first: np.ndarray  # areas x groups, first-round shares of registered voters
    actual: np.ndarray  # areas x 4, second-round shares of registered voters
    registered_r2: np.ndarray

    @property
    def outcomes(self) -> tuple[str, str, str, str]:
        return (*self.finalists, *NON_VOTE)

    @property
    def eliminated(self) -> tuple[str, ...]:
        return tuple(g for g in self.groups if g not in self.outcomes)


def build_election(results: pd.DataFrame) -> Election:
    """Reshape one election of the validated wide view; no value is altered."""
    if results.year.nunique() != 1:
        raise ValueError("Build one election at a time.")
    first, second = results[results["round"] == 1], results[results["round"] == 2]
    if set(first.department_code) != set(second.department_code):
        raise ValueError("Both rounds must cover the same territorial units.")
    finalists = second.loc[second.option.str.startswith("candidate:"), "option"].unique()
    if len(finalists) != 2:
        raise ValueError("The second round must contain exactly two finalists.")
    # Ordered with first-round information only, so the labels A and B use no outcome.
    support = first[first.option.isin(finalists)].groupby("option")["count"].sum()
    finalist_a, finalist_b = support.sort_values(ascending=False, kind="stable").index
    outcomes = [finalist_a, finalist_b, *NON_VOTE]
    wide_first = first.pivot(index="department_code", columns="option", values="share")
    wide_second = second.pivot(index="department_code", columns="option", values="share")
    wide_second = wide_second.reindex(wide_first.index)[outcomes]
    if wide_first.isna().any().any() or wide_second.isna().any().any():
        raise ValueError("Every area needs every option in both rounds.")
    registered = second.drop_duplicates("department_code").set_index("department_code").registered
    return Election(
        year=int(results.year.iloc[0]),
        finalists=(finalist_a, finalist_b),
        groups=tuple(wide_first.columns),
        areas=tuple(wide_first.index),
        first=wide_first.to_numpy(float),
        actual=wide_second.to_numpy(float),
        registered_r2=registered.reindex(wide_first.index).to_numpy(float),
    )


def election_scores(positions: pd.DataFrame, year: int, coding: str) -> dict[str, float | None]:
    """Map each candidate option to its 0-1 score, or None where the candidate is not placed.

    ``polls`` reads the poll-based scale. ``primary`` reads the hand-coded 1-7 family,
    put on the 0-1 scale. ``alternative`` replaces that family by ``alternative_family``
    on every row that lists one: a single alternative scenario, not a search over codings.
    """
    if coding not in CODINGS:
        raise ValueError(f"Unknown coding: {coding!r}. Use one of {CODINGS}.")
    scores = {}
    for row in positions[positions.year == year].itertuples():
        if coding == "polls":
            score = None if pd.isna(row.poll_score) else float(row.poll_score)
        else:
            family = None if pd.isna(row.ideology_score) else int(row.ideology_score)
            if coding == "alternative" and row.alternative_family:
                family = FAMILY_SCORES[row.alternative_family]
            score = None if family is None else family_to_unit(family)
        scores[f"candidate:{row.candidate_id}"] = score
    return scores


def at_least(distance: float, threshold: float = THRESHOLD) -> bool:
    """``distance >= threshold``, without letting rounding break the rule."""
    return distance >= threshold - TOLERANCE


def proximity_row(
    score: float | None, score_a: float, score_b: float, *, tie: str, far: str | None
) -> np.ndarray | None:
    """One eliminated group's row under H1 (``far`` is None) or H2.

    Returns None when the candidate has no score; the caller then uses the H0b row.
    """
    if tie not in TIES:
        raise ValueError(f"Unknown tie rule: {tie!r}. Use one of {TIES}.")
    if score is None:
        return None
    row = np.zeros(4)
    distance_a, distance_b = abs(score - score_a), abs(score - score_b)
    if far is not None and at_least(distance_a) and at_least(distance_b):
        row[2 + NON_VOTE.index(far)] = 1
    elif distance_a < distance_b - TOLERANCE:
        row[0] = 1
    elif distance_b < distance_a - TOLERANCE:
        row[1] = 1
    elif tie == "split":
        row[:2] = 0.5
    else:
        row[3] = 1
    return row


def transfer_tensor(
    election: Election,
    model: str,
    scores: dict[str, float | None] | None = None,
    tie: str = "split",
) -> np.ndarray:
    """Transfer matrices for every area: an (areas, groups, 4) array.

    H0 rows depend on each area's own first-round shares, so the matrix is
    area-specific; H1/H2 rows are the same everywhere except the H0b fallback.
    """
    if model not in PARAMETER_FREE:
        raise ValueError(f"Unknown model: {model!r}.")
    index = {group: i for i, group in enumerate(election.groups)}
    tensor = np.zeros((len(election.areas), len(election.groups), 4))
    for k, option in enumerate(election.outcomes):
        tensor[:, index[option], k] = 1  # retained groups stay where they were
    retained = election.first[:, [index[option] for option in election.outcomes]]
    h0b = retained.copy()
    h0b[:, 3] = 0  # H0b: no eliminated support goes to abstention
    if (h0b.sum(axis=1) <= 0).any() or (retained.sum(axis=1) <= 0).any():
        raise ValueError("H0 needs positive support among retained options.")
    h0a = retained / retained.sum(axis=1, keepdims=True)
    h0b = h0b / h0b.sum(axis=1, keepdims=True)
    if model in BASES:
        scores = scores or {}
        score_a, score_b = (scores.get(finalist) for finalist in election.finalists)
        if score_a is None or score_b is None:
            raise ValueError(f"{model} needs a score for each finalist in {election.year}.")
    for group in election.eliminated:
        if model == "H0a":
            row = h0a
        elif model == "H0b":
            row = h0b
        else:
            if group not in scores:
                raise ValueError(f"No reference row for {group} in {election.year}.")
            fixed = proximity_row(scores[group], score_a, score_b, tie=tie, far=FAR_OUTCOME[model])
            row = h0b if fixed is None else fixed
        tensor[:, index[group], :] = row
    return tensor


def transfer_matrix(
    election: Election,
    model: str,
    area: str,
    scores: dict[str, float | None] | None = None,
    tie: str = "split",
) -> pd.DataFrame:
    """One area's matrix with labelled rows and columns, for inspection and tests."""
    tensor = transfer_tensor(election, model, scores, tie)
    return pd.DataFrame(
        tensor[election.areas.index(area)], index=election.groups, columns=election.outcomes
    )


def predict(election: Election, tensor: np.ndarray) -> np.ndarray:
    """Second-round shares per area: first-round shares times the transfer matrix."""
    return np.einsum("ag,agk->ak", election.first, tensor)


def mix(base: np.ndarray, h0b: np.ndarray, p: float) -> np.ndarray:
    """H3: a fraction p does not follow the base rule and behaves as in H0b.

    Works on matrices and on predictions alike, because prediction is linear.
    """
    return (1 - p) * base + p * h0b


def primary_score(predicted: np.ndarray, election: Election) -> float:
    """Mean absolute error over four outcomes per area, weighted by round-two registration.

    Same definition as ``evaluation.weighted_area_error``; this array form exists
    so the H3 grid search stays fast. A test keeps the two in agreement.
    """
    area_error = np.abs(predicted - election.actual).mean(axis=1) * 100
    return float(area_error @ election.registered_r2 / election.registered_r2.sum())


def fit_p(training: list[tuple[np.ndarray, np.ndarray, Election]]) -> tuple[float, float]:
    """Grid search for H3's single parameter on training elections only.

    Each element is (base prediction, H0b prediction, election). The objective is
    the primary score averaged over training elections, each election counting
    once. Ties go to the smallest p.
    """
    if not training:
        raise ValueError("H3 needs at least one training election.")
    objective = [
        np.mean([primary_score(mix(base, h0b, p), election) for base, h0b, election in training])
        for p in P_GRID
    ]
    best = int(np.argmin(objective))
    return float(P_GRID[best]), float(objective[best])


def prediction_rows(
    election: Election, predicted: np.ndarray, model: str, variant: str, trained: str = ""
) -> pd.DataFrame:
    """Long rows for one model and election, in the shared predictions schema."""
    areas, outcomes = len(election.areas), len(election.outcomes)
    return pd.DataFrame(
        {
            "year": election.year,
            "area_code": np.repeat(election.areas, outcomes),
            "model": model,
            "variant": variant,
            "train_elections": trained,
            "outcome": np.tile(election.outcomes, areas),
            "predicted_share": predicted.ravel(),
            "actual_share": election.actual.ravel(),
            "registered_r2": np.repeat(election.registered_r2, outcomes).astype("int64"),
        }
    )[PREDICTION_COLUMNS]


def coding_status(positions: pd.DataFrame) -> str:
    """What every output must say about the hand-coded 1-7 comparison (decision D6)."""
    scored = positions[positions.ideology_score.notna()]
    return "reviewed coding" if scored.review_status.eq("reviewed").all() else "draft coding"


SCALE_STATUS = "poll-based scale"  # what every output says about the main positions


def evaluate_models(
    results_by_year: dict[int, pd.DataFrame], positions: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Run every model on every election; H3 is fitted leave-one-election-out.

    For H3 only held-out predictions enter the table. The fit on all elections is
    reported separately for the 2027 scenario, where no election is being scored.
    """
    elections = {year: build_election(results_by_year[year]) for year in sorted(results_by_year)}
    if len(elections) < 2:
        raise ValueError("Leave-one-election-out needs at least two elections.")
    frames, folds, fallbacks = [], [], []
    h0b = {year: predict(e, transfer_tensor(e, "H0b")) for year, e in elections.items()}
    for year, election in elections.items():
        frames.append(
            prediction_rows(
                election, predict(election, transfer_tensor(election, "H0a")), "H0a", NO_VARIANT
            )
        )
        frames.append(prediction_rows(election, h0b[year], "H0b", NO_VARIANT))
    for coding, tie in SETTINGS:
        variant = variant_name(coding, tie)
        scores = {year: election_scores(positions, year, coding) for year in elections}
        for base in BASES:
            predicted = {
                year: predict(e, transfer_tensor(e, base, scores[year], tie))
                for year, e in elections.items()
            }
            for year, election in elections.items():
                frames.append(prediction_rows(election, predicted[year], base, variant))
            for test_year in [*elections, None]:
                train_years = [year for year in elections if year != test_year]
                p, train_score = fit_p([(predicted[y], h0b[y], elections[y]) for y in train_years])
                fold = {
                    "base": base,
                    "variant": variant,
                    "test_year": test_year,
                    "train_elections": train_years,
                    "p": p,
                    "train_score_pp": train_score,
                    "heldout_score_pp": None,
                }
                if test_year is not None:
                    held_out = mix(predicted[test_year], h0b[test_year], p)
                    fold["heldout_score_pp"] = primary_score(held_out, elections[test_year])
                    frames.append(
                        prediction_rows(
                            elections[test_year],
                            held_out,
                            h3_name(base),
                            variant,
                            ",".join(map(str, train_years)),
                        )
                    )
                folds.append(fold)
        if (coding, tie) == SETTINGS[0]:
            fallbacks = [
                {"year": year, "option": option, "rule": "no score: H0b row"}
                for year, election in elections.items()
                for option in election.eliminated
                if scores[year][option] is None
            ]
    report = {
        "coding_status": SCALE_STATUS,
        "comparison_coding_status": coding_status(positions),
        "main_variant": MAIN_VARIANT,
        "elections": {
            str(year): {
                "finalist_a": election.finalists[0],
                "finalist_b": election.finalists[1],
                "areas": len(election.areas),
            }
            for year, election in elections.items()
        },
        "h0b_fallbacks": fallbacks,
        "h3_folds": folds,
    }
    return pd.concat(frames, ignore_index=True), report
