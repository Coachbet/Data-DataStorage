# Local data storage

- `raw/official/<year>/`: unchanged Ministry files and provenance manifests.
- `raw/reference/`: consolidated results for independent validation.
- `raw/2017/`: preserved partial legacy API collection; not a primary source.
- `interim/<year>/`: validated station-level Parquet tables.
- `processed/<year>/`: results, H0 evaluation and quality report read by Streamlit.
- `bundled/<year>/`: small, verified, versioned aggregates for offline review.
- `reference/`: versioned manual candidate/party mapping, scores, coding notes and sources.
- `external/`: unversioned downloads for future external positional references.
- `archive/legacy/`: previous local datasets, preserved but excluded from Git.

The app works immediately with the bundled snapshots. To rebuild all originals, run
`uv run vote-transfer acquire --all-years`, then `uv run vote-transfer process --all-years`.
Refresh the versioned snapshots explicitly with `uv run vote-transfer bundle --all-years`. The root README has the full setup.
Generated data and archives are ignored. Only small raw provenance manifests, curated bundled aggregates,
documented manual inputs in `reference/` and
README/placeholder files are versioned. Never edit raw source bytes in place.
