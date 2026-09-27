# Data layout

- `raw/`: immutable files exactly as acquired;
- `external/`: reference tables maintained by third parties;
- `interim/`: validated and partially transformed data;
- `processed/`: analysis-ready outputs derived by the reproducible workflow;
- `samples/`: small, non-sensitive fixtures that may be committed for tests.

Large data files are ignored by Git. Each acquisition must document its source,
licence, retrieval date, checksum where useful, and exact reproduction command.
