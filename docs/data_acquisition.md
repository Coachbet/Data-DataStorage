# Data acquisition and provenance

## Primary path: original Ministry files

```bash
uv run vote-transfer acquire --year 2022
uv run vote-transfer process --year 2022
```

The downloader resolves the unique polling-station text resource in each
[data.gouv.fr Ministry dataset](https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour).
The second-round dataset is
[here](https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-2nd-tour).
Resource title and format must match explicitly; ambiguous results fail.

Downloads stream into `.part` files. Published byte sizes and basic headers are
checked before renaming. The manifest is checkpointed after each round and stores
resource ID, source API, published/resolved URLs, licence metadata, retrieval
UTC timestamp, file size and SHA-256. Existing files are reused only when their
hash matches the manifest; their original retrieval dates are retained.
Unverified or modified files cause an error and are never overwritten implicitly.

The source API currently returns `notspecified` for licence metadata on these
2022 datasets. The manifest records that value literally; it does not assert a
licence that the metadata has not supplied. Check reuse terms before redistribution.

Processing rechecks hashes, parses original fields, validates all station totals,
and writes normalised interim tables plus app-ready processed tables. Raw bytes
are never modified. Generated datasets stay outside Git. Reproduction commands
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

- Original 2017 polling-station results, then original 2002/2007/2012 files:
  select exact releases and implement separate format adapters.
- CHES: choose a survey wave and document candidate-to-party mapping and missing parties.
- Polling-company axes / Wikipedia 2027 tables: dated snapshots and a fixed scraping protocol.
- Political Compass 2022 / CEVIPOF: documented manual extraction for robustness checks.
- Voter Autrement 2017: verify the precise Zenodo record before acquisition.

Socioeconomic datasets and media mention counts are no longer active sources.
