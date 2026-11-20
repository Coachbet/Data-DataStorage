<!-- Generated from docs/templates/presentation_outline.md by `vote-transfer analyse`. Edit the template, not this file. -->

# Presentation outline (2 December, 15 minutes)

Draft for the team to turn into slides. Twelve slides, about 75 seconds each.
Numbers are filled from `reports/results/numbers.json`. Status: **poll-based scale**.
`[PENDING: coder agreement]` on slides 5, 8 and 10.

## Slides

**1. Two rounds, one electorate: what changes?**
- Question: which assumption about voter behaviour best explains the second round?
- 5 elections, 2002–2022; one observation is one area in one election (522 in all).
- We compare aggregate patterns; we never observe an individual's transfer.
- Figure: the app's home snapshot (round 1 and round 2 bars for one election).

**2. Everything is a share of registered voters**
- Four outcomes: finalist A, finalist B, blank/invalid, abstention.
- Abstention is an outcome, so the shares always sum to 100%.
- Why it matters: the usual "share of valid votes" hides the two outcomes that move most.
- Figure: app "Explore" page, registered voters against valid votes.

**3. Data: original Ministry files, pinned by hash**
- 293 MB of polling-station text, 673,228 station-round records.
- Acquisition script records URL, date, size and SHA-256; a different file stops the pipeline.
- Coverage limit: 100 areas in 2002, 101 in 2007, 107 from 2012.
- Figure: pipeline diagram (acquire → validate → aggregate → models → report).

**4. Cleaning: verify, flag, never repair**
- Zero-violation rules; a failure means our parser is wrong.
- Nothing removed or imputed; overseas areas flagged and kept.
- Blank and invalid combined for comparability; kept separately for 2017 and 2022.
- Figure: table of checks from the quality document.

**5. The weakest input is ours: the candidate table**
- 61 candidacies coded by hand on a 1–7 left–right scale.
- Consistency check flags PS, UDF; 2 rows have no score.
- Two coders, blind sheets, weighted kappa: `[PENDING: coder agreement]`.
- Figure: the 1–7 scale with a few placed candidates.

**6. Storage: normalised Parquet, compared with a database**
- `areas`, `outcomes`, `options`, one long `predictions` table; shares computed, not stored.
- A database gives declarative constraints; we tested our tables in SQLite.
- We keep files: byte-identical rebuilds, hashes, 584 kB in Git; constraints enforced in code.
- Figure: schema diagram with the derived view.

**7. Five assumptions, each one sentence**
- H0a: like everyone else, abstainers included. H0b: like everyone who voted.
- H1: nearest finalist. H2: nearest, unless two steps from both (then abstain, or vote blank).
- H3: a fitted share `p` ignores proximity. Rules fixed before any result.
- Figure: one transfer matrix, with identity rows highlighted.

**8. Result 1: the first baseline was weak for one reason**
- H0a over-predicts abstention in 5 of 5 elections, by 8.6 to 30.0 pp.
- H0b beats it in 5 of 5: mean 5.1 against 8.7 pp.
- This came from a reviewer's question.
- Figure: `reports/figures/signed_error_by_outcome.png`.

**9. Result 2: no stable winner**
- Lowest five-election mean: H1 (4.7 pp), but it beats H0b in only 2 election.
- Without 2002, H1 ranks 7 of 8; H0b is at 3.0 pp.
- H2 has the highest errors: with finalists at 0.5 and 0.9, every group coded none is exactly 0.3 steps away and is sent to a non-vote (0.0% of registered voters in 2022). A finding about thresholds on a coarse scale.
- The fitted H3 throws the H2 rule away (`p` from 0.77 to 1.00).
- Figure: `reports/figures/model_comparison.png`.

**10. How fragile is it?**
- Alternative coding: the order of models changes; lowest mean becomes H3(H2-blank).
- Tie rule: irrelevant, 0 ties occur.
- Overseas areas in 2022: H1 8.1 pp, H0b 3.3 pp.
- Figure: `reports/figures/predicted_vs_observed_2022.png`.

**11. A 2027 scenario, not a forecast**
- The 2022 first-round electorate, two stand-in finalists, one assumption. Default H0b; one option shows all models side by side.
- No 2027 data, no polls.
- The spread between assumptions is the message.
- Figure: live demo or screenshot of the "2027 scenarios" page.

**12. Answer, limits, and what we changed**
- Answer: inconclusive. Proximity explains 2002; elsewhere a proportional split among voters does as well.
- Limits: aggregate inference, draft coding, one dimension, five elections.
- Changed after feedback: second baseline, coder review, normalised storage, cross-election charts.
- Figure: the three-line summary; repository link and `make analysis`.

## Likely questions, short answers

**Why not ecological regression or a fitted transfer matrix?**
The course asks for simple methods first, and with five elections a full matrix
has far more parameters than observations can identify. Our single fitted
parameter was already unstable across folds.

**Is H1 the best model or not?**
It has the lowest mean, because of 2002. In the other four elections H0b is as
good or better. We do not claim a best model.

**Why keep H0a if it is clearly worse?**
It is the baseline we committed to at the start. Showing both makes visible that
one modelling choice, not the data, caused most of its error.

**Why a threshold of two for H2? Did you try others?**
It was fixed before looking at results. Trying thresholds until one fits would be
tuning on the evaluation elections, and five elections cannot validate it.

**How do you know the candidate coding is right?**
We do not, which is why two people code it independently and we report agreement
and rerun everything on the alternative coding. `[PENDING: coder agreement]`

**Why is 2002 so different?**
Abstention fell between rounds and nearly all voters outside the far right ended
on one side. H0a predicts 49.7% abstention against
19.7% observed.

**Why Parquet and not a database?**
Written once, read by column, small, and it must rebuild byte for byte for a
reader with no setup. We lose declarative constraints and enforce them in code.

**Could the 2027 page predict the election?**
No. It applies an assumption to the 2022 electorate. Different candidates, a
different electorate and a different campaign are all outside it.

**What about voters abroad and overseas areas?**
Kept and flagged. Missing from the 2002 and 2007 files, so those years describe
covered areas only. They fit worse under H1 in 2022.

**How was AI used?**
For code, tests and drafting. Decisions, the coding of candidates and the
interpretation are the team's.
