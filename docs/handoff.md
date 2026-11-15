# Handoff: analysis branch (`final/analysis`), 15 November 2026

Final report and code are due **27 November**; the presentation is on **2 December**.
Everything below is on the branch `final/analysis` (pull request #3). Nothing was
pushed to `master`.

The branch history was rewritten once on 15 November to clean the commit
messages, so every hash below differs from the ones in earlier versions of this
file. File contents, authors and dates did not change. Anyone who fetched the
branch before must reset to `origin/final/analysis`. Commit messages and the pull
request carry no tool attribution; the authors are the team members only.

## What was done

| Step | Result | Commits |
|---|---|---|
| Plan | `docs/plan_final.md` | `5f4cecb` |
| 1 Reproducibility | `make acquire/process/bundle` cover all years; `make data`, `make analysis`, `make archive`; `vote-transfer check-snapshots` in `make check` and a warning at app start-up | `862d209`, `4765d26` |
| 2 Storage | `areas`, `outcomes`, `options` per election; blank and invalid kept for 2017 and 2022; wide table derived on load; one long `predictions.parquet` | `5fcc422`, `44312b4` |
| 3 Review kit | Blind coding sheet, coder instructions, `review-kit` and `review-agreement` commands. **No coding was done or simulated.** | `d89b927` |
| 4 Models | H0a (unchanged), H0b, H1, H2-abst, H2-blank, H3 on each base with leave-one-election-out | `44312b4`, `d89b927` |
| 5 Analysis | `vote-transfer analyse`: tables, figures, `findings.md`, `numbers.json`, templated documents | `60294b8` |
| 6–7 App | "Compare models" and "2027 scenarios" pages | `18ddb37` |
| 8 Documents | Report draft, storage comparison, response to reviews, presentation outline, professor email | `5b94211` |
| 9 Handoff | First version of this file | `34b50c0` |
| Decisions | Scenario default H0b and all-models view | `6b7cc61` |
| Decisions | No processing timestamp; byte-identical rebuild | `5aa54bb` |
| Decisions | 3 November quality document restored; addendum moved to `docs/candidate_table_quality.md` | `2d29692` |
| Decisions | H2 threshold table, dated cross-check, methodology and prose | `1fa5854` |

Headline findings are in `reports/results/findings.md`. In one sentence: the
second baseline (H0b) matters more than any other change, H1 has the lowest mean
score only because of 2002, H2 fails for an arithmetic reason tied to its fixed
threshold, H3 adds little, and the order of models changes under the alternative
coding. The honest answer to the research question is currently "inconclusive".

## How to reproduce

```bash
uv sync --locked --dev
make check        # tests, lint, format, snapshot comparison
make analysis     # evaluate -> bundle -> analyse; works on a fresh clone, offline
make data         # full rebuild from the Ministry files (needs data.gouv.fr once, ~293 MB)
make app          # the Streamlit app
make archive      # zip of tracked files for submission
uv run vote-transfer crosscheck --year 2022   # optional, needs network; refreshes the dated record
```

Verified on 15 November 2026:

- Two full rebuilds from the local raw files give byte-identical processed and
  bundled files, quality reports included.
- A fresh clone of the branch passes `make check`, and `make analysis` there
  leaves `git status` clean.
- `vote-transfer crosscheck --year 2022` compared 26 fields with the Ministry's
  published national summaries: all match. The record is
  `data/bundled/crosscheck_2022.json`.

## Human tasks remaining

- [ ] **Assign an owner to every item below.** Owners were deliberately not assigned.
- [ ] **Code the candidate table.** Two members each copy
      `data/reference/review/coding_sheet_template.csv`, fill it alone following
      `data/reference/review/README.md`, and commit it before talking to each other.
- [ ] Run `uv run vote-transfer review-agreement --coder-a ... --coder-b ...` and
      keep `reports/results/coding_agreement.json`.
- [ ] Resolve each disagreement; update `data/reference/candidate_positions.csv`
      and set `review_status` to `reviewed`. Decide the two flagged consistency
      cases (PS, UDF) and the two Cheminade rows
      (see [`candidate_table_quality.md`](candidate_table_quality.md)).
- [ ] Run `make analysis` and `make check`, then commit the regenerated files.
- [ ] **Re-read the prose after that rerun.** Numbers update automatically; the
      sentences around them (in `docs/templates/`) were written for the draft
      results. The H2 explanation in particular assumes the finalists' codes of
      2017 and 2022 stay as they are.
- [ ] Remove every `[PENDING: coder agreement]` marker and write the measured
      agreement in its place.
- [ ] **Send the professor email** (`docs/email_professor_H3.md`), record the
      answer, and remove every `[PENDING: professor approval]` marker. If the
      answer is no: remove the three `H3(...)` names from `MODEL_ORDER` in
      `analysis.py` and `SCENARIO_MODELS` in `scenario.py`, rerun `make analysis`,
      and cut the H3 paragraphs.
- [ ] Cut the report to five pages **in the final format**. The Markdown draft is
      now about 2,450 words: the decided additions (H2 mechanism, scenario default,
      limitations) made it longer. Edit `docs/templates/report.md`, never
      `docs/report/report.md`.
- [ ] Build the slides from `docs/presentation_outline.md`.
- [ ] Check the repository link printed in the report PDF.
- [ ] Merge pull request #3.

## The thirteen open problems: decided

| # | Problem | Decision | Status |
|---|---|---|---|
| 1 | Peer-review PDFs not in the repository | They stay out of the public repository; cited by title | Nothing to change |
| 2 | Weights in the H3 fit | D5 confirmed | `docs/methodology.md` reworded: training-election weights may enter the fit; the evaluated election's never do. Temporary note removed |
| 3 | H3 before approval | Stays, pending approval | Marked `[PENDING: professor approval]` in the report where H3 is presented |
| 4 | Tie rule never applies | Kept | The report says so in one sentence (section 6, sensitivity) |
| 5 | Scenario default | H0b | Default changed, reason shown on the page, "Show all models side by side" added, tests updated |
| 6 | H2 fits badly | Kept as specified, no new variant | Mechanism generated in `reports/results/h2_threshold.csv` and explained in the findings and the report as a finding about thresholds on a coarse scale |
| 7 | Alternative coding | Kept as one scenario | One sentence added to the limitations |
| 8 | Blank-only convention | Confirmed | Described in `docs/methodology.md` |
| 9 | Candidates only, no map | Kept | Stated on the scenario page and in the report |
| 10 | Timestamp in quality reports | Removed | `processed_at_utc` dropped (schema version 4); bundles regenerated; a test compares two runs byte for byte |
| 11 | Cross-check | Rerun | Passed on 15 November 2026 (26 fields); the report cites the dated record |
| 12 | Working-method tools missing | Nothing to do | — |
| 13 | 3 November quality document | Restored | Identical to `master`; the addendum is [`candidate_table_quality.md`](candidate_table_quality.md) |

Two points for the team to know, neither blocking:

- The cross-check date in the report comes from `data/bundled/crosscheck_2022.json`.
  It changes only when someone reruns the command with network access.
- `README.md`, the report and the app each keep one sentence saying that AI
  assisted the work, as `master` already did in `docs/development.md` and the app.
  They are disclosures of how the project was made, not authorship; the team
  decides whether the course requires them.

## Final `make check` summary

```text
208 passed
ruff check: All checks passed!
ruff format --check: 51 files already formatted
vote-transfer check-snapshots: Processed and bundled snapshots are consistent.
```
