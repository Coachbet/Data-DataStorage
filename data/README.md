# Data layout

- `raw/`: immutable files exactly as acquired;
- `external/`: reference tables maintained by third parties;
- `interim/`: validated and partially transformed data;
- `processed/`: analysis-ready outputs derived by the reproducible workflow;
- `samples/`: small, non-sensitive fixtures that may be committed for tests.

Large data files are ignored by Git. Each acquisition must document its source,
licence, retrieval date, checksum where useful, and exact reproduction command.

## Acquisition

The source catalogue lives in `src/vote_transfer/application/source_catalog.py`.
To review it before any network transfer:

```bash
uv run python -m vote_transfer.infrastructure.collect --list
uv run python -m vote_transfer.infrastructure.collect --source core
```

The first command explains every source. The second resolves current download
links without saving the data. Add `--download` only after checking the selected
resources and expected sizes. Downloads use a temporary `.part` file and are
renamed only after completion; `manifest.json` records provenance and integrity.
