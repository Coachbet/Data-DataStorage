"""Review kit for the hand-coded candidate table: blind sheets, agreement, quality checks.

The kit measures the table; it never fills it. Coding is a human task.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from vote_transfer.application.positions import FAMILY_SCORES

UNCLASSIFIED = "Unclassified"
LABELS = [*FAMILY_SCORES, UNCLASSIFIED]
# Columns a coder must not see: the existing codes and any text that reveals them.
BLIND_COLUMNS = (
    "political_family",
    "ideology_score",
    "alternative_family",
    "review_status",
    "classification_note",
)
SHEET_KEY = ["year", "candidate_id"]
SHEET_COLUMNS = [
    *SHEET_KEY,
    "candidate_name",
    "party_abbreviation",
    "party_name",
    "source_ids",
    "political_family",
    "coder_note",
]


def coding_sheet(positions: pd.DataFrame) -> pd.DataFrame:
    """The blind template: identification and sources, with the code left empty."""
    sheet = positions.drop(columns=list(BLIND_COLUMNS)).copy()
    sheet["political_family"] = ""
    sheet["coder_note"] = ""
    return sheet[SHEET_COLUMNS].reset_index(drop=True)


def load_coding_sheet(path: Path, positions: pd.DataFrame) -> pd.DataFrame:
    """Parse one coder's sheet; reject anything but a complete coding of the same rows."""
    sheet = pd.read_csv(path, keep_default_na=False, dtype={"candidate_id": str})
    if not {*SHEET_KEY, "political_family"} <= set(sheet.columns):
        raise ValueError(f"{path.name}: missing year, candidate_id or political_family.")
    expected = positions[SHEET_KEY].reset_index(drop=True)
    if not sheet[SHEET_KEY].reset_index(drop=True).equals(expected):
        raise ValueError(f"{path.name}: rows must be exactly the reference rows, in order.")
    families = sheet.political_family.str.strip()
    if not families.isin(LABELS).all():
        bad = sorted(set(families[~families.isin(LABELS)]))
        raise ValueError(f"{path.name}: every row needs one of {LABELS}; found {bad}.")
    return sheet.assign(political_family=families)


def weighted_kappa(a: list[int], b: list[int], categories: int) -> float | None:
    """Quadratic-weighted Cohen's kappa for two raters on an ordinal 1..k scale.

    ``kappa = 1 - sum(w * O) / sum(w * E)`` with ``w[i, j] = (i - j)^2 / (k - 1)^2``,
    ``O`` the observed joint proportions and ``E`` the product of the raters'
    marginal proportions. A disagreement of three steps costs nine times a
    disagreement of one step, which suits an ordinal scale.

    Worked example (k = 3): a = 1,1,2,2,3,3 and b = 1,2,2,2,3,1.
    sum(w * O) = (0.25 + 1) / 6 = 0.2083; sum(w * E) = 0.2917; kappa = 2/7.

    Returns None when chance disagreement is zero (both raters use one category):
    kappa is then undefined. Implemented here in a few lines of NumPy, so the
    project needs no statistics dependency for a single formula.
    """
    if len(a) != len(b) or not a:
        raise ValueError("Both raters must code the same, nonempty set of rows.")
    ratings = np.array([a, b])
    if ratings.min() < 1 or ratings.max() > categories:
        raise ValueError(f"Ratings must lie between 1 and {categories}.")
    observed = np.zeros((categories, categories))
    np.add.at(observed, (ratings[0] - 1, ratings[1] - 1), 1)
    observed /= observed.sum()
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    steps = np.subtract.outer(np.arange(categories), np.arange(categories))
    weights = steps**2 / (categories - 1) ** 2
    chance = float((weights * expected).sum())
    if chance == 0:
        return None
    return 1 - float((weights * observed).sum()) / chance


def coding_agreement(sheet_a: pd.DataFrame, sheet_b: pd.DataFrame) -> dict:
    """Agreement between two validated sheets covering the same rows."""
    frame = sheet_a[[*SHEET_KEY, "candidate_name"]].copy()
    frame["coder_a"] = sheet_a.political_family.to_numpy()
    frame["coder_b"] = sheet_b.political_family.to_numpy()
    score_a, score_b = frame.coder_a.map(FAMILY_SCORES), frame.coder_b.map(FAMILY_SCORES)
    both = score_a.notna() & score_b.notna()
    frame["steps_apart"] = (score_a - score_b).abs().where(both)
    confusion = (
        pd.crosstab(frame.coder_a, frame.coder_b)
        .reindex(index=LABELS, columns=LABELS, fill_value=0)
        .astype(int)
    )
    disagreements = frame[frame.coder_a != frame.coder_b]
    return {
        "rows": len(frame),
        "agreement_pct": float((frame.coder_a == frame.coder_b).mean() * 100),
        "rows_scored_by_both": int(both.sum()),
        "within_one_step_pct": (
            float((frame.steps_apart[both] <= 1).mean() * 100) if both.any() else None
        ),
        "quadratic_weighted_kappa": (
            weighted_kappa(
                score_a[both].astype(int).tolist(),
                score_b[both].astype(int).tolist(),
                categories=len(FAMILY_SCORES),
            )
            if both.any()
            else None
        ),
        "kappa_note": (
            "Computed on rows both coders placed on the 1-7 scale; rows either coder "
            "left Unclassified count in the percentage agreement and the matrix only."
        ),
        "confusion_matrix": {
            "rows": "coder A",
            "columns": "coder B",
            "labels": LABELS,
            "counts": confusion.to_numpy().tolist(),
        },
        "disagreements": [
            {
                "year": int(row.year),
                "candidate_id": row.candidate_id,
                "candidate_name": row.candidate_name,
                "coder_a": row.coder_a,
                "coder_b": row.coder_b,
                "steps_apart": None if pd.isna(row.steps_apart) else int(row.steps_apart),
            }
            for row in disagreements.itertuples()
        ],
    }


def reference_quality(positions: pd.DataFrame, agreement: dict | None = None) -> dict:
    """Quality rows for the candidate table: accuracy, consistency, completeness.

    Findings are reported, never repaired: a party coded differently in two
    elections can be a deliberate choice (Hamon's 2017 PS candidacy), and only
    the reviewers can say so.
    """
    affiliated = positions[positions.party_abbreviation != "IND"]
    parties = [
        {
            "party": party,
            "rows": [
                {"year": int(r.year), "candidate": r.candidate_name, "family": r.political_family}
                for r in rows.itertuples()
            ],
        }
        for party, rows in affiliated.groupby("party_abbreviation")
        if rows.political_family.nunique() > 1
    ]
    candidates = [
        {
            "candidate_id": candidate,
            "rows": [
                {"year": int(r.year), "family": r.political_family} for r in rows.itertuples()
            ],
        }
        for candidate, rows in positions.groupby("candidate_id")
        if rows.political_family.nunique() > 1
    ]
    missing = positions[positions.ideology_score.isna()]
    return {
        "rows": len(positions),
        "review_status": positions.review_status.value_counts().sort_index().to_dict(),
        "rows_with_alternative": int(positions.alternative_family.ne("").sum()),
        "accuracy": (
            {"status": "pending: two-coder review not done"}
            if agreement is None
            else {
                "status": "two-coder agreement measured",
                "agreement_pct": agreement["agreement_pct"],
                "quadratic_weighted_kappa": agreement["quadratic_weighted_kappa"],
                "disagreements": len(agreement["disagreements"]),
            }
        ),
        "consistency": {
            "rule": "the same party label carries the same family in every election",
            "parties_checked": int(affiliated.party_abbreviation.nunique()),
            "parties_coded_differently": parties,
            "candidates_coded_differently": candidates,
        },
        "completeness": {
            "rows_without_score": len(missing),
            "missing": [
                {"year": int(r.year), "candidate_id": r.candidate_id} for r in missing.itertuples()
            ],
            "treatment": "H1 and H2 use the H0b row for these candidates",
        },
    }
