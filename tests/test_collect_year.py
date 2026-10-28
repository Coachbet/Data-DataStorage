import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from vote_transfer.infrastructure import collect_year as cy


class FakeClient:
    """Stands in for ApiClient: serves tabular pages from memory, no network."""

    def __init__(self, page_cap: int = 2) -> None:
        self.calls: list[str] = []
        self.page_cap = page_cap
        turnout = [
            {"id_election": e, "id_brut_miom": f"01001_000{i}", "inscrits": 100 + i}
            for e in ("2017_pres_t1", "2017_pres_t2", "2022_pres_t1", "2022_pres_t2")
            for i in range(1, 4)
        ]
        candidates = [
            {"id_election": e, "id_brut_miom": "01001_0001", "nom": n, "voix": 5}
            for e in ("2017_pres_t1", "2017_pres_t2", "2022_pres_t1", "2022_pres_t2")
            for n in ("A", "B", "C")
        ]
        stations = [
            {"id_brut_miom": "01001_0001"},
            {"id_brut_miom": "01001_0002"},
            {"id_brut_miom": "99999_0001"},
        ]
        self.data = {
            cy.TURNOUT_RESOURCE: turnout,
            cy.CANDIDATE_RESOURCE: candidates,
            cy.POLLING_STATION_RESOURCE: stations,
        }

    def get_json(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> Any:
        params = dict(params or {})
        self.calls.append(f"{url}?{params}")
        resource = url.split("/resources/")[1].split("/")[0]
        rows = self.data[resource]
        if "id_election__exact" in params:
            rows = [r for r in rows if r["id_election"] == params["id_election__exact"]]
        size = min(int(params["page_size"]), self.page_cap)
        number = int(params.get("page", 1))
        start = (number - 1) * size
        ids = {id(r): i for i, r in enumerate(self.data[resource])}
        chunk = [{"__id": ids[id(r)], **r} for r in rows[start : start + size]]
        return {"data": chunk, "meta": {"page": number, "page_size": size, "total": len(rows)}}

    def download(self, url: str, target: Path) -> None:
        self.calls.append(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"url": url}), encoding="utf-8")


def test_fetch_tabular_reads_all_pages_and_checks_total() -> None:
    client = FakeClient(page_cap=2)
    frame = cy.fetch_tabular(client, cy.TURNOUT_RESOURCE, "2017_pres_t1", workers=3)
    assert len(frame) == 3
    assert set(frame["id_election"]) == {"2017_pres_t1"}
    assert "__id" not in frame.columns
    assert len(client.calls) == 2  # 3 rows, pages of 2


def test_fetch_tabular_rejects_incomplete_reads() -> None:
    class Broken(FakeClient):
        def get_json(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> Any:
            payload = super().get_json(url, params)
            payload["meta"]["total"] += 1
            return payload

    with pytest.raises(RuntimeError):
        cy.fetch_tabular(Broken(), cy.TURNOUT_RESOURCE, "2017_pres_t1")


def test_fetch_tabular_rejects_duplicate_rows() -> None:
    class Duplicating(FakeClient):
        def get_json(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> Any:
            payload = super().get_json(url, params)
            for row in payload["data"]:
                row["__id"] = 0
            return payload

    with pytest.raises(RuntimeError):
        cy.fetch_tabular(Duplicating(), cy.TURNOUT_RESOURCE, "2017_pres_t1")


def test_acquire_year_writes_one_folder_with_explicit_names(tmp_path: Path) -> None:
    client = FakeClient()
    manifest = cy.acquire_year(2017, tmp_path, client=client)  # type: ignore[arg-type]
    folder = tmp_path / "raw" / "2017"
    expected = {
        "turnout_by_polling_station_2017.parquet",
        "candidate_votes_by_polling_station_2017.parquet",
        "polling_stations_reu_2017.parquet",
        "departments_list.json",
        "department_boundaries_2025.geojson",
        "manifest.json",
    }
    assert {p.name for p in folder.iterdir()} == expected
    turnout = pd.read_parquet(folder / cy.turnout_file(2017))
    assert set(turnout["id_election"]) == {"2017_pres_t1", "2017_pres_t2"}
    assert len(turnout) == 6
    stations = pd.read_parquet(folder / cy.stations_file(2017))
    assert set(stations["id_brut_miom"]) == {"01001_0001", "01001_0002"}
    assert {item["file"] for item in manifest["files"]} == expected - {"manifest.json"}
    assert all(item["sha256"] for item in manifest["files"])


def test_second_run_keeps_existing_files_without_new_calls(tmp_path: Path) -> None:
    cy.acquire_year(2017, tmp_path, client=FakeClient())  # type: ignore[arg-type]
    again = FakeClient()
    manifest = cy.acquire_year(2017, tmp_path, client=again)  # type: ignore[arg-type]
    assert again.calls == []
    assert all(item["method"] == "kept from an earlier run" for item in manifest["files"])


def test_stations_table_is_read_once_for_several_years(tmp_path: Path) -> None:
    client = FakeClient()
    cy.acquire_year(2017, tmp_path, client=client)  # type: ignore[arg-type]
    cy.acquire_year(2022, tmp_path, client=client)  # type: ignore[arg-type]
    station_calls = [c for c in client.calls if cy.POLLING_STATION_RESOURCE in c]
    assert len(station_calls) == 2  # 3 stations, pages of 2, read a single time


def test_election_ids_and_years() -> None:
    assert cy.election_ids(2022) == ["2022_pres_t1", "2022_pres_t2"]
    assert cy.PRESIDENTIAL_YEARS == (2002, 2007, 2012, 2017, 2022)
