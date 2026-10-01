# Data acquisition guide

## Principle

Collection is selective and auditable. The program first asks the producer for
the current resource URL, prints what it found, and downloads only when a human
adds `--download`. This prevents accidental multi-gigabyte transfers and avoids
hard-coding dated storage URLs.

## Source decisions

| Key | Source | Decision |
|---|---|---|
| `elections` | Consolidated data.gouv.fr election files | Core source; obtain both Parquet tables |
| `presidentielle_2022_reference` | Official 2022 second-round files | Validation reference; do not duplicate bulk data |
| `cog` | INSEE Code officiel géographique | Core source for historical geographic identifiers |
| `geo_api` | Etalab administrative API | Small snapshot for current labels and checks |
| `contours` | Etalab administrative contours | Simplified department geometry for maps |
| `reu` | INSEE electoral register | Download only the polling-station table, never the address table |
| `insee_local` | INSEE local indicators | Acquire once, then retain only justified variables |
| `filosofi` | INSEE income and poverty | Contextual source, with year and confidentiality caveats |
| `unemployment` | INSEE local unemployment | Match each election to information available at that date |
| `gdelt` | GDELT news search | Optional experiment requiring a fixed query protocol |

## Commands

```bash
# Complete catalogue and explanations
uv run python -m vote_transfer.infrastructure.collect --list

# Resolve one source without writing data
uv run python -m vote_transfer.infrastructure.collect --source elections

# Download one reviewed source
uv run python -m vote_transfer.infrastructure.collect --source elections --download

# Resolve all core sources without writing data
uv run python -m vote_transfer.infrastructure.collect --source core
```

## Result

Each source is stored below `data/raw/<source>/`. The generated `manifest.json`
records the landing page, resolved URL, retrieval timestamp, number of bytes and
SHA-256 digest. Raw data files stay outside Git and must never be edited in place.

## Acquisition by election year (APIs only)

`vote_transfer.infrastructure.collect_year` builds one folder per presidential election year
(`data/raw/2002/` ... `data/raw/2022/`). Every dataset comes from an API call; nothing is read from a
file downloaded beforehand.

```bash
uv run python -m vote_transfer.infrastructure.collect_year --year 2017 --dry-run   # rows announced, nothing written
uv run python -m vote_transfer.infrastructure.collect_year --year 2017             # writes data/raw/2017/
uv run python -m vote_transfer.infrastructure.collect_year --all-years             # 2002, 2007, 2012, 2017, 2022
```

Each year folder holds the same files:

| File | API call |
|---|---|
| `turnout_by_polling_station_<year>.parquet` | tabular API, resource `b8703c69-...`, `id_election__exact=<year>_pres_t1` and `_t2` |
| `candidate_votes_by_polling_station_<year>.parquet` | tabular API, resource `52a11762-...`, same filters |
| `polling_stations_reu_<year>.parquet` | tabular API, resource `3a321a06-...`, kept for the stations in the year's results |
| `departments_list.json` | `https://geo.api.gouv.fr/departements?fields=nom,code,codeRegion` |
| `department_boundaries_2025.geojson` | `https://www.data.gouv.fr/api/1/datasets/r/b06ff8a1-...` |
| `manifest.json` | every call, row count, size, SHA-256 |

- The first request of each table gives `meta.total` and the real page size; the other pages are requested
  in parallel (`--workers`, default 6). The rows read must equal `meta.total` with no duplicated `__id`.
- A file that already exists is kept, so an interrupted run resumes; `--force` downloads again.
- The REU table has no year: it is read once and cached in `data/raw/_cache/`.
- The département list and the contours are one version each, copied into every year folder.
