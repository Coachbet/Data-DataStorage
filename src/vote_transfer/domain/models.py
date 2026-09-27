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
        "How do voters of candidates eliminated in the first round of a French "
        "presidential election transfer their vote in the second round?"
    ),
    unit_of_analysis="Aggregate first- and second-round election results",
    geographic_level="French department",
    principal_limitation=(
        "Individual transfers are not observed; department-level flows are ecological estimates."
    ),
)
