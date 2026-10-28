# Data contracts

## Raw inputs

Original files stay unchanged in `data/raw/official/<year>/`.
All verified adapters read Windows-1252, semicolon-separated text:

| Years | File layout | Processing |
|---|---|---|
| 2002, 2007 | `both_rounds.txt`: 13 fields per candidate row, embedded comment schema | Filter round; check repeated station totals agree; count each station once |
| 2012 | `both_rounds.txt`: 15 fields per candidate row, no header | Same method; two extra canton/constituency fields precede the station field |
| 2017, 2022 | `round_1.txt`, `round_2.txt`: 21 station/turnout fields, repeated seven-field candidate blocks | Parse all blocks, including those without header labels |

A changed schema fails explicitly. Producer column names remain in French in the
adapter as source identifiers. For 2002–2012, department names are not provided:
labels are `Reporting area <code>`, without an undocumented modern-geography join.

## Normalised interim tables

| Field | Type | Meaning |
|---|---|---|
| `year`, `round` | integer | Election and round (1 or 2) |
| `department_code` | string | Original Ministry reporting-unit code; preserve leading zeros, Corsica and overseas codes |
| `department_name` | string | Published reporting-unit label |
| `commune_code`, `station_code` | string | Original within-unit codes, not globally unique alone |
| `registered`, `abstentions`, `voters` | integer | Registered electorate and participation counts |
| `valid`, `blank_invalid` | integer | Valid votes and combined blank/invalid ballots |
| `blank`, `invalid` | nullable integer | Separate categories when published; null before 2017 |
| `candidate_id` | string | Normalised full-name slug, scoped by election year |
| `candidate` | string | Published candidate display name |
| `source_panel_number` | string | Original round-specific panel number; never used to join rounds |
| `votes` | integer | Candidate votes in a station and round |

Station key: `(year, round, department_code, commune_code, station_code)`.
Candidate key adds `candidate_id`. Full-name slug collisions with inconsistent
labels are rejected. A future multi-year adapter needs explicit identity/mapping
review; there is no implied party or bloc classification.

## Processed tables

`data/processed/<year>/department_results.parquet` has one row per
`(year, round, department_code, option)`:

- `option`: `candidate:<candidate_id>`, `blank_invalid` or `abstention`;
- `label`: display name;
- `count`: votes or abstaining people;
- `registered`: the unit/round denominator, repeated on each outcome row;
- `polling_stations`: number of source station rows in the unit/round;
- `share`: `count / registered`, a fraction in `[0, 1]`.

Do not sum repeated `registered` across options. Sum once per unit and round.
`department_name` accompanies each row. Original reporting units are preserved;
not every unit is administratively a department.

`h0_evaluation.parquet` has one row per unit and second-round outcome:
`year`, `department_code`, `department_name`, `option`, `label`, `registered`
(round two), `actual_share`, `predicted_share`, and `absolute_error_pp`.

`quality_report.json` records checks, row counts, registration changes, input
hashes, build time, limitations and output checksums. The app reads these three
processed files. It never reprocesses raw results during a page rerun.


## Versioned aggregates

`data/bundled/<year>/` contains exact verified copies of the two processed Parquet
tables and their quality report. The report preserves input provenance and output
hashes. `vote-transfer bundle` enforces a 2 MB per-year ceiling and copies only
these three allowlisted files. It never copies polling-station records.

The app prefers a complete local processed year, falling back to its bundled
snapshot otherwise. A custom `VOTE_TRANSFER_DATA_DIR` uses only datasets under
that root, with no hidden fallback to another project directory.
