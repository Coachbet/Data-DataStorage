# Data acquisition and provenance

## Primary path: original Ministry files

```bash
uv run vote-transfer acquire --all-years
uv run vote-transfer process --all-years
uv run vote-transfer bundle --all-years
```

The downloader resolves the verified polling-station text resource in each
[data.gouv.fr Ministry dataset](https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour).
The second-round dataset is
[here](https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-2nd-tour).
Every election and round is pinned to a reviewed resource ID; a replaced or
ambiguous resource fails rather than being substituted.

Downloads stream into `.part` files. Published byte sizes and basic headers are
checked before renaming. The manifest is checkpointed after each round and stores
resource ID, source API, published/resolved URLs, licence metadata, retrieval
UTC timestamp, file size and SHA-256. Existing files are reused only when their
hash matches the manifest; their original retrieval dates are retained. The
manifests are versioned, so a fresh clone must reproduce the pinned SHA-256: a
download with different bytes stops with an error and is left as a `.part` file for
inspection. On 31 October 2026 a clean re-download of all five elections reproduced
every pinned checksum.
Unverified or modified files cause an error and are never overwritten implicitly.

For 2022, the source API currently returns `notspecified` for licence metadata on these
2022 datasets. The manifest records that value literally; it does not assert a
licence that the metadata has not supplied. Check reuse terms before redistribution.

Processing rechecks hashes, parses original fields, validates all station totals,
and writes normalised interim tables plus app-ready processed tables. Raw bytes
are never modified. Generated raw/interim/processed datasets stay outside Git. Small reviewed aggregate
snapshots in `data/bundled/` are versioned for offline review. Reproduction commands
are in the root README; exact dates/checksums are in the raw manifest.

## Consolidated data: validation only

The old collect/collect_year modules remain available for reference collection:

```bash
uv run python -m vote_transfer.infrastructure.collect --list
uv run python -m vote_transfer.infrastructure.collect --source elections
uv run python -m vote_transfer.infrastructure.collect --source elections --download
uv run python -m vote_transfer.infrastructure.collect_year --year 2017 --dry-run
```

The generic collector is retained for reference datasets. Original primary sources
must use `vote-transfer acquire` to get the correct files and manifest contract.
The old partial `data/raw/2017/` download is consolidated API data, not a primary
original-file dataset. It is not consumed by the new pipeline.
Older acquired data were preserved in `data/archive/legacy/`, excluded from Git.

## Upcoming sources

- CHES: no longer the primary candidate-position source (see `project_scope.md`,
  "Change from the acquisition note"); possible later sensitivity reference only.
- Polling-company axes / Wikipedia 2027 tables: dated snapshots and a fixed scraping protocol.
- Political Compass 2022 / CEVIPOF: documented manual extraction for robustness checks.
- Voter Autrement 2017: verify the precise Zenodo record before acquisition.

Socioeconomic datasets and media mention counts are no longer active sources.


## Verified historical originals

| Year | Original Ministry dataset | Resource selection |
|---|---|---|
| 2002 | [Both rounds](https://www.data.gouv.fr/datasets/election-presidentielle-2002-resultats-par-bureaux-de-vote) | `17fbaf03-33f2-48d6-95e8-aaa13809e432` |
| 2007 | [Both rounds](https://www.data.gouv.fr/datasets/election-presidentielle-2007-resultats-par-bureaux-de-vote) | `83e6c566-e313-4dbb-a504-8467c0952697` |
| 2012 | [Both rounds](https://www.data.gouv.fr/datasets/election-presidentielle-2012-resultats-par-bureaux-de-vote-1) | `206b1668-2b31-46da-b957-9857f94fe85c` |
| 2017 | [Round 1](https://www.data.gouv.fr/datasets/election-presidentielle-des-23-avril-et-7-mai-2017-resultats-definitifs-du-1er-tour-par-bureaux-de-vote) / [round 2](https://www.data.gouv.fr/datasets/election-presidentielle-des-23-avril-et-7-mai-2017-resultats-definitifs-du-2nd-tour-par-bureaux-de-vote) | `8fdb0926-ea9d-4fb4-a136-7767cd97e30b` / `2e3e44de-e584-4aa2-8148-670daf5617e1` |

These datasets report the Ministry as producer and `fr-lo` as licence metadata.
Resource IDs select the reviewed originals while their current URLs are resolved
through the dataset API. Unknown replacement resources fail rather than being
silently substituted. Both rounds share one physical input in 2002–2012; the
manifest associates that same file/hash with each round, without two downloads.

The 2002/2007 embedded comments document their 13-field schema. The 2012 format
has two additional codes before the station identifier; those unused contextual
fields are not used to infer geography. Counts are independently validated against
candidate sums. In these files abstentions (`registered − voters`) and blank/invalid
(`voters − valid`) are derived, so turnout accounting holds by construction; the
informative checks are `voters ≤ registered`, `valid ≤ voters`, agreement of the
station totals repeated on every candidate row, and candidate sums. Historical
cross-source comparison remains
an explicit next step.
