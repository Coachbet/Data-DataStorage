# Presentation outline (2 December, 15 minutes)

Draft for the team to turn into slides. Eleven slides, about 80 seconds each.
Numbers are filled from `reports/results/numbers.json`. Candidate positions: **{{coding_status}}**.

## Slides

**1. Two rounds, one electorate: what changes?**
- Question: which assumption about voter behaviour best explains the second round?
- {{n.elections}} elections, 2002–2022; one observation is one area in one election ({{areas.total}} in all).
- We compare aggregate patterns; we never observe an individual's transfer.
- Figure: the app's home snapshot (round 1 and round 2 bars for one election).

**2. Everything is a share of registered voters**
- Four outcomes: finalist A, finalist B, blank/invalid, abstention.
- Abstention is an outcome, so the shares always sum to 100%.
- Why it matters: the usual "share of valid votes" hides the two outcomes that move most.
- Figure: app "Explore" page, registered voters against valid votes.

**3. Data: original Ministry files, pinned by hash**
- {{storage.raw_mb|.0f}} MB of polling-station text, {{storage.station_rows|,}} station-round records.
- Acquisition script records URL, date, size and SHA-256; a different file stops the pipeline.
- Coverage limit: {{areas.2002}} areas in 2002, {{areas.2007}} in 2007, {{areas.2022}} from 2012.
- Figure: pipeline diagram (acquire → validate → aggregate → models → report).

**4. Cleaning: verify, flag, never repair**
- Zero-violation rules; a failure means our parser is wrong.
- Nothing removed or imputed; overseas areas flagged and kept.
- Blank and invalid combined for comparability; kept separately for 2017 and 2022.
- Figure: table of checks from the quality document.

**5. Placing {{n.candidacies}} candidacies without placing them ourselves**
- Polling institutes list candidates left to right in their reports: we collected {{scale.polls}} orders from {{scale.institutes}} institutes, 2002–2022, each with its source link.
- Score from 0 (left) to 1 (right): evenly spaced within a poll, averaged across institutes.
- {{scale.unplaced}} candidacies we cannot place ({{scale.unplaced_list}}): removed, their voters follow H0b.
- Replaced our first hand-coded 1–7 scale, which no outside source checked; it stays as a comparison.
- Figure: the 2017 scale, with the seven institutes' orders behind it.

**6. Storage: normalised Parquet, compared with a database**
- `areas`, `outcomes`, `options`, one long `predictions` table; shares computed, not stored.
- A database gives declarative constraints; we tested our tables in SQLite.
- We keep files: byte-identical rebuilds, hashes, {{storage.total_parquet_kb|.0f}} kB in Git; constraints enforced in code.
- Figure: schema diagram with the derived view.

**7. Five assumptions, each one sentence**
- H0a: like everyone else, abstainers included. H0b: like everyone who voted.
- H1: nearest finalist. H1-soft: both finalists, the nearer one gets more. H2: nearest, unless at least one third of the scale from both (then abstain, or vote blank).
- H3: a fitted share `p` ignores proximity. H0a, H1 and H2 were fixed before any result; H0b (in response to H0a's abstention error) and H1-soft were added afterwards.
- Figure: one transfer matrix, with identity rows highlighted.

**8. Result 1: the first baseline was weak for one reason**
- H0a over-predicts abstention in {{signed_positive_elections.H0a.abstention}} of {{n.elections}} elections, by {{signed_min.H0a.abstention}} to {{signed_max.H0a.abstention}} pp.
- H0b beats it in {{wins.H0b.vs_H0a}} of {{n.elections}}: mean {{score.H0b.mean}} against {{score.H0a.mean}} pp.
- This came from a reviewer's question.
- Figure: `reports/figures/signed_error_by_outcome.png`.

**9. Result 2: no stable winner**
- Lowest five-election mean: {{best.model}} ({{best.mean}} pp), but it beats H0b in only {{wins.H1.vs_H0b}} of {{n.elections}} elections, mostly thanks to 2002.
- Without 2002, {{best.model}} ranks {{best.rank_without_2002}} of {{n.models}}; H0b is at {{score.H0b.mean_without_2002}} pp.
- H2 fails in 2002: both finalists on the right, so the whole left is "too far" and sent to a non-vote ({{h2.2002.beyond_pct|.0f}}% of registered voters), while it voted Chirac. Elsewhere H2 is close to H1.
- The fitted H3 throws the H2 rule away (`p` from {{p.H2-blank.min|.2f}} to {{p.H2-abst.max|.2f}}).
- Figure: `reports/figures/model_comparison.png`.

**10. How fragile is it?**
- On our old hand-coded 1–7 scale: lowest mean still {{sens.primary.split.best.model}}, H0b still {{sens.primary.split.rank.H0b}}; H2 much worse ({{sens.primary.split.change.H2-abst.mean|+.1f}} pp).
- Main conclusion holds on both scales; H2 depends on where candidates are placed.
- Tie rule: {{ties.polls.count}} exact ties, at most {{sens.polls.abstention.max_abs_change|.2f}} pp of change.
- Overseas areas in 2022: {{best.model}} {{territory.overseas.H1.2022}} pp, H0b {{territory.overseas.H0b.2022}} pp.
- Figure: `reports/figures/predicted_vs_observed_2022.png`.

**11. Answer, limits, and what we changed**
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
They are not ours: they are the orders published by {{scale.institutes}} polling institutes,
each linked to its source. Where institutes disagree too much we do not place the
candidate. We also rerun everything on our old hand-coded scale: the main conclusion
does not change.

**Why not score candidates from their programmes, or use the Manifesto Project?**
Many 2002–2007 minor candidates have no programme online, and the Manifesto Project
codes legislative manifestos of parties with seats, so most minor presidential
candidates are missing.

**Why is 2002 so different?**
Abstention fell between rounds and nearly all voters outside the far right ended
on one side. H0a predicts {{predicted.H0a.2002.abstention}}% abstention against
{{actual.2002.abstention}}% observed.

**Why Parquet and not a database?**
Written once, read by column, small, and it must rebuild byte for byte for a
reader with no setup. We lose declarative constraints and enforce them in code.

**What about voters abroad and overseas areas?**
Kept and flagged. Missing from the 2002 and 2007 files, so those years describe
covered areas only. They fit worse under H1 in 2022.

**How was AI used?**
For code, tests and drafting. Decisions, the collection of the poll orders and the
interpretation are the team's.
