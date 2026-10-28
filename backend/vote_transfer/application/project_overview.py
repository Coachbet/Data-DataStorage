"""Application service supplying stable project metadata to user interfaces."""

from dataclasses import asdict

from vote_transfer.domain.models import PROJECT_QUESTION


def get_project_overview() -> dict[str, object]:
    """Return the agreed scope without coupling the domain to Streamlit."""

    return {
        "research": asdict(PROJECT_QUESTION),
        "workflow": (
            ("01", "Collect", "Acquire official election and geographic reference data."),
            ("02", "Clean", "Validate identifiers, turnout totals and cross-year schemas."),
            ("03", "Store", "Keep immutable raw files and query-ready harmonised tables."),
            ("04", "Analyse", "Estimate department-level flows with explicit assumptions."),
            ("05", "Communicate", "Show evidence, uncertainty and limitations together."),
        ),
        "sources": (
            "Original Ministry of the Interior presidential election files",
            "Consolidated election results for independent validation only",
            "CHES candidate positions; preference surveys for later extensions",
        ),
    }
