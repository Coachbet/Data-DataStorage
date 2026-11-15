# Offline election snapshots

These are real aggregate results derived from the original Ministry files, not
synthetic demo data. All five elections (2002, 2007, 2012, 2017, 2022) are included.
The application can read them directly after cloning and installing dependencies.
The files are small enough for ordinary Git tracking; no Git LFS or external
hosting is needed.

Each year contains only:

- `areas.parquet`: one row per area and round (registered voters, stations, and the
  separate blank and invalid counts where published);
- `outcomes.parquet`: one count per area, round and option;
- `options.parquet`: display labels;
- `quality_report.json`: source URLs, dates, checksums, processing checks and limitations.

Beside the year folders:

- `predictions.parquet`: every model, variant and election in one long table;
- `evaluation_report.json`: coding status, finalists, H3 folds and input hashes.

Shares and the wide table used by the app are computed on load, not stored.

The exporter verifies output hashes and enforces a 2 MB limit per year. Source
licence metadata is retained literally in the quality reports. Raw files and
station-level data stay outside Git.

Regenerate from a successful local build with:

```bash
uv run vote-transfer evaluate --all-models --all-years
uv run vote-transfer bundle --all-years
```

`make check` fails if these snapshots differ from a local `data/processed/` build
or if the predictions are older than their inputs.

This operation updates local files; it does not commit or push them. Review the
changed snapshots and reports before including them in a commit. The complete
rebuild instructions are in the root README.

2002 and 2007 have partial national coverage. Pre-2017 sources do not separate
blank and invalid ballots; the combined outcome is used consistently for all years.
