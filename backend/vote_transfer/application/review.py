"""Quality checks on the hand-coded 1-7 candidate table, kept as a comparison scale.

The main candidate positions come from polling institutes (see ``positions.py``).
"""

from __future__ import annotations

import pandas as pd


def reference_quality(positions: pd.DataFrame) -> dict:
    """Quality rows for the hand-coded 1-7 table: accuracy, consistency, completeness.

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
        "accuracy": {"status": "not reviewed: kept only as a comparison for the poll-based scale"},
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
