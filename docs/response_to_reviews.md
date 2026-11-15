# Response to feedback

Draft for the team to edit. One row per comment: what was said, what we did (or
why we did not act), and where a reader can see it. Results cited here are in
`reports/results/findings.md`; this page contains no result figures of its own.

Sources: Peer Review Report, Checkpoint 1 (October 2026); Peer Review Report,
Checkpoint 2 (10 November 2026); the professor's "Feedback on the Project
Proposals" (`docs/references/archive/`). The two peer-review PDFs are not in the
repository yet (see `docs/handoff.md`).

## Checkpoint 1 (acquisition)

| # | Comment | Action | Where |
|---|---|---|---|
| 1.1 | No standalone proposal document was provided. | The original proposal is now in the repository beside the acquisition note. | `docs/references/project-proposal.pdf` |
| 1.2 | No raw data and no acquisition script were submitted. | Acquisition is implemented for all five elections: pinned resource IDs, a manifest with URL, date, size and SHA-256 per file, and a clean re-download that reproduced every hash. | `backend/vote_transfer/infrastructure/official.py`, `data/raw/official/<year>/manifest.json`, `docs/data_acquisition.md` |
| 1.3 | No running code was provided. | A tested package and command-line tool cover acquisition, cleaning, storage, models, analysis and the app. | `backend/vote_transfer/`, `Makefile`, `tests/` |
| 1.4 | H4 and H5 rely on one 2017 volunteer experiment (Voter Autrement): temporal and selection bias across five elections. | **Accepted.** H4 and H5 are dropped. Core models are H0a, H0b, H1, H2 and H3. | `docs/methodology.md` ("Out of scope"), `docs/project_scope.md` |
| 1.5 | Scope creep across six external datasets; recommendation to prune and focus on the baseline through H3. | **Accepted.** The only inputs are the Ministry files and our own candidate table. Socioeconomic indicators, media mentions, Political Compass data and preference surveys were removed. | `docs/project_scope.md` |
| 1.6 | Scraping Wikipedia for 2027 polls adds manual work late in the project. | **Accepted, and taken further.** No 2027 poll is collected. The 2027 page applies an assumption to the 2022 first-round electorate and is labelled a hypothetical scenario, not a forecast. | `site/app.py` ("2027 scenarios"), `backend/vote_transfer/application/scenario.py` |
| 1.7 | The Chapel Hill Expert Survey (CHES) is appropriate for positions. | **Not followed, with a stated reason.** CHES rates parties, not candidacies; many of our 61 candidacies are independents or minor parties that would have to be placed by hand anyway. We use one hand-coded 1–7 family scale for every candidacy and treat its reliability as a quality problem in its own right (see 2.1, 2.19). CHES remains a possible external check. | `docs/project_scope.md` ("Change from the acquisition note"), `data/reference/README.md` |
| 1.8 | Suggestion to calibrate on 2017 and 2022 first. | **Partly followed.** All five elections were feasible, so the fitted model (H3) uses leave-one-election-out over five elections instead of two. | `docs/methodology.md` (H3) |
| 1.9 | Commended: explicit baseline, incremental hypotheses, fitting on some elections and testing on others. | Kept. The baseline is now reported in two forms and every fitted score is held-out. | `reports/results/model_comparison.csv` |

## Checkpoint 2 (quality, cleaning, storage)

| # | Comment | Action | Where |
|---|---|---|---|
| 2.1 | **Q1.** The hand-coded candidate table is the main input of H1 and H2 but is absent from the quality assessment: all rows are drafts, most list an alternative, the scale is coarse, two parties are coded differently across elections, two scores are missing. | The table now has its own quality rows: accuracy (two-coder agreement), consistency (same party, same family) and completeness (rows without a score). Consistency and completeness are computed and reported; **accuracy is pending the human coding**. `[PENDING: coder agreement]` | `docs/data_quality_and_cleaning.md` §5, `reports/results/candidate_table_quality.json`, `backend/vote_transfer/application/review.py` |
| 2.2 | **Q1.** The coarse scale will produce frequent ties under H1 and no tie rule exists. | Tie rule fixed before any result: an equidistant group splits 50/50 between the finalists; `tie=abstention` is a named sensitivity variant. We then counted the ties: the result is in the findings. | `docs/methodology.md` (H1), `reports/results/tied_groups.csv`, `findings.md` §5 |
| 2.3 | **Q2.** Merging blank and invalid ballots is justified for comparison across years but fits H2 badly; about a quarter of the combined category is invalid ballots. | The combined outcome stays primary (one definition for five elections). For 2017 and 2022 we added a sensitivity analysis that scores blank ballots alone and isolates the invalid-ballot error, which is the same for every model. | `reports/results/blank_only.csv`, `findings.md` §5 |
| 2.4 | **Q2.** The separate blank and invalid counts survive only in the interim tables. | They are now stored in the processed and bundled `areas` table for 2017 and 2022, and null before 2017. | `data/bundled/<year>/areas.parquet`, `docs/data_dictionary.md` |
| 2.5 | **Q3.1.** The GitHub link in the PDF returns "page not found". | **Open, human task.** The repository is private; the team must make it readable for the graders or submit the `make archive` zip. | `docs/handoff.md` |
| 2.6 | **Q3.2.** `make acquire` and `make process` handle 2022 only. | Both now cover all five elections; `make data` runs the full rebuild. | `Makefile` |
| 2.7 | **Q3.3.** The reproduction instructions leave out `bundle`. | `bundle` is in the Makefile sequence, in the README and in the quality document's commands. | `Makefile`, `README.md` |
| 2.8 | **Q3.4.** The READMEs describe `data/raw/2017/` and `data/archive/legacy/`, which do not exist. | References removed. | `README.md`, `data/README.md`, `docs/data_acquisition.md` |
| 2.9 | **Q3.5.** `docs/validation.md` reports 72 tests; the suite has 86. | The current count is no longer written in the document; `make check` prints it. Past entries are marked as dated records. | `docs/validation.md` |
| 2.10 | **Q3.6.** The archive weighed 160 MB because of `.venv/`, raw files and `.DS_Store`. | `make archive` builds the archive with `git archive`: tracked files only. | `Makefile` |
| 2.11 | **Q4.** The candidate table is a CSV although the document argues against CSV. | One paragraph explains the exception: the table is edited by hand, diffed in Git, and its types are enforced on load. | `docs/data_dictionary.md`, `docs/storage_comparison.md` |
| 2.12 | **Q4.** One `h0_evaluation.parquet` per election will multiply files; a single long predictions table would make comparison easier. | Replaced by one long table with `model`, `variant` and `train_elections` columns, plus one evaluation report. | `data/bundled/predictions.parquet`, `docs/data_dictionary.md` |
| 2.13 | **Q4.** A database is not needed yet; DuckDB could query the Parquet files later. | Agreed. The detailed comparison of Parquet with SQLite/PostgreSQL and with DuckDB is written, including a test that loads our tables into SQLite with declared constraints. | `docs/storage_comparison.md`, `tests/test_storage.py` |
| 2.14 | **Q5.** Possible update anomaly between `processed/` and `bundled/`. | A check compares the two copies and also detects predictions older than their inputs. It runs in `make check` and the app warns at start-up. | `vote-transfer check-snapshots`, `backend/vote_transfer/application/datasets.py` |
| 2.15 | **Q5.** The repeated `registered` column and the stored `share` are a denormalised design. | The processed data is split into an area table and an outcome table (plus option labels). Shares are computed. The wide table is a view built on load, so the app is unchanged. H0 results were verified identical before and after. | `backend/vote_transfer/application/processing.py`, `tests/test_storage.py` |
| 2.16 | **Q6.** No chart in the document; every app view covers one election; the H0 score is quoted for 2022 only. | A cross-election page and three generated figures: the model comparison for all five elections, the signed error by outcome (the chart the reviewers asked for first) and a predicted-against-observed scatter by area with overseas areas and voters abroad highlighted. | `reports/figures/`, app page "Compare models" |
| 2.17 | **Q6.** 2002 is an outlier; H0 over-predicts abstention in every election. | Both confirmed and reported. Every summary is given with and without 2002. | `findings.md` §2–3 |
| 2.18 | **Q8.** Does "the rest of the electorate" include first-round abstainers? Is H0 a deliberately weak baseline? | It did, and that choice explains most of its error. We keep it unchanged as **H0a** and add **H0b**, which splits eliminated voters between the two finalists and blank/invalid only. Both are reported; later models are judged against both. | `docs/methodology.md` (H0b), `findings.md` §1 and interpretation 1 |
| 2.19 | **Q9.1–9.2.** Two members should code all 61 records independently and report percentage agreement and a weighted kappa, with disagreements. | The kit is built: a blind sheet, coder instructions, and a script computing percentage agreement, quadratic-weighted kappa, the confusion matrix and the disagreements. **The coding itself is human work and has not been done.** `[PENDING: coder agreement]` | `data/reference/review/`, `vote-transfer review-agreement` |
| 2.20 | **Q9.3.** Add the table to the quality assessment (accuracy, consistency, completeness). | Done; see 2.1. | `docs/data_quality_and_cleaning.md` §5 |
| 2.21 | **Q9.4.** Define the tie rule and the treatment of the Cheminade records before implementing H1. | Both were fixed before any result was computed: 50/50 split; candidates without a score use the H0b row. | `docs/methodology.md` |
| 2.22 | **Q9.5.** Plan a sensitivity analysis on `alternative_family`. | Every model is rerun with the alternative coding; the ranking under both codings is reported. | `reports/results/sensitivity.csv`, `findings.md` §5 |
| 2.23 | Availability: no note on changes since the first submission. | This document. | `docs/response_to_reviews.md` |
| 2.24 | **Q7.** Strongest part: traceability from raw files to cleaned tables. | Kept unchanged: raw files and manifests were not modified by any of the work above. | `data/raw/official/` |

## Professor's feedback on the proposals

| # | Comment | Action | Where |
|---|---|---|---|
| P1 | Determine the data from the question; remove datasets the question does not need. | Only two inputs remain: official results (the outcome and the first-round structure) and candidate positions (needed by H1–H3). Removing either makes the question unanswerable. | `docs/project_scope.md` |
| P2 | Narrow the project to one coherent investigation. | One question; every model is a transfer matrix scored by one rule. | `docs/methodology.md` |
| P3 | Make the operationalisation precise: two members should compute a variable the same way. | Shares, outcomes, the score and every model rule are defined as formulas. The one variable two members could code differently, the candidate family, is the subject of the two-coder review. | `docs/methodology.md`, `data/reference/review/README.md` |
| P4 | More data is not a better project. | See 1.5. | — |
| P5 | Do not promise sophisticated analysis before understanding the data. | Four of the five model families have no fitted parameter. The only fitted model has one parameter, validated on held-out elections, and is submitted to the professor for approval first. | `docs/email_professor_H3.md` |
