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
