# Handoff: what is done and what people must still do

Final report and code are due **27 November 2026**; the presentation is on
**2 December 2026**.

This file lists the state of the work and the open human tasks. It deliberately
holds no commit hashes, branch names or test counts: those go stale. Use `git log`
for history and run `make check` for the current verification result.

## What exists

| Area | Result |
|---|---|
| Reproducibility | `make acquire/process/bundle` cover all years; `make data`, `make analysis`, `make archive`; `vote-transfer check-snapshots` runs in `make check` and as a warning at app start-up |
| Storage | `areas`, `outcomes`, `options` per election; blank and invalid kept for 2017 and 2022; the wide table is derived on load; one long `predictions.parquet` |
| Review kit | Blind coding sheet, coder instructions, `review-kit` and `review-agreement` commands. **No coding was done or simulated.** |
| Models | H0a, H0b, H1, H2-abst, H2-blank, and H3 on each base with leave-one-election-out |
| Analysis | `vote-transfer analyse`: tables, figures, `findings.md`, `numbers.json`, templated documents |
| App | Five pages: answer, evidence, explore, scenarios, method |
| Documents | Report draft, storage comparison, response to reviews, presentation outline, professor email |
| Plan | The completed implementation plan is kept in [`archive/plan_final.md`](archive/plan_final.md) |

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

Where `make` is not installed (default on Windows), run the `uv run ...` commands
listed in the README instead.

Reproducibility holds in two senses. **Content**: any platform reproduces the same
tables, scores and documents. **Bytes**: a rebuild gives byte-identical files only on
the same platform, because the last floating-point digit of a prediction can differ
between machines. Tests therefore compare predictions and fitted parameters with a
tolerance, and versioned text files are stored with LF line endings (`.gitattributes`)
so that their hashes do not depend on a clone's `core.autocrlf`.

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
      well over that length. Edit `docs/templates/report.md`, never
      `docs/report/report.md`.
- [ ] Build the slides from `docs/presentation_outline.md`.
- [ ] Check the repository link printed in the report PDF.

## Decisions taken

| # | Topic | Decision |
|---|---|---|
| 1 | Peer-review PDFs | Stay out of the public repository; cited by title |
| 2 | Weights in the H3 fit | Training-election weights may enter the fit; the evaluated election's never do (`docs/methodology.md`) |
| 3 | H3 before approval | Stays, marked `[PENDING: professor approval]` |
| 4 | Tie rule never applies | Kept; the report says so in one sentence |
| 5 | Scenario default | H0b, with all models available side by side |
| 6 | H2 fits badly | Kept as specified, no new variant; explained as a finding about thresholds on a coarse scale |
| 7 | Alternative coding | Kept as one scenario, stated in the limitations |
| 8 | Blank-only convention | Described in `docs/methodology.md` |
| 9 | Candidates only, no map | Kept; stated on the scenario page and in the report |
| 10 | Timestamp in quality reports | Removed so a rebuild from the same raw bytes is identical on one platform |
| 11 | Cross-check | 2022 sums match the Ministry's national summaries; the dated record is `data/bundled/crosscheck_2022.json` |
| 12 | 3 November quality document | Kept as delivered; the addendum is `candidate_table_quality.md` |
| 13 | H0b status | Added after the second peer review, in response to H0a's abstention error. Documents say it is not a pre-specified model |
| 14 | "Without 2002" column | A post-hoc robustness check, labelled as such |

`README.md`, the report and the app each keep one sentence saying that AI assisted
the work. They are disclosures of how the project was made, not authorship; the
team decides whether the course requires them.
