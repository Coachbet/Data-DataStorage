# Local data storage

- `raw/official/<year>/`: unchanged Ministry files and provenance manifests.
- `raw/reference/`: consolidated results for independent validation.
- `raw/2017/`: preserved partial legacy API collection; not a primary source.
- `interim/<year>/`: validated station-level Parquet tables.
- `processed/<year>/`: results, H0 evaluation and quality report read by Streamlit.
- `external/`: future documented candidate/party mappings and positional references.
- `archive/legacy/`: previous local datasets, preserved but excluded from Git.

Build the first dataset with `uv run vote-transfer acquire --year 2022` followed
by `uv run vote-transfer process --year 2022`. The root README has the full setup.
Generated data and archives are ignored. Only small raw provenance manifests and
README/placeholder files are versioned. Never edit raw source bytes in place.
