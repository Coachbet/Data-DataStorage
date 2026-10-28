# Validation record — 28 October 2026

## Automated checks

- 35 offline tests passed, including raw parsing, acquisition/resume, integrity,
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

Only 2022 is implemented in the new original-file pipeline. H0 is a provisional
baseline and has not been compared with H1–H5. There is no fitted model,
cross-election performance claim or completed 2027 simulation.
