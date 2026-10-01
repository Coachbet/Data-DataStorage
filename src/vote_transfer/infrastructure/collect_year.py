"""Acquire the data of presidential election years, only through APIs.

For each year (for example 2017) the script calls the data.gouv.fr tabular API with a filter on
``id_election`` (rounds 1 and 2), the REU polling-station table, the Etalab departement list and
the departement contours, and writes one folder per year::

    data/raw/2017/
        turnout_by_polling_station_2017.parquet           # registered, voters, blank, null, valid
        candidate_votes_by_polling_station_2017.parquet   # votes per candidate and station
        polling_stations_reu_2017.parquet                 # REU table, stations found in the results
        departments_list.json                             # name, code, region (geo.api.gouv.fr)
        department_boundaries_2025.geojson                # simplified departement geometry
        manifest.json                                     # every call, rows, size, SHA-256

Usage (from the project root)::

    uv run python -m vote_transfer.infrastructure.collect_year --year 2017 --dry-run
    uv run python -m vote_transfer.infrastructure.collect_year --year 2017
    uv run python -m vote_transfer.infrastructure.collect_year --all-years
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import requests

USER_AGENT = "vote-transfer-student-project/0.1 (reproducible academic acquisition)"
CHUNK_SIZE = 1024 * 1024
PAGE_SIZE = 200
WORKERS = 6
PRESIDENTIAL_YEARS = (2002, 2007, 2012, 2017, 2022)

TABULAR_URL = "https://tabular-api.data.gouv.fr/api/resources/{resource_id}/data/"
# CSV resources of the data.gouv.fr datasets, indexed by the tabular API.
TURNOUT_RESOURCE = "b8703c69-a18f-46ab-9e7f-3a8368dcb891"  # donnees-des-elections-agregees
CANDIDATE_RESOURCE = "52a11762-45b4-414f-b6a2-eaa290217dc6"  # donnees-des-elections-agregees
POLLING_STATION_RESOURCE = "3a321a06-9e05-4de9-8dd3-421da6abd4c5"  # bureaux-de-vote-...
DEPARTMENTS_URL = "https://geo.api.gouv.fr/departements?fields=nom,code,codeRegion"
CONTOURS_URL = "https://www.data.gouv.fr/api/1/datasets/r/b06ff8a1-fd22-4925-bad1-e72989e1ba91"

DEPARTMENTS_FILE = "departments_list.json"
CONTOURS_FILE = "department_boundaries_2025.geojson"


def turnout_file(year: int) -> str:
    return f"turnout_by_polling_station_{year}.parquet"


def candidates_file(year: int) -> str:
    return f"candidate_votes_by_polling_station_{year}.parquet"


def stations_file(year: int) -> str:
    return f"polling_stations_reu_{year}.parquet"


def election_ids(year: int) -> list[str]:
    """Identifiers used by the consolidated files: presidential rounds 1 and 2."""

    return [f"{year}_pres_t1", f"{year}_pres_t2"]


class ApiClient:
    """HTTP client: one session per thread, retries, pause, and a record of every call made."""

    def __init__(self, pause: float = 0.05) -> None:
        self.pause = pause
        self.calls: list[str] = []
        self._local = threading.local()

    @property
    def session(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            session = requests.Session()
            session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
            self._local.session = session
        return self._local.session

    def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: tuple[int, int] = (10, 120),
        retries: int = 5,
        stream: bool = False,
    ) -> requests.Response:
        last_error: requests.RequestException | None = None
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=timeout, stream=stream)
                if response.status_code >= 500 or response.status_code == 429:
                    raise requests.ConnectionError(f"HTTP {response.status_code} for {url}")
                response.raise_for_status()
                self.calls.append(response.url)
                time.sleep(self.pause)
                return response
            except requests.HTTPError:
                raise  # other 4xx: retrying will not help
            except requests.RequestException as error:
                last_error = error
                if attempt + 1 < retries:
                    time.sleep(2**attempt)
        assert last_error is not None
        raise last_error

    def get_json(self, url: str, params: dict[str, Any] | None = None, **options: Any) -> Any:
        return self._get(url, params, **options).json()

    def download(self, url: str, target: Path) -> None:
        """Stream a file to ``target`` through a temporary ``.part`` file."""

        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        with (
            self._get(url, timeout=(30, 300), stream=True) as response,
            temporary.open("wb") as output,
        ):
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    output.write(chunk)
        temporary.replace(target)


def fetch_tabular(
    client: ApiClient,
    resource_id: str,
    election_id: str | None = None,
    page_size: int = PAGE_SIZE,
    workers: int = WORKERS,
    label: str = "",
) -> pd.DataFrame:
    """Read every row of a tabular-API resource, optionally filtered on ``id_election``.

    The first request gives ``meta.total`` and the real page size; the other pages are then
    requested in parallel with ``page=<n>``. The rows read must be exactly ``meta.total`` with
    no duplicate ``__id``, otherwise an error is raised.
    """

    url = TABULAR_URL.format(resource_id=resource_id)
    base: dict[str, Any] = {"page_size": page_size}
    if election_id:
        base["id_election__exact"] = election_id
    first = client.get_json(url, {**base, "page": 1})
    total = first["meta"]["total"]
    size = first["meta"]["page_size"]
    if total == 0:
        raise RuntimeError(f"{resource_id} {election_id}: the API returned no row")
    pages = max(1, -(-total // size))
    frames = {1: pd.DataFrame(first["data"])}

    def load(number: int) -> tuple[int, pd.DataFrame]:
        payload = client.get_json(url, {**base, "page": number})
        return number, pd.DataFrame(payload["data"])

    if pages > 1:
        pool = ThreadPoolExecutor(max_workers=workers)
        try:
            for done, (number, frame) in enumerate(pool.map(load, range(2, pages + 1)), start=2):
                frames[number] = frame
                if done % 50 == 0 or done == pages:
                    print(f"    {label or resource_id}: page {done}/{pages}", flush=True)
        except BaseException:
            pool.shutdown(wait=False, cancel_futures=True)
            raise
        pool.shutdown()
    table = pd.concat([frames[n] for n in sorted(frames)], ignore_index=True)
    if len(table) != total or table["__id"].duplicated().any():
        raise RuntimeError(f"{resource_id} {election_id}: read {len(table)} rows, API said {total}")
    return table.drop(columns="__id")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.convert_dtypes().to_parquet(temporary, index=False)
    temporary.replace(path)


def _polling_stations(client: ApiClient, root: Path, workers: int) -> pd.DataFrame:
    """The REU table has no year: read it once through the API, then cache it."""

    cached = root / "raw" / "_cache" / "polling_stations_reu.parquet"
    if cached.exists():
        return pd.read_parquet(cached)
    frame = fetch_tabular(client, POLLING_STATION_RESOURCE, workers=workers, label="REU stations")
    cached.parent.mkdir(parents=True, exist_ok=True)
    _write_parquet(frame, cached)
    return frame


def acquire_year(
    year: int,
    root: Path = Path("data"),
    client: ApiClient | None = None,
    workers: int = WORKERS,
    force: bool = False,
) -> dict[str, Any]:
    """Acquire the five datasets of one election year and write ``manifest.json``.

    A file that already exists is kept (resume after an interruption) unless ``force`` is set.
    """

    client = client or ApiClient()
    ids = election_ids(year)
    folder = root / "raw" / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []

    def record(name: str, method: str, calls: int, rows: int | None, **extra: Any) -> None:
        path = folder / name
        files.append(
            {
                "file": name,
                "method": method,
                "api_calls": calls,
                "rows": rows,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
                **extra,
            }
        )

    def kept(name: str) -> bool:
        """True (and recorded) when the file is already there from an earlier run."""

        path = folder / name
        if path.exists() and not force:
            rows = pq.ParquetFile(path).metadata.num_rows if name.endswith(".parquet") else None
            record(name, "kept from an earlier run", 0, rows)
            print(f"  {name}: already present, kept", flush=True)
            return True
        return False

    # 1 and 2. Turnout and candidate votes: tabular API, filter id_election, one series per round.
    tabular = (
        (turnout_file(year), TURNOUT_RESOURCE, "turnout"),
        (candidates_file(year), CANDIDATE_RESOURCE, "candidates"),
    )
    for name, resource, label in tabular:
        if kept(name):
            continue
        print(f"  {name}", flush=True)
        start = len(client.calls)
        frame = pd.concat(
            [
                fetch_tabular(client, resource, e, workers=workers, label=f"{label} {e}")
                for e in ids
            ],
            ignore_index=True,
        )
        _write_parquet(frame, folder / name)
        record(
            name,
            "tabular API, filter id_election__exact",
            len(client.calls) - start,
            len(frame),
            resource_id=resource,
            election_ids=ids,
        )

    # 3. Polling stations: REU table (tabular API, cached), kept for the stations in the results.
    name = stations_file(year)
    if not kept(name):
        print(f"  {name}", flush=True)
        start = len(client.calls)
        stations = _polling_stations(client, root, workers)
        results = pd.read_parquet(folder / turnout_file(year), columns=["id_brut_miom"])
        wanted = set(results["id_brut_miom"].dropna())
        found = stations[stations["id_brut_miom"].isin(wanted)]
        _write_parquet(found, folder / name)
        share = float(results["id_brut_miom"].isin(set(stations["id_brut_miom"].dropna())).mean())
        record(
            name,
            "tabular API (full table, cached), filtered on id_brut_miom of the results",
            len(client.calls) - start,
            len(found),
            resource_id=POLLING_STATION_RESOURCE,
            share_of_result_rows_found_in_reu=round(share, 4),
        )

    # 4 and 5. Departement list and contours: one version each, copied into every year folder.
    for name, url in ((DEPARTMENTS_FILE, DEPARTMENTS_URL), (CONTOURS_FILE, CONTOURS_URL)):
        if kept(name):
            continue
        print(f"  {name}", flush=True)
        start = len(client.calls)
        client.download(url, folder / name)
        record(name, "direct GET", len(client.calls) - start, None, url=url)

    manifest = {"year": year, "election_ids": ids, "files": files}
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def dry_run(years: list[int], client: ApiClient | None = None) -> None:
    """Print the rows announced by the API and the requests needed, writing nothing."""

    client = client or ApiClient()
    tables = ((TURNOUT_RESOURCE, "turnout"), (CANDIDATE_RESOURCE, "candidates"))
    for year in years:
        for resource, label in tables:
            for election in election_ids(year):
                params = {"page_size": PAGE_SIZE, "id_election__exact": election, "page": 1}
                try:
                    meta = client.get_json(
                        TABULAR_URL.format(resource_id=resource),
                        params,
                        timeout=(10, 60),
                        retries=1,
                    )["meta"]
                    requests_needed = -(-meta["total"] // meta["page_size"])
                    print(
                        f"{label:11s} {election}: {meta['total']:>8} rows, "
                        f"{requests_needed} requests of {meta['page_size']} rows"
                    )
                except requests.RequestException as error:
                    print(f"{label:11s} {election}: API unavailable ({error.__class__.__name__})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire presidential election years by API.")
    parser.add_argument("--year", type=int, nargs="+", help="one or more years, e.g. 2017 2022")
    parser.add_argument("--all-years", action="store_true", help=f"all of {PRESIDENTIAL_YEARS}")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--workers", type=int, default=WORKERS, help="parallel requests")
    parser.add_argument("--force", action="store_true", help="download again existing files")
    parser.add_argument("--dry-run", action="store_true", help="show row counts, write nothing")
    args = parser.parse_args()

    years = list(PRESIDENTIAL_YEARS) if args.all_years else (args.year or [])
    if not years:
        parser.error("give --year <year> [<year> ...] or --all-years")
    invalid = [y for y in years if y not in PRESIDENTIAL_YEARS]
    if invalid:
        parser.error(f"no presidential election in {invalid}; choose from {PRESIDENTIAL_YEARS}")
    if args.dry_run:
        dry_run(years)
        return
    client = ApiClient()
    for year in years:
        print(f"Year {year}", flush=True)
        manifest = acquire_year(year, args.data_root, client, args.workers, args.force)
        for item in manifest["files"]:
            print(f"  -> {item['file']}: {item['rows']} rows, {item['bytes']} bytes", flush=True)


if __name__ == "__main__":
    main()
