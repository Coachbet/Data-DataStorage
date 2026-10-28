# Validation record — 28 October 2026

## Automated checks

- 55 offline tests passed, including raw parsing, acquisition/resume, integrity,
  vote accounting, aggregation, H0, weighting and Streamlit interactions.
- Ruff lint and formatting checks passed; `git diff --check` passed.
- The local Streamlit server started and `/_stcore/health` returned HTTP 200.
- No controllable browser was available in the execution environment. Functional
  UI verification used Streamlit AppTest; browser visual QA remains outstanding.

## Real 2022 processing

The two original polling-station files produced:

| Measure | Value |
|---|---:|
| Polling-station/round records | 139,364 |
| Candidate/station/round records | 975,548 |
| Territorial reporting units | 107 |
| Registered voters, round 1 | 48,747,876 |
| Registered voters, round 2 | 48,752,339 |
| Units with changed registration between rounds | 106 |

All station-level vote-accounting and coverage checks passed. No missing rows,
identifiers or count discrepancies were silently repaired.

An independent aggregation check compared the processed totals against the
Ministry's published national summary files from the same releases:

- [Round 1 national summary](https://www.data.gouv.fr/api/1/datasets/r/1421c8db-b10f-4ed1-abb3-52b010e74e79):
  all six participation/ballot totals and all 12 candidate totals matched exactly.
- [Round 2 national summary](https://www.data.gouv.fr/api/1/datasets/r/debe2f26-48e5-4c45-abab-4926145c9936):
  all six participation/ballot totals and both candidate totals matched exactly.

Reference snapshots and hashes are in `data/raw/reference/national_2022/`.
The reference manifest is versionable; its source files remain outside Git.
This verifies aggregation against that publication version, not agreement with
all other releases or the separate consolidated dataset. Cross-source comparison
with the consolidated results remains a next step.

The primary input manifest is `data/raw/official/2022/manifest.json`; the detailed
processing report and output hashes are in `data/processed/2022/quality_report.json`.

## Limits

Original-file ingestion and H0 now cover 2002, 2007, 2012, 2017 and 2022. H0 is a
provisional baseline and has not been compared with H1–H5. There is no fitted
model, cross-election generalisation claim or completed 2027 simulation.


## Historical integration and offline handoff

All five original-source pipelines completed successfully. The source files and
station-level outputs remain local and ignored; small aggregate snapshots are
included under `data/bundled/` (325,886 bytes for the 15 data/report files).

| Year | Reporting units | Station/round records | Candidate records | Registered R1 | Registered R2 |
|---|---:|---:|---:|---:|---:|
| 2002 | 100 | 128,282 | 1,154,538 | 40,467,855 | 40,463,551 |
| 2007 | 101 | 131,234 | 918,638 | 43,319,652 | 43,320,654 |
| 2012 | 107 | 135,864 | 815,184 | 46,028,571 | 46,066,215 |
| 2017 | 107 | 138,484 | 900,146 | 47,582,183 | 47,568,693 |
| 2022 | 107 | 139,364 | 975,548 | 48,747,876 | 48,752,339 |

2002 and 2007 have partial national coverage. All source rows passed station-level
turnout/candidate-total checks and both-round unit coverage checks. Independent
published-total comparison has been performed for 2022 only; systematic historical
cross-source comparison is still the next step.

The shipped snapshots are checked for integrity and H0 can be reproduced directly
from their aggregate observations. A Streamlit test copies only `data/bundled/`
into an empty data root, blocks HTTP acquisition requests, and exercises the year
selector for all five elections. It needs neither raw nor locally processed data.
This verifies the intended professor/reviewer workflow after dependency installation.
