"""Wording and shapes for the site, derived from generated results only.

Nothing here computes a new result. These helpers format numbers one way, turn
the comparison table into sentences whose claims are checked against the data,
and reshape existing tables for charts.
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
    transfer_tensor,
)

ROLES = ("finalist_a", "finalist_b", "blank_invalid", "abstention")
OUTLIER = "2002"
NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight")


# --- Numbers ---------------------------------------------------------------------------


def fmt_pp(value: float, signed: bool = False, digits: int = 1) -> str:
    """Percentage points: ``4.3 pp``; signed errors read ``+4.3 pp`` with a true minus."""
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace("-", "−") + " pp"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def fmt_int(value: float) -> str:
    return f"{int(value):,}"


def count_of(k: int, n: int) -> str:
    """'all five', 'four of five', 'none of five': counts as a reader says them."""
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    if k == n:
        return f"all {word}"
    if k == 0:
        return f"none of the {word}"
    return f"{NUMBER_WORDS[k] if k < len(NUMBER_WORDS) else k} of {word}"


def join_years(years: list[str]) -> str:
    if len(years) <= 1:
        return "".join(years)
    return ", ".join(years[:-1]) + " and " + years[-1]


# --- The answer ------------------------------------------------------------------------


def election_columns(comparison: pd.DataFrame) -> list[str]:
    return [column for column in comparison.columns if column.isdigit()]


def answer(comparison: pd.DataFrame) -> dict:
    """The current answer to the research question, in sentences the table supports.

    Every clause is conditional on the comparison table, so a rerun with reviewed
    codes cannot leave a sentence that the numbers contradict.
    """
    years = election_columns(comparison)
    n, models = len(years), len(comparison)
    without = f"mean_without_{OUTLIER}"
    best, best_without = comparison["mean"].idxmin(), comparison[without].idxmin()
    h0a, h0b = comparison.loc["H0a"], comparison.loc["H0b"]
    baseline_wins = sum(h0b[y] < h0a[y] for y in years)
    beats_h0b = [y for y in years if comparison.loc[best, y] < h0b[y]]
    stable = best == best_without
    baseline = (
        f"The second baseline, H0b, is closer to the observed result than the original "
        f"baseline H0a in {count_of(baseline_wins, n)} elections "
        f"({fmt_pp(h0b['mean'])} against {fmt_pp(h0a['mean'])} on average)."
    )
    if stable:
        headline = f"{best} is the closest assumption, with and without {OUTLIER}."
        lead = (
            f"{best} has the lowest average error over the {NUMBER_WORDS[n]} elections "
            f"({fmt_pp(comparison.loc[best, 'mean'])}) and keeps the first rank when "
            f"{OUTLIER} is set aside."
        )
        title = f"{best} has the lowest average error, with and without {OUTLIER}"
    else:
        headline = "No assumption explains every election best."
        only = f"only in {join_years(beats_h0b)}" if beats_h0b else "in no election"
        lead = (
            f"{best} has the lowest average error over the {NUMBER_WORDS[n]} elections "
            f"({fmt_pp(comparison.loc[best, 'mean'])}), but it beats H0b {only}. "
            f"Without {OUTLIER} it ranks "
            f"{int(comparison.loc[best, f'rank_without_{OUTLIER}'])} of {models} and the "
            f"lowest average belongs to {best_without} "
            f"({fmt_pp(comparison.loc[best_without, without])})."
        )
        title = (
            f"H0b is closer than H0a in {count_of(baseline_wins, n)} elections; {best} leads {only}"
        )
    return {
        "headline": headline,
        "sentences": [lead, baseline],
        "chart_title": title,
        "best": best,
        "best_without_outlier": best_without,
        "stable": stable,
    }


def key_findings(comparison: pd.DataFrame, errors: pd.DataFrame, threshold: pd.DataFrame) -> list:
    """Three findings, each a statement the tables support, with where to check it."""
    years = election_columns(comparison)
    n = len(years)
    abstention = errors[(errors.model == "H0a") & (errors.role == "abstention")].signed_error_pp
    over = int((abstention > 0).sum())
    h0b_wins = sum(comparison.loc["H0b", y] < comparison.loc["H0a", y] for y in years)
    findings = [
        {
            "title": "The original baseline fails on abstention."
            if over == n
            else "The original baseline misjudges abstention.",
            "body": (
                f"H0a predicts more abstention than was observed in {count_of(over, n)} "
                f"elections, by {abstention.min():.1f} to {fmt_pp(abstention.max())}. "
                f"Removing that single channel (H0b) lowers the error in "
                f"{count_of(h0b_wins, n)}."
            ),
            "evidence": "Evidence, section 3: where each assumption misses",
        }
    ]
    h1, h0b = comparison.loc["H1"], comparison.loc["H0b"]
    h1_wins = [y for y in years if h1[y] < h0b[y]]
    largest = max(years, key=lambda y: h0b[y] - h1[y])
    findings.append(
        {
            "title": f"Ideological proximity explains {largest}, not the other elections."
            if h1_wins == [largest]
            else "Ideological proximity helps in some elections only.",
            "body": (
                f"In {largest}, H1 (each group goes to the nearest finalist) scores "
                f"{fmt_pp(h1[largest])} against {fmt_pp(h0b[largest])} for H0b. It is closer "
                f"than H0b in {count_of(len(h1_wins), n)} elections."
            ),
            "evidence": "Evidence, section 2: the comparison table",
        }
    )
    top = threshold.sort_values("exactly_on_threshold_pct", ascending=False).head(2)
    top = top.sort_values("year")
    worst = comparison["mean"].nlargest(2).index.tolist()
    h2_worst = set(worst) == {"H2-abst", "H2-blank"}
    findings.append(
        {
            "title": "The distance threshold fails for an arithmetic reason."
            if h2_worst
            else "The distance threshold moves large groups in one piece.",
            "body": (
                f"In {join_years([str(y) for y in top.year])}, "
                f"{' and '.join(fmt_pct(v) for v in top.exactly_on_threshold_pct)} of registered "
                "voters belong to groups exactly on the threshold. H2 sends all of them to a "
                "non-vote"
                + (
                    f", and its two variants have the highest average errors "
                    f"({fmt_pp(comparison.loc['H2-abst', 'mean'])} and "
                    f"{fmt_pp(comparison.loc['H2-blank', 'mean'])})."
                    if h2_worst
                    else "."
                )
            ),
            "evidence": "Evidence, section 4: what the threshold removes",
        }
    )
    return findings


# --- Shapes for charts -----------------------------------------------------------------


def outcome_roles(results: pd.DataFrame) -> dict[str, str]:
    """Map each option of one election to its role; finalist A led the first round."""
    first, second = results[results["round"] == 1], results[results["round"] == 2]
    finalists = second.loc[second.option.str.startswith("candidate:"), "option"].unique()
    support = first[first.option.isin(finalists)].groupby("option")["count"].sum()
    ordered = list(support.sort_values(ascending=False, kind="stable").index)
    roles = dict(zip(ordered, ROLES[:2], strict=False))
    return roles | {option: option for option in NON_VOTE}


def rounds_side_by_side(results: pd.DataFrame, roles: dict[str, str]) -> pd.DataFrame:
    """Both rounds as shares of each round's registered voters, in five segments."""
    rows = []
    for number in (1, 2):
        current = results[results["round"] == number]
        registered = current.drop_duplicates("department_code").registered.sum()
        role = current.option.map(roles).fillna("other")
        shares = current.groupby(role)["count"].sum() / registered * 100
        for segment in (*ROLES[:2], "other", *ROLES[2:]):
            rows.append(
                {"row": f"Round {number}", "segment": segment, "pct": float(shares.get(segment, 0))}
            )
    return pd.DataFrame(rows)


def ladder_example(election: Election, positions: pd.DataFrame, report: dict) -> dict:
    """Where each assumption sends the largest eliminated group of one election.

    The row of the transfer matrix for that group, pooled over areas with the
    group's own size as weight. H3 uses the share fitted with this election held out.
    """
    scores = election_scores(positions, election.year, MAIN_CODING)
    weights = election.registered_r2 / election.registered_r2.sum()
    index = {group: i for i, group in enumerate(election.groups)}
    scored = [g for g in election.eliminated if scores.get(g) is not None]
    group = max(scored, key=lambda g: float(weights @ election.first[:, index[g]]))
    mass = weights * election.first[:, index[group]]

    def pooled(model: str) -> np.ndarray:
        return mass @ transfer_tensor(election, model, scores)[:, index[group], :] / mass.sum()

    rows = {model: pooled(model) for model in PARAMETER_FREE}
    shares = {}
    for base in BASES:
        p = next(
            fold["p"]
            for fold in report["h3_folds"]
            if fold["base"] == base
            and fold["variant"] == MAIN_VARIANT
            and fold["test_year"] == election.year
        )
        rows[h3_name(base)] = mix(rows[base], rows["H0b"], p)
        shares[h3_name(base)] = p
    table = pd.DataFrame(rows, index=ROLES).T * 100
    return {
        "group": group,
        "group_pct": float(mass.sum() * 100),
        "group_score": scores[group],
        "finalist_scores": tuple(scores[f] for f in election.finalists),
        "rows": table,
        "p": shares,
    }
