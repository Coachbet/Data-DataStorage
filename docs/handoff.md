# Handoff: analysis branch (`final/analysis`), 15 November 2026

Final report and code are due **27 November**; the presentation is on **2 December**.
Everything below is on the branch `final/analysis`. Nothing was pushed to `master`.

## What was done

| WP | Result | Commits |
|---|---|---|
| Plan | `docs/plan_final.md` | `e3fb9f3` |
| 1 Reproducibility | `make acquire/process/bundle` cover all years; `make data`, `make analysis`, `make archive`; folders that do not exist removed from the docs; test count no longer hard-coded; `vote-transfer check-snapshots` in `make check` and a warning at app start-up | `0f220b9`, `0b08a4a` |
| 2 Storage | `areas`, `outcomes`, `options` per election; blank and invalid kept for 2017 and 2022; wide table derived on load; one long `predictions.parquet` with an evaluation report | `f7165b7`, `0229703` |
| 3 Review kit | Blind coding sheet, coder instructions, `review-kit` and `review-agreement` commands, consistency and completeness checks, alternative coding as a variant. **No coding was done or simulated.** | `c709a00` |
| 4 Models | H0a (unchanged), H0b, H1, H2-abst, H2-blank, H3 on each base with leave-one-election-out; definitions in `docs/methodology.md` | `0229703`, `c709a00` |
| 5 Analysis | `vote-transfer analyse`: comparison table, signed errors, sensitivity, blank-only scoring, 2002 with and without, three figures, `findings.md`, `numbers.json`, templated documents | `42aae1a` |
| 6 Scenario page | "2027 scenarios" on the 2022 electorate, always beside H0b, permanent banner | `6678b4f` |
| 7 Site | "Compare models" page; existing pages and notes kept | `6678b4f` |
| 8 Documents | Report draft, storage comparison, response to reviews, presentation outline, professor email | `f2ca2b4` |
| 9 Handoff | This file | this commit |

Headline findings are in `reports/results/findings.md`. In one sentence: the
second baseline (H0b) matters more than any other change, H1 has the lowest mean
score only because of 2002, H2 as specified is worse than the baselines, H3 adds
little, and the order of models changes under the alternative coding. The honest
answer to the research question is currently "inconclusive".

## How to reproduce

```bash
uv sync --locked --dev
make check        # tests, lint, format, snapshot comparison
make analysis     # evaluate -> bundle -> analyse; works on a fresh clone, offline
make data         # full rebuild from the Ministry files (needs data.gouv.fr once, ~293 MB)
make app          # the Streamlit app
make archive      # zip of tracked files for submission
```

Verified on 15 November 2026:

- `make data` from the local raw files completes; the seven raw files keep their
  SHA-256 hashes; processed tables equal the bundled ones byte for byte.
- A fresh clone of the branch passes `make check`, and `make analysis` there
  leaves `git status` clean: every committed result, figure and rendered document
  is exactly what the code produces.
- H0a is unchanged by the storage refactor: the derived view and the H0a
  comparison equal the previous Parquet files exactly, and the five H0a scores
  match the values pinned before the refactor to 1e-12.

## Human tasks remaining

- [ ] **Assign an owner to every item below.** Owners were deliberately not assigned.
- [ ] **Code the candidate table.** Two members each copy
      `data/reference/review/coding_sheet_template.csv`, fill it alone following
      `data/reference/review/README.md`, and commit it before talking to each other.
- [ ] Run `uv run vote-transfer review-agreement --coder-a ... --coder-b ...` and
      keep `reports/results/coding_agreement.json`.
- [ ] Resolve each disagreement; update `data/reference/candidate_positions.csv`
      (family, score, alternative, note) and set `review_status` to `reviewed`.
      Decide the two flagged consistency cases (PS, UDF) and the two Cheminade rows.
- [ ] Run `make analysis` and `make check`, then commit the regenerated files.
      Outputs switch to "reviewed coding" by themselves.
- [ ] **Re-read the prose after that rerun.** Numbers update automatically; the
      sentences around them (in `docs/templates/`) were written for the draft
      results and may no longer be true. Check in particular the interpretations
      in `findings.md`, report section 6 and outline slides 9–10.
- [ ] Remove every `[PENDING: coder agreement]` marker (templates, response to
      reviews, quality document) and write the measured agreement in its place.
- [ ] **Send the professor email** (`docs/email_professor_H3.md`), record the
      answer, and remove `[PENDING: professor approval for H3]`. If the answer is
      no, see open problem 3.
- [ ] Edit the report down to five pages **in the final format** (the Markdown
      draft is about 2,300 words with three figures; page count is untested).
      Edit `docs/templates/report.md`, never `docs/report/report.md`.
- [ ] Build the slides from `docs/presentation_outline.md`.
- [ ] Check the repository link printed in the report (reviewers got "page not
      found" from the 3 November PDF; the repository was public on 15 November).
- [ ] Look at the app in a browser: the navigation now has six items and its
      layout was not visually checked (tests cover behaviour, not appearance).
- [ ] Confirm the open problems below, then merge the pull request.

## Open problems and contradictions, with options

1. **The peer reviews are not in the repository.** The brief places them in
   `docs/references/reviews/`; that folder does not exist. They were read from
   local copies (`Peer Review Round 1 Comments.pdf`,
   `Peer_Review_Report_Checkpoint_2.pdf`). They were not copied in, because the
   repository is public and the Checkpoint 2 report names its five authors.
   Options: (a) add them, with the reviewers' agreement; (b) keep them out and
   cite them by title, as `docs/response_to_reviews.md` does now.

2. **Weights in the H3 fit against an older sentence.** `docs/methodology.md`
   (31 October) says registered-voter weights "must not enter model fitting".
   Decision D5 says `p` minimises the primary score on training elections, and
   that score uses those elections' round-two weights. D5 was implemented as
   written; the held-out election's weights and outcomes never enter the fit.
   Options: (a) confirm D5 and reword the older sentence (a note is already in
   the methodology); (b) fit with unweighted area errors, a small code change
   in `models.fit_p`.

3. **H3 is implemented and evaluated before approval.** The brief asked for it;
   the course rule asks for approval first. H3 rows are in the tables, the
   figures and the app. If approval is refused: remove the three `H3(...)` names
   from `MODEL_ORDER` in `analysis.py` and `SCENARIO_MODELS` in `scenario.py`,
   rerun `make analysis`, and cut the H3 paragraphs. No other model depends on it.

4. **The tie rule never applies.** No eliminated candidate is equidistant from
   both finalists under the primary or the alternative coding, so `tie=split`
   and `tie=abstention` give identical results. The requested sensitivity check
   is reported as exactly that. A fourth variant (alternative coding with
   `tie=abstention`) was added so the check would be informative if a review
   changes codes; it costs nothing and can be removed.

5. **"Best model" depends on 2002.** The scenario page defaults to the lowest
   five-election mean, as specified, which is H1. Without 2002, H1 ranks fifth.
   Options: (a) keep the specified default (H0b is always shown beside it);
   (b) default to H0b; (c) show all models side by side.

6. **H2 fits badly by construction in three elections.** With finalists at 4 and
   7 (2017, 2022) or 6 and 7 (2002), every left-coded group is at least two steps
   from both and becomes a non-vote. This is D4 as written and was not changed.
   The report says the threshold was not tuned.

7. **The alternative coding changes all listed rows at once, finalists
   included** (for example Macron from Centre to Centre-right). It is one
   alternative scenario, not a search. The team may prefer per-candidate checks.

8. **Blank-only scoring needed a convention.** "H2 on blank votes only" was
   implemented as a five-outcome score for 2017 and 2022 in which first-round
   invalid ballots stay invalid and every modelled inflow counts as blank. It is
   documented in `analysis.blank_only_table`; the team should confirm it.

9. **The scenario page offers candidates, not families.** D7 allowed "two 2022
   candidates (or two families)"; only candidates are implemented. No map is
   shown: the repository has no boundary data and none was added.

10. **A rebuild changes the timestamp in each `quality_report.json`.** Data files
    are byte-identical, but `processed_at_utc` makes the five bundled reports
    show as modified after `make data`. Options: (a) restore them with
    `git checkout -- data/bundled` when nothing else changed; (b) drop the
    timestamp from the report.

11. **Not re-run in this session:** `vote-transfer crosscheck --year 2022`
    (network). The report repeats the earlier validated statement that our 2022
    sums match the Ministry's national summaries.

12. **Working-method tools.** The `ub-mode` skill names three tools (crapper,
    dryer, mutator) that are not installed here, so no complexity, duplication or
    mutation report was produced. The skill also says to push to the main line;
    the brief forbids pushing to `master`, and the brief was followed.

13. **The 3 November quality document was extended**, not rewritten: section 5 is
    a dated addendum on the candidate table. If that document must stay as
    submitted, move the addendum to its own file.

## Final `make check` summary

```text
204 passed
ruff check: All checks passed!
ruff format --check: 51 files already formatted
vote-transfer check-snapshots: Processed and bundled snapshots are consistent.
```

## Action log

| Step | Action | Reason |
|---|---|---|
| 1 | Read `AGENTS.md`, scope, methodology, quality, dictionary, validation, reference README, the code, the brief, both reviews and the proposal feedback | Required before any change |
| 2 | Created `final/analysis`; ran `uv sync --locked --dev`, `make check`, `process --all-years`; compared with `data/bundled/` | Baseline: green, byte-identical |
| 3 | Pinned the five H0 scores and kept copies of the old snapshots outside the repo | To prove H0a did not change |
| 4 | Wrote `docs/plan_final.md` | Requested first deliverable |
| 5 | WP1: tests first for drift detection, then code, Makefile, docs | Review 2, Q3 and Q5 |
| 6 | WP2: tests first, normalised tables, derived view, regenerated snapshots, removed the ten superseded generated tables from `data/processed/` | Review 2, Q2, Q4, Q5 |
| 7 | WP4: tests first, `models.py`, shared scoring, predictions on disk, `evaluate` | Decisions D2–D5; no score was looked at before the rules were coded |
| 8 | WP3: tests first, `review.py`, template, coder README, quality addendum | Decision D6; coding left to humans |
| 9 | Looked at results for the first time; added the fourth variant when no tie was found | To keep the tie check informative |
| 10 | WP5: analysis tables, validated a four-colour palette, figures, templates, guard test "committed equals fresh" | Numbers must be regenerable |
| 11 | WP6/WP7: scenario backend and two app pages, offline tests | Decision D7; review 2, Q6 |
| 12 | WP8: documents; SQLite test to back the storage comparison | Brief: detailed comparison with an alternative |
| 13 | Found `make analysis` failed on a fresh clone; fixed `bundle`; verified in a clean clone | Acceptance criterion of WP5 |
| 14 | Ran `make data` from raw; restored the five timestamp-only report changes | Full-rebuild check without noise in the commit |
| 15 | WP9: this file; pushed the branch and opened a pull request | Brief, section 3 |
