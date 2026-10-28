"""Domain definitions for transparent, reproducible data acquisition."""

from dataclasses import dataclass
from enum import StrEnum


class AccessMethod(StrEnum):
    """Supported ways of obtaining a source."""

    DATAGOUV_DATASET = "data.gouv.fr dataset API"
    JSON_API = "JSON API"
    INSEE_DOWNLOAD_PAGE = "INSEE download page"
    PARAMETERIZED_API = "parameterized API"
    REFERENCE_ONLY = "reference only"


@dataclass(frozen=True, slots=True)
class DataSource:
    """A documented external source required or considered by the project."""

    key: str
    name: str
    provider: str
    purpose: str
    landing_url: str
    access_method: AccessMethod
    raw_directory: str
    dataset_slug: str | None = None
    endpoint: str | None = None
    preferred_format: str | None = None
    title_contains: tuple[str, ...] = ()
    notes: str = ""
    core: bool = True
