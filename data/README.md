# Local data storage

- `raw/official/<year>/`: unchanged Ministry files and provenance manifests.
- `raw/reference/`: consolidated results for independent validation.
- `interim/<year>/`: validated station-level Parquet tables.
- `processed/<year>/`: normalised `areas`, `outcomes` and `options` tables and the quality report;
  `processed/predictions.parquet` holds every model's predictions.
- `bundled/<year>/`: small, verified, versioned aggregates for offline review.
- `reference/`: versioned manual candidate/party mapping, scores, coding notes and sources.
- `external/`: unversioned downloads for future external positional references.

The app works immediately with the bundled snapshots. To rebuild all originals, run
`make data` (acquire, process, evaluate and bundle for all five elections). The root README has the full setup.
Generated data and archives are ignored. Only small raw provenance manifests, curated bundled aggregates,
documented manual inputs in `reference/` and
README/placeholder files are versioned. Never edit raw source bytes in place.
