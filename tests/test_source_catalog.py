from vote_transfer.application.source_catalog import SOURCES, get_source
from vote_transfer.domain.data_source import AccessMethod


def test_source_keys_are_unique() -> None:
    keys = [source.key for source in SOURCES]
    assert len(keys) == len(set(keys))


def test_every_automatic_source_has_a_machine_access_path() -> None:
    for source in SOURCES:
        if source.access_method == AccessMethod.DATAGOUV_DATASET:
            assert source.dataset_slug
        if source.access_method in {AccessMethod.JSON_API, AccessMethod.PARAMETERIZED_API}:
            assert source.endpoint


def test_get_source_returns_documented_entry() -> None:
    assert get_source("elections").provider.startswith("data.gouv.fr")
