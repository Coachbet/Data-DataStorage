<!-- Generated from docs/templates/presentation_outline.md by `vote-transfer analyse`. Edit the template, not this file. -->

# Presentation outline (2 December, 15 minutes)

Draft for the team to turn into slides. Twelve slides, about 75 seconds each.
Numbers are filled from `reports/results/numbers.json`. Candidate positions: **poll-based scale**.

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

**5. Placing 61 candidacies without placing them ourselves**
- Polling institutes list candidates left to right in their reports: we collected 22 orders from 9 institutes, 2002–2022, each with its source link.
- Score from 0 (left) to 1 (right): evenly spaced within a poll, averaged across institutes.
- 3 candidacies we cannot place (Cheminade 2012, Cheminade 2017, Lassalle 2017): removed, their voters follow H0b.
- Replaced our first hand-coded 1–7 scale, which no outside source checked; it stays as a comparison.
- Figure: the 2017 scale, with the seven institutes' orders behind it.

**6. Storage: normalised Parquet, compared with a database**
- `areas`, `outcomes`, `options`, one long `predictions` table; shares computed, not stored.
- A database gives declarative constraints; we tested our tables in SQLite.
- We keep files: byte-identical rebuilds, hashes, 584 kB in Git; constraints enforced in code.
- Figure: schema diagram with the derived view.

**7. Five assumptions, each one sentence**
- H0a: like everyone else, abstainers included. H0b: like everyone who voted.
- H1: nearest finalist. H2: nearest, unless at least one third of the scale from both (then abstain, or vote blank).
- H3: a fitted share `p` ignores proximity. Rules fixed before any result.
- Figure: one transfer matrix, with identity rows highlighted.

**8. Result 1: the first baseline was weak for one reason**
- H0a over-predicts abstention in 5 of 5 elections, by 8.6 to 30.0 pp.
- H0b beats it in 5 of 5: mean 5.1 against 8.7 pp.
- This came from a reviewer's question.
- Figure: `reports/figures/signed_error_by_outcome.png`.

**9. Result 2: no stable winner**
- Lowest five-election mean: H1 (4.7 pp), but it beats H0b in only 2 of 5 elections, mostly thanks to 2002.
- Without 2002, H1 ranks 7 of 8; H0b is at 3.0 pp.
- H2 fails in 2002: both finalists on the right, so the whole left is "too far" and sent to a non-vote (30% of registered voters), while it voted Chirac. Elsewhere H2 is close to H1.
- The fitted H3 throws the H2 rule away (`p` from 0.77 to 1.00).
- Figure: `reports/figures/model_comparison.png`.

**10. How fragile is it?**
- On our old hand-coded 1–7 scale: lowest mean still H1, H0b still 2; H2 much worse (+2.9 pp).
- Main conclusion holds on both scales; H2 depends on where candidates are placed.
- Tie rule: 2 exact ties, at most 0.10 pp of change.
- Overseas areas in 2022: H1 8.1 pp, H0b 3.3 pp.
- Figure: `reports/figures/predicted_vs_observed_2022.png`.

**11. A 2027 scenario, not a forecast**
- The 2022 first-round electorate, two stand-in finalists, one assumption. Default H0b; one option shows all models side by side.
- No 2027 data, no polls.
- The spread between assumptions is the message.
- Figure: live demo or screenshot of the "2027 scenarios" page.

**12. Answer, limits, and what we changed**
- Answer: inconclusive. Proximity explains 2002; elsewhere a proportional split among voters does as well.
- Limits: aggregate inference, an order not a distance, one institute for 2002, one dimension, five elections.
- Changed after feedback: second baseline, candidate positions from polling institutes, normalised storage, cross-election charts.
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

**Why a threshold of one third for H2? Did you try others?**
It is our original rule (two steps out of six on the 1–7 scale), fixed before looking at results. Trying thresholds until one fits would be
tuning on the evaluation elections, and five elections cannot validate it.

**How do you know the candidate positions are right?**
They are not ours: they are the orders published by 9 polling institutes,
each linked to its source. Where institutes disagree too much we do not place the
candidate. We also rerun everything on our old hand-coded scale: the main conclusion
does not change.

**Why not score candidates from their programmes, or use the Manifesto Project?**
Many 2002–2007 minor candidates have no programme online, and the Manifesto Project
codes legislative manifestos of parties with seats, so most minor presidential
candidates are missing.

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
