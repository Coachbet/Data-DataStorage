# Offline election snapshots

These are real aggregate results derived from the original Ministry files, not
synthetic demo data. All five elections (2002, 2007, 2012, 2017, 2022) are included.
The application can read them directly after cloning and installing dependencies.
The 15 dataset files total about 336 KB; no Git LFS or external hosting is needed.

Each year contains only:

- `department_results.parquet`: aggregate observed outcomes for both rounds;
- `h0_evaluation.parquet`: H0 outputs and errors;
- `quality_report.json`: source URLs, dates, checksums, processing checks and limitations.

The exporter verifies output hashes and enforces a 2 MB limit per year. Source
licence metadata is retained literally in the quality reports. Raw files and
station-level data stay outside Git.

Regenerate from a successful local build with:

```bash
uv run vote-transfer bundle --all-years
```

This operation updates local files; it does not commit or push them. Review the
changed snapshots and reports before including them in a commit. The complete
rebuild instructions are in the root README.

2002 and 2007 have partial national coverage. Pre-2017 sources do not separate
blank and invalid ballots; the combined outcome is used consistently for all years.
