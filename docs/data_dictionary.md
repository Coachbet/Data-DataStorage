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

Each election has three normalised tables in `data/processed/<year>/`. Every fact
is stored once; a relational schema would declare the same keys.

**`areas.parquet`** — one row per `(year, round, area_code)`:

| Field | Type | Meaning |
|---|---|---|
| `year`, `round` | integer | Election and round (1 or 2) |
| `area_code` | string | Original Ministry reporting-unit code (`01`, `2A`, `ZZ`); not every unit is a département |
| `area_name` | string | Published label, or `Reporting area <code>` before 2017 |
| `registered` | integer | Registered voters: the denominator of every share in that area and round |
| `polling_stations` | integer | Number of source station rows aggregated |
| `blank`, `invalid` | nullable integer | Published separately in 2017 and 2022; null before 2017, never zero-filled |

**`outcomes.parquet`** — one row per `(year, round, area_code, option)`:

| Field | Type | Meaning |
|---|---|---|
| `option` | string | `candidate:<candidate_id>`, `blank_invalid` or `abstention` |
| `count` | integer | Votes, combined blank/invalid ballots, or abstaining voters |

**`options.parquet`** — one row per `(year, option)` with its display `label`.

Constraints checked on every write and every load (`processing.validate_tables`):
unique keys; every outcome has a label; `areas` and `outcomes` cover the same
areas and rounds; counts in an area sum exactly to `registered`; where published,
`blank + invalid` equals the `blank_invalid` count.

**Shares are not stored.** `share = count / registered` is computed when needed.
The primary outcome is the combined `blank_invalid` in every year; the separate
columns exist so 2017 and 2022 can be examined on blank ballots alone.

### Derived view

`processing.results_view(areas, outcomes, options)` returns the wide table the
app uses: one row per outcome with `label`, `department_name`, `registered`,
`polling_stations` and the computed `share`. It keeps the historical column name
`department_code` for `area_code`. It is a view built on load, not a file. In it
`registered` repeats on every outcome row, so sum it once per area and round, or
read it from `areas`.

### Predictions

`data/processed/predictions.parquet` is one long table for every model, variant
and election, with one row per `(year, area_code, model, variant, outcome)`:

| Field | Type | Meaning |
|---|---|---|
| `year`, `area_code` | integer, string | Election and reporting area |
| `model` | string | `H0a`, `H0b`, `H1`, `H2-abst`, `H2-blank`, `H3(H1)`, `H3(H2-abst)`, `H3(H2-blank)` |
| `variant` | string | `default` for H0a/H0b; otherwise `positions=<primary\|alternative>;tie=<split\|abstention>` |
| `train_elections` | string | Comma-separated training years for H3; empty for parameter-free models |
| `outcome` | string | One of the four second-round options |
| `predicted_share`, `actual_share` | float | Shares of round-two registered voters |
| `registered_r2` | integer | Round-two registered voters: the area's weight in the primary score |

For H3 the table holds **held-out predictions only**: the row's `year` never
appears in its `train_elections`. `evaluation_report.json` beside it records the
coding status of the candidate table, each election's finalists, the candidates
that fell back to the H0b row, every H3 fold (training years, fitted `p`, training
and held-out scores), the hash of the predictions file and the hashes of all its
inputs (the fifteen election tables, `candidate_positions.csv` and
`candidate_scores.csv`).
`vote-transfer evaluate --all-models --all-years` regenerates both files.

`quality_report.json` (per election) records checks, row counts, registration
changes, input hashes, build time, limitations and output checksums.
`derived_fields` states which counts are computed rather than published
(abstentions and blank/invalid before 2017). `diagnostics.stations_by_round`
measures completeness, key uniqueness, zero-registration/zero-voter stations and
station-level turnout outliers. `diagnostics.reporting_units` lists areas flagged
by within-election IQR fences on first-round abstention, registration change
between rounds and H0a error; flagged areas are retained.

`national_crosscheck.json` (local only, from `vote-transfer crosscheck`) compares
our station-level sums with the Ministry's published national summaries.
The same command writes a short dated record, `data/bundled/crosscheck_2022.json`
(versioned), which the report cites.

## Versioned aggregates

`data/bundled/<year>/` contains exact verified copies of the three processed
tables and their quality report; `data/bundled/predictions.parquet` and
`evaluation_report.json` are copies of the evaluation. `vote-transfer bundle
--all-years` copies only these allowlisted files, enforces a 2 MB ceiling per
election and for the predictions, and never copies polling-station records.

The app prefers a complete local processed election, falling back to its bundled
snapshot otherwise. Two copies can diverge if someone reprocesses and forgets to
bundle. `vote-transfer check-snapshots` (part of `make check`) fails when a
processed file and its bundled copy differ, or when the elections or the
candidate table changed after the last evaluation; the app shows the same warning
at start-up. A custom `VOTE_TRANSFER_DATA_DIR` uses only datasets under that root.

## Candidate references

Three versioned research inputs in `data/reference/`, separate from observed
results. Their key is `(year, candidate_id)`. Join to candidate outcomes by
removing the `candidate:` prefix from `option`; never join by row order or
display name. Each covers all 61 first-round candidacies. The
[reference README](../data/reference/README.md) documents them in full.

| File | Content | Key columns |
|---|---|---|
| `polling_axes.csv` | 22 collected polls, one row each | `year`, `institute`, `fieldwork`, `client`, `source_type`, `source_url`, `order_left_to_right` (candidate IDs separated by `;`) |
| `candidate_scores.csv` | The main, poll-based scale, written by `notebooks/candidate_scale.ipynb` | `score` (0–1, empty if unplaced), `lowest`, `highest`, `range`, `n_institutes`, `status` (`placed`/`unplaced`), `reason` |
| `candidate_positions.csv`, `sources.json` | The hand-coded 1–7 comparison scale and its sources | `political_family`, `ideology_score` (1–7, nullable), `alternative_family`, `review_status` |

These files ship with the code and are read from the repository, independently
of `VOTE_TRANSFER_DATA_DIR`, which selects election outputs only. They do not
affect H0a or H0b. The hashes of the two tables the models read are recorded in
`evaluation_report.json`, so editing either marks the predictions as stale.

**Why these tables stay CSV although the results are Parquet.** They are small
and edited by hand (the polls, the comparison codes) or regenerated by a notebook
(the scale), and reviewers must read, change and discuss them. A text file gives
line-by-line diffs in Git, so every change is attributable. The weakness of CSV,
untyped columns, is covered at the boundary: `positions.py` parses each file once
and enforces types, keys, allowed values, that placed candidates have a score in
[0, 1] and unplaced ones none, and that both tables list the same candidacies.
The scale keeps every decimal, because rounding would break exact ties.

## Evaluation summaries

`area_errors(evaluation)` recomputes each area's four-outcome absolute errors
from actual and predicted shares, counts registration once per area, and returns
`mean_error_pp`, `weight` and `weighted_error_pp` alongside year, area code and
registration. Weights sum to one within each selected election. The total of
weighted contributions is the primary score; the error after pooling the
outcome shares remains a separate diagnostic. `score_predictions(predictions)`
applies the same function to every model and variant in the long table.
