from vote_transfer.application.project_overview import get_project_overview


def test_project_overview_exposes_complete_workflow() -> None:
    overview = get_project_overview()

    assert len(overview["workflow"]) == 5
    assert overview["research"]["geographic_level"] == "French department"
    assert "ecological estimates" in overview["research"]["principal_limitation"]
