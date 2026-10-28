# Data contracts

## Raw inputs

`data/raw/official/2022/round_1.txt` and `round_2.txt` are unchanged Ministry
exports. The verified adapter reads Windows-1252 text separated by semicolons.
There are 21 station/turnout fields, then repeated seven-field candidate blocks.
The header only describes the first block. A changed schema fails explicitly.
Producer column names remain in French in the adapter, as source identifiers.

## Normalised interim tables

| Field | Type | Meaning |
|---|---|---|
| `year`, `round` | integer | Election and round (1 or 2) |
| `department_code` | string | Original Ministry reporting-unit code; preserve leading zeros, Corsica and overseas codes |
| `department_name` | string | Published reporting-unit label |
| `commune_code`, `station_code` | string | Original within-unit codes, not globally unique alone |
| `registered`, `abstentions`, `voters` | integer | Registered electorate and participation counts |
| `blank`, `invalid`, `valid` | integer | Ballot categories |
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
