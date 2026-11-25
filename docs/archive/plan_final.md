# Final push plan (15 → 27 November 2026)

Working branch: `final/analysis`. Nothing here reopens the team decisions D1–D8
recorded in the session brief; contradictions go to `docs/handoff.md`.

## Current state (verified on 15 November 2026)

- `uv sync --locked --dev` and `make check` pass on `master` (86 tests).
- `vote-transfer process --all-years` on the local raw files reproduces the ten
  bundled Parquet tables byte for byte.
- Implemented: acquisition with pinned manifests, cleaning/validation, one wide
  processed table per election, H0 (per-year `h0_evaluation.parquet`), a four-page
  Streamlit app, and a draft 61-row candidate table that no model reads yet.
- Not implemented: H0b, H1, H2, H3, cross-election evaluation, any figure for the
  report, the 2027 scenario page, the written deliverables.
- The two peer reviews are **not** in `docs/references/reviews/` (the folder does
  not exist). They were read from local copies outside the repository.

## Design choices that shape every later package

- **Normalised storage.** Each election stores `areas`, `outcomes` and `options`
  (labels). The wide table the app uses becomes a view computed on load, so shares
  and repeated denominators are no longer stored.
- **One predictions table** for every model, variant and election, plus one
  evaluation report holding the H3 folds and the input hashes.
- **Every model is a transfer matrix.** One function builds the matrix for an
  area; one function turns matrices into predictions; one scoring function is used
  for every model. H3 is a mixture of two matrices.
- **Numbers reach prose through generated files.** `vote-transfer analyse` writes
  `reports/results/*` and renders the report and findings from templates, so a
  rerun after the human coding review updates every number.

## Work packages and acceptance criteria

| WP | Content | Accept when |
|---|---|---|
| 1 | Makefile for all years, `bundle`/`archive` targets, stale folder references removed, test count no longer hard-coded, processed-vs-bundled drift check in `make check` and at app start | Documented commands rebuild everything; `make check` passes |
| 2 | `areas` / `outcomes` / `options` tables, blank and invalid kept for 2017 and 2022, wide view derived, long predictions table, data dictionary | H0a scores numerically identical to the pinned pre-refactor values; tests cover the new tables; app runs |
| 3 | Blind coding sheet, coder instructions, `review-agreement` (agreement, quadratic-weighted kappa, confusion matrix, disagreements), consistency and completeness checks, alternative coding as a model variant | Kit runs end to end on synthetic sheets in `tests/`; no real coder data exists in the repo |
| 4 | H0b, H1 (+ `tie=abstention`), H2-abst, H2-blank, H3 on each base with leave-one-election-out | Tests for identity rows, row sums, non-negativity, ties, missing-score fallback, `d = 2`, and no leakage; all models run on five elections |
| 5 | Comparison table, signed-error chart, 2022 scatter, sensitivity table, 2002 note, `findings.md` | One command regenerates every figure and result |
| 6 | "2027 scenarios" page on the 2022 electorate | Works offline from bundled data; covered in `tests/test_site.py` |
| 7 | Cross-election page; existing pages and honesty notes kept | Existing site tests still pass |
| 8 | Response to reviews, storage comparison, report draft, presentation outline, professor email | Consistent with generated results; pending human inputs marked |
| 9 | `docs/handoff.md` | Lists commits, commands, human tasks, open problems, final check output |

## Risks

- **Draft coding.** Every H1–H3 number depends on codes no one has reviewed. All
  outputs carry the coding status read from the table itself.
- **Fixed rules can fit badly.** D3–D4 are fixed before seeing results. If H2
  performs poorly (for example in 2002, where both finalists sit at 6 and 7), that
  is reported, not repaired.
- **Five elections.** Leave-one-election-out has five folds; held-out scores are
  descriptive, with no significance claim.
- **Model selection.** Naming a "best" model after comparing them on the same five
  elections is itself a selection step; the report says so.
- **New dependency.** Static figures need Matplotlib; the lock file must be
  refreshed, which needs registry access once.
- **Snapshot drift.** `processed/` and `bundled/` can diverge; WP1 adds the check.
