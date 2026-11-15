<!-- Generated from docs/templates/storage_comparison.md by `vote-transfer analyse`. Edit the template, not this file. -->

# Storage: Parquet files compared with a relational database and with DuckDB

Draft for the team to edit. Sizes and row counts are measured by
`vote-transfer analyse` (`storage.*` in `reports/results/numbers.json`).

## What has to be stored, and what is done with it

| Layer | Content | Size | Written | Read |
|---|---|---|---|---|
| Raw | Ministry polling-station text files, pinned by hash | 293 MB | Once, by download | Once per rebuild |
| Interim | 673,228 station-round rows and 4,764,054 candidate rows | Local only | Once per rebuild | By the cross-check |
| Processed | `areas` (1,044 rows), `outcomes` (9,475), `options` (71) for five elections | 139 kB in 15 files | Once per rebuild | Every app page; every model |
| Predictions | 54,288 rows: every model, variant, election, area and outcome | 304 kB | Once per evaluation | Analysis, app |
| Reference | 61 hand-coded candidacies | CSV | By hand | By every scored model |

The operations are few and regular:

1. **Write once, by one process.** A rebuild replaces whole tables. No row is
   inserted, updated or deleted on its own, and nothing writes concurrently.
2. **Read whole columns.** Models read every area of an election; scoring reads
   two share columns and a weight.
3. **Join across elections and models.** Predictions are compared across models
   and elections; outcomes are joined to their area's denominator.
4. **Be reproduced by a reader.** A classmate must clone, install and get the same
   numbers, offline, without administering anything.
5. **Keep types and keys honest.** Area codes such as `01`, `2A` and `ZZ` are text;
   counts are integers; "not published" is null, not zero; keys are unique.

## The three candidates against those operations

| Operation | Parquet files (chosen) | SQLite / PostgreSQL | DuckDB over the same Parquet files |
|---|---|---|---|
| Write once | Natural: one file per table, replaced atomically after validation | Works, but transactions, locking and (PostgreSQL) a server solve a concurrent-write problem we do not have | Not a storage change: DuckDB reads the files we already write |
| Column reads | Columnar: reads only the columns asked for | Row-oriented; fine at this size, no advantage | Columnar, vectorised |
| Joins across models and elections | Done in pandas after loading (`merge`, `groupby`); every table fits in memory many times over | SQL joins, declared once as views; the strongest argument for a database | SQL joins directly on the Parquet files, with no import step |
| Size | 443 kB for all processed tables and predictions; the same tables as CSV take 7098 kB (16 times more) | Not measured. SQLite: one file with row storage and no column compression; PostgreSQL: a data directory outside the repository | Same files, same size |
| Reproducibility for a reader | `uv sync`, then read files. Snapshots are small enough to version in Git, and each file's SHA-256 is recorded and checked on load | SQLite: one binary file, awkward to diff and to version; byte-identical rebuilds are not guaranteed. PostgreSQL: install, create a role and a database, load a dump | One extra Python package; nothing else changes |
| Schema enforcement | Types are stored in the file. Keys and identities are **not** declared: they are enforced by `validate_tables` on every write and every load | **Declarative** primary keys, foreign keys and `CHECK` constraints; violations are refused by the engine | None of its own on external Parquet files |
| Text codes, integers, nulls | Preserved (string, int64, nullable Int64) | Preserved with `TEXT`/`INTEGER`; SQLite's loose typing needs `STRICT` tables to refuse a wrong type | Preserved (it reads Parquet types) |

### Parquet compared with a relational database, in detail

A relational database would give us one thing we lack: **constraints stated in
the schema**. We checked this is real and not rhetorical. The test
`tests/test_storage.py::test_same_tables_load_into_sqlite_with_declared_constraints`
loads the 2022 `areas`, `outcomes` and `options` tables into SQLite with primary
keys, foreign keys and `CHECK` constraints. The engine accepts our data, refuses
an outcome that points to a missing area, keeps `01` as text, and a SQL join
returns the same shares as our derived view. The relational model fits the data:
after the refactor suggested by the second peer review, our tables *are* a
normalised relational design (area, outcome and option tables, with the wide
table as a view).

What it would cost us:

- **Reproducibility.** Our strongest property, confirmed by the reviewers, is
  that a rebuild gives byte-identical files whose hashes are recorded. A reader
  can verify a snapshot with one hash. A SQLite file embeds page layout and
  free-list state, so equal content does not guarantee equal bytes; PostgreSQL
  has no file to hash at all. We would have to hash query results instead.
- **Versioning.** Fifteen small Parquet files and one predictions file sit in
  Git. A database file would be replaced wholesale at every rebuild.
- **Installation.** PostgreSQL adds a server, credentials and a loading step for
  every reader, with no benefit at 9,475 outcome rows.
- **A second representation.** Models run in NumPy and pandas. With a database we
  would load from SQL into the same frames, so the database would sit between two
  steps that already work.

The one integrity rule a simple schema cannot declare anyway is the central one:
**outcome counts in an area sum to its registered voters**. In SQL it needs a
trigger or a deferred assertion; in our code it is one line of `validate_tables`.
So even with a database, part of the integrity checking would stay in code.

### Parquet compared with DuckDB over Parquet

DuckDB is not an alternative store; it is a query engine over the files we keep.
It would let us write the model comparison as SQL (`GROUP BY model, year` over
`predictions.parquet` joined to `areas.parquet`) with no import step and no
server. It was in the project's early dependencies and was removed because no
implemented feature used it. The comparison we need is a handful of `groupby`
and `merge` calls on 54,288 rows, which pandas runs in well
under a second. DuckDB becomes the right addition, with no change to storage, if
the predictions table grows by orders of magnitude (station-level predictions,
many more variants) or if readers want to explore it in SQL.

## Decision and limits

**We keep Parquet files as the storage layer, with normalised tables, a derived
view and executable constraints. We keep the hand-edited reference table as CSV.**

Why: the data is written once by one process, read by column, small, and must be
reproduced exactly by a reader with no setup. Parquet keeps the types that CSV
loses, is 16 times smaller than CSV for our tables,
and yields files that can be hashed and versioned.

Limits we accept and state:

1. **Constraints are executable, not declarative.** A file written by other code
   could violate them; they are caught on load, not prevented on write. A reader
   who opens a Parquet file directly, without our loader, gets no check.
2. **Joins live in Python.** There is no ad hoc SQL for a reader. DuckDB would add
   it without changing the files.
3. **Two copies exist** (`processed/` and `bundled/`). They can diverge; we detect
   it (`vote-transfer check-snapshots`, run by `make check` and at app start-up)
   and do not prevent it.
4. **One table is still CSV.** `candidate_positions.csv` is edited by hand and
   reviewed line by line in Git; its types are enforced when it is read
   (`positions.py`). This is a deliberate exception, not an inconsistency.
5. **This choice does not scale to concurrent writers.** If the project became a
   service with several people writing results, a database would be the right
   answer.
