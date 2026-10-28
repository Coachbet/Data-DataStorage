"""Active sources from the 2 October 2026 acquisition note.

French resource-title filters are producer identifiers and must not be translated.
"""

from vote_transfer.domain.data_source import AccessMethod, DataSource
from vote_transfer.infrastructure.official import DATASETS

SOURCES: tuple[DataSource, ...] = (
    *(
        DataSource(
            key=f"official_{year}_r{round_number}",
            name=f"Original presidential results: {year}, round {round_number}",
            provider="French Ministry of the Interior",
            purpose="Primary evidence: polling-station results to harmonise ourselves.",
            landing_url=f"https://www.data.gouv.fr/datasets/{slug}",
            access_method=AccessMethod.DATAGOUV_DATASET,
            dataset_slug=slug,
            raw_directory=f"official/{year}",
            preferred_format="txt",
            title_contains=(f"burvot-t{round_number}-france-entiere",),
            notes="Use vote-transfer acquire for the validated, resumable original-file workflow.",
        )
        for (year, round_number), slug in DATASETS.items()
    ),
    DataSource(
        key="elections",
        name="Consolidated election results (validation only)",
        provider="data.gouv.fr / Ministry of the Interior",
        purpose="Independent comparison against our cleaning of the original files.",
        landing_url="https://www.data.gouv.fr/datasets/donnees-des-elections-agregees",
        access_method=AccessMethod.DATAGOUV_DATASET,
        dataset_slug="donnees-des-elections-agregees",
        raw_directory="reference/elections",
        preferred_format="parquet",
        title_contains=("Résultats généraux", "Résultats par candidat"),
        notes="Never substitute this harmonised dataset for the primary source.",
        core=False,
    ),
    DataSource(
        key="ches",
        name="Chapel Hill Expert Survey",
        provider="CHES",
        purpose="Party order, ideological distances and political-family labels for H1/H2/H5.",
        landing_url="https://www.chesdata.eu/",
        access_method=AccessMethod.REFERENCE_ONLY,
        raw_directory="positions/ches",
        notes=(
            "Pending: select a survey wave, record its release and licence, "
            "and document candidate-to-party mappings. No positions have been inferred."
        ),
        core=False,
    ),
    DataSource(
        key="preferences",
        name="Voter Autrement 2017",
        provider="Zenodo / study authors",
        purpose="Approval preferences versus official votes for the H4/H5 extensions.",
        landing_url="https://zenodo.org/",
        access_method=AccessMethod.REFERENCE_ONLY,
        raw_directory="preferences",
        notes=(
            "Discovery entry only: the exact study record and reuse conditions still need "
            "verification."
        ),
        core=False,
    ),
)


def get_source(key: str) -> DataSource:
    """Return one source by its stable key."""
    for source in SOURCES:
        if source.key == key:
            return source
    raise KeyError(f"Unknown source: {key}. Choose from: {', '.join(s.key for s in SOURCES)}")
