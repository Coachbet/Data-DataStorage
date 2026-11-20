"""Quality checks on the hand-coded 1-7 comparison table."""

from vote_transfer.application.positions import load_candidate_positions
from vote_transfer.application.review import reference_quality


def test_reference_quality_reports_consistency_and_completeness():
    quality = reference_quality(load_candidate_positions())
    assert quality["rows"] == 61
    assert sorted(
        item["party"] for item in quality["consistency"]["parties_coded_differently"]
    ) == [
        "PS",
        "UDF",
    ]
    ps = next(i for i in quality["consistency"]["parties_coded_differently"] if i["party"] == "PS")
    assert {row["family"] for row in ps["rows"]} == {"Centre-left", "Left"}
    assert quality["completeness"]["rows_without_score"] == 2
    assert {(r["year"], r["candidate_id"]) for r in quality["completeness"]["missing"]} == {
        (2012, "jacques-cheminade"),
        (2017, "jacques-cheminade"),
    }
    assert quality["review_status"] == {"draft": 59, "unresolved": 2}
    assert quality["rows_with_alternative"] == 41
    assert quality["accuracy"]["status"].startswith("not reviewed")
