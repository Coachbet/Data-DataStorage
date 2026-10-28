"""Core concepts used throughout the vote-transfer project."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    """A precise question and the population to which it applies."""

    question: str
    unit_of_analysis: str
    geographic_level: str
    principal_limitation: str


PROJECT_QUESTION = ResearchQuestion(
    question=(
        "Which assumptions about voter behaviour best explain second-round results "
        "in French presidential elections (2002-2022)?"
    ),
    unit_of_analysis="One department in one election; shares over registered voters",
    geographic_level="French department",
    principal_limitation=(
        "Individual transfers are not observed; department-level flows are ecological estimates."
    ),
)
