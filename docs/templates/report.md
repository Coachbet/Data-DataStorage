# Which assumptions about voter behaviour best explain second-round results in French presidential elections (2002–2022)?

Victor Henz, Edgar Gusching, Louis Bettelli, Lucas Magret Delord, Oscar Moulet ·
Data, Data Storage, Data Collection · final report, draft of the analysis branch

> **Status: {{coding_status}}.** H1, H2 and H3 place candidates with the left-to-right
> orders published by polling institutes. The earlier hand-coded 1–7 scale is kept as
> a comparison ({{comparison_coding_status}}).

## 1. Question

Between the two rounds of a French presidential election, the supporters of
eliminated candidates must choose again: one of the two finalists, a blank or
invalid ballot, or abstention. We ask **which simple assumption about that choice
best reproduces the second-round result of each area from its first-round
result**, over the {{n.elections}} elections from 2002 to 2022.

One observation is one reporting area (département, overseas area or voters
abroad) in one election: {{areas.total}} observations. Every share is a share of
**registered voters**, so abstention and blank/invalid ballots are outcomes, not
missing data. We compare aggregate patterns. Individual ballots are secret, so
no result here says how any person voted. An inconclusive answer is possible, and
section 6 argues that it is the honest one.

## 2. Data and acquisition

**Source.** The Ministry of the Interior's polling-station result files for both
rounds of each election, published on data.gouv.fr: {{storage.raw_mb|.0f}} MB of
text, {{storage.station_rows|,}} station-round records. We chose the original
station files over ready-made consolidated tables so that every aggregation step
is ours and checkable.

**Procedure.** `vote-transfer acquire` queries the data.gouv.fr API, selects a
pinned resource identifier per election and round, and records the URL, retrieval
time, size and SHA-256 hash in a versioned manifest. Any later download must
reproduce the hash, and processing refuses different bytes.

**Second source, collected by us.** H1–H3 need a left–right position for each of
the {{n.candidacies}} first-round candidacies. Polling institutes list the
candidates in a left-to-right order in their published reports, and these orders
cover every candidate, minor ones included. We extracted the order of
{{scale.polls}} polls by {{scale.institutes}} institutes: the last pre-election poll
we could find per institute ({{scale.polls.2002}} for 2002, {{scale.polls.2007}} for
2007, {{scale.polls.2012}} for 2012), and the {{scale.polls.2017}} and
{{scale.polls.2022}} orders for 2017 and 2022 compiled by Delemazure, Dong, Peters
and Tydrichová (2024). `data/reference/polling_axes.csv` records the institute,
fieldwork dates, client and source link of each. `notebooks/candidate_scale.ipynb`
turns them into a score from 0 (leftmost) to 1 (rightmost): within each poll the
candidates are evenly spaced, then each candidate's positions are averaged across
institutes. This follows the advice of Magdaléna Tydrichová, and replaced both the
planned Chapel Hill Expert Survey table (it rates parties, not candidacies, and
misses most minor candidates) and our first hand-coded 1–7 scale, which no outside
source checked.

**Bias and coverage.** Within registered voters the results are a census: no
sampling error. The limits are elsewhere. (i) People who are not registered are
outside the frame. (ii) The 2002 and 2007 files omit voters abroad and some
overseas areas ({{areas.2002}} and {{areas.2007}} areas against {{areas.2022}} from
2012), so their totals are not national totals. (iii) The candidate scale is an
order, not a measured distance, and rests on {{scale.polls.2002}} institute for 2002;
section 7 returns to it. The files contain no personal data.

## 3. Cleaning

Official totals leave little to clean and much to verify. The threshold for every
rule is zero violations, and a violation stops the pipeline instead of being
repaired, because with official counts it can only mean that we parsed a file
wrongly. Checks cover schema per file layout (three layouts over twenty years),
unique station and candidate keys, bounds (`voters ≤ registered`,
`valid ≤ voters`), candidate votes equal to valid ballots in every station, and
identical areas in both rounds. {{text.crosscheck}}

We removed, imputed and corrected no observation. Three decisions matter for the
analysis:

- **Derived fields.** Before 2017 only registered voters, voters and valid
  ballots are published; abstention and blank/invalid are derived by exact
  identities and recorded as derived.
- **Blank and invalid ballots.** Before 2017 they are published together. We use
  the combined outcome in every election so the outcome has one definition, and
  keep the separate counts for 2017 and 2022 (null earlier, never zero) for a
  sensitivity analysis.
- **Unusual areas are flagged, not removed.** Overseas areas and voters abroad
  have very different turnout. They are part of the electorate we study.

The poll-based scale has its own checks. Completeness: every candidacy appears in
every poll of its election, and every candidate identifier matches the Ministry
files. Consistency: a candidate is **unplaced** if institutes disagree by more than
0.4 on their position, or if institutes list them last by default (Jacques
Cheminade). {{scale.unplaced}} candidacies are unplaced ({{scale.unplaced_list}});
they are removed from their election's polls, the others are spread again between 0
and 1, and their voters follow the H0b row. After that, the largest disagreement for
a placed candidate is {{scale.max_range_placed|.2f}}. Both rules were fixed before
any model was run on the scale. Accuracy: {{scale.from_reports}} orders come from
the institutes' reports and {{scale.from_paper}} from the published compilation;
each is checked against its source.

## 4. Storage

Raw text is kept unchanged. Cleaned data is stored as **Parquet files in a
normalised layout**: per election an `areas` table (denominator, number of
stations, blank and invalid counts), an `outcomes` table (one count per option)
and an `options` table (labels); and one long `predictions` table for every
model, variant and election. Shares are computed, never stored; the wide table
the app needs is a view built on load. This layout answers the second peer
review, which found a repeated denominator and one result file per model.

We compared this in detail with a relational database (SQLite or PostgreSQL) and
with DuckDB over the same files (`docs/storage_comparison.md`). Our operations
are: write once by one process, read whole columns, join across models and
elections, and be reproduced exactly by a reader with no setup. A database would
add what we lack, **declarative keys and constraints**; we verified that our
tables load into SQLite with primary keys, foreign keys and checks. It would cost
what we value most: files that rebuild byte for byte, can be hashed, and are
small enough to version ({{storage.total_parquet_kb|.0f}} kB in all, against
{{storage.total_csv_kb|.0f}} kB as CSV). PostgreSQL would also add a server for
every reader. DuckDB is not a different store but a query engine over our files;
it becomes useful if the predictions grow well beyond their
{{storage.prediction_rows|,}} rows. **Limits of our choice:** constraints are
enforced by code on every write and load, not by the storage engine; joins live
in Python; and two copies of the snapshots can diverge, which a check detects.
The collected poll orders and the scale built from them stay CSV files: they are
small, edited or regenerated by hand, and reviewed line by line in Git, with their
types and rules enforced on load. The scale keeps every decimal: rounded to three
decimals, a candidate exactly halfway between the finalists (Christine Boutin in
2002) would no longer count as a tie.

## 5. Methodology

**Models.** Each assumption is a transfer matrix: one row per first-round group,
one column per outcome (finalist A, finalist B, blank/invalid, abstention), rows
summing to one. Both finalists' voters, first-round blank/invalid voters and
abstainers keep their position in every model; models differ only in where the
supporters of eliminated candidates go. The rules of H0a, H1 and H2 were fixed
before their results were computed. H0b was added after the second peer review,
that is after the original baseline's failure on abstention was known, so it is a
response to a result and not a pre-specified model. H1-soft was likewise added
after the first results, in response to a later review.

| Model | Eliminated supporters… | Fitted |
|---|---|---|
| H0a | split like the rest of the electorate, abstainers included | no |
| H0b | split between the two finalists and blank/invalid, in proportion to first-round shares; none abstain | no |
| H1 | go to the finalist nearest on the poll-based scale (a tie splits 50/50) | no |
| H1-soft | split between the two finalists, each getting a share inversely proportional to its distance (added after the other results were known) | no |
| H2-abst, H2-blank | as H1, unless at least one third of the scale from both finalists: then abstention, or a blank ballot | no |
| H3 | a share `p` splits as in H0b, the rest follows H1 or H2 | `p` |

Unplaced candidates use the H0b row. The H2 threshold of one third is the rule
written before any result, two steps out of six on the 1–7 scale, carried over
unchanged. We report both H2 variants and do not
choose between them by fit. We use simple, parameter-free rules first because the
question is about assumptions that can be stated in one sentence; H3 is the only
fitted model, with one parameter.

**Evaluation.** The primary score is, per area, the mean absolute error over the
four outcomes in percentage points (pp), averaged with round-two registered
voters as weights. Errors are taken before pooling, so opposite errors in two
areas cannot cancel. The signed error per outcome after pooling is a secondary
diagnostic.

**Validation of H3.** Leave-one-election-out: `p` is fitted by grid search (step
0.01) on four elections and scored on the fifth, for each election in turn. Areas
of one election are never split between training and test. Only held-out scores
are reported. With five elections this describes how a rule transfers; it
supports no significance claim.

## 6. Results

![Model comparison](../../reports/figures/model_comparison.png)

*Figure 1. Primary score (pp) per model and election; lower is closer to the
observed result. H3 is held-out.*

**Observations.**

1. **The original baseline fails on abstention.** H0a over-predicts abstention in
   {{signed_positive_elections.H0a.abstention}} of {{n.elections}} elections, by
   {{signed_min.H0a.abstention}} to {{signed_max.H0a.abstention}} pp (Figure 2). H0b,
   which removes that one channel, scores lower in {{wins.H0b.vs_H0a}} of
   {{n.elections}} elections (mean {{score.H0b.mean}} against {{score.H0a.mean}} pp).
2. **The lowest five-election mean is {{best.model}}** ({{best.mean}} pp), ahead of
   H0b ({{score.H0b.mean}} pp). But {{best.model}} beats H0b in only
   {{wins.H1.vs_H0b}} of {{n.elections}} elections, and most of its lead comes from
   2002, where it scores {{score.H1.2002}} pp against {{score.H0b.2002}}.
3. **Splitting by distance trades 2002 for the other elections.** H1-soft averages
   {{score.H1-soft.mean}} pp (rank {{rank.H1-soft}}) and {{score.H1-soft.mean_without_2002}} pp
   without 2002. It is closer than H1 outside 2002 (for example {{score.H1-soft.2012}}
   against {{score.H1.2012}} pp in 2012) but much worse in 2002 ({{score.H1-soft.2002}}
   against {{score.H1.2002}}): on an evenly spaced scale Chirac and Le Pen are almost as
   far from Jospin, so a large share of the left goes to Le Pen.
4. **Without 2002 the order changes** (a post-hoc check: we set 2002 aside after
   seeing that {{best.model}} beats H0b mainly there). {{best.model}} falls to rank
   {{best.rank_without_2002}} of {{n.models}} ({{best.mean_without_2002}} pp); H0b is at
   {{score.H0b.mean_without_2002}} pp and the lowest mean is
   {{best_without_2002.model}} ({{best_without_2002.mean_without_2002|.2f}} pp), followed
   by the H3 mixtures on the H2 bases ({{score.H3(H2-abst).mean_without_2002|.2f}} and
   {{score.H3(H2-blank).mean_without_2002|.2f}} pp), which are almost entirely H0b.
5. **The distance threshold fails in one election.** H2-abst and H2-blank have
   means of {{score.H2-abst.mean}} and {{score.H2-blank.mean}} pp and beat H0b in
   {{wins.H2-abst.vs_H0b}} and {{wins.H2-blank.vs_H0b}} of {{n.elections}} elections.
   The damage is in 2002: both finalists sit on the right of the scale
   ({{h2.2002.finalist_a_score|.2f}} and {{h2.2002.finalist_b_score|.2f}}), so the whole left
   is at least one third away from both and H2 sends {{h2.2002.beyond_pct}}% of
   registered voters to a non-vote; H2-abst then scores {{score.H2-abst.2002}} pp.
   In the other elections the rule removes little ({{h2.2007.beyond_pct}}% in 2007,
   {{h2.2012.beyond_pct}}% in 2012, {{h2.2017.beyond_pct}}% in 2017 and
   {{h2.2022.beyond_pct}}% in 2022), and H2 scores close to H1. So in practice the
   threshold is tested in one election only, and we do not claim that it helps.
6. **H3 adds little.** On the H2 bases the fitted `p` is between
   {{p.H2-blank.min|.2f}} and {{p.H2-abst.max|.2f}}: the fit almost discards the H2
   rule. On H1, `p` is between {{p.H1.min|.2f}} and {{p.H1.2017|.2f}} in four folds and
   {{p.H1.2002|.2f}} when 2002 is held out. Held-out H3(H1) is worse than H1 over five
   elections ({{score.H3(H1).mean}} against {{score.H1.mean}} pp) but better without
   2002 ({{score.H3(H1).mean_without_2002}} against {{score.H1.mean_without_2002}} pp).
7. **Blank and invalid ballots are under-predicted** in 2017 and 2022 by every
   model, H2-blank included ({{signed.H2-blank.2017.blank_invalid|+.1f}} and
   {{signed.H2-blank.2022.blank_invalid|+.1f}} pp).
   Invalid ballots are {{blank.2017.invalid_share_of_combined|.0f}}% of the category
   in 2017 and {{blank.2022.invalid_share_of_combined|.0f}}% in 2022; their error is the
   same for every model ({{blank.2017.signed_invalid|+.1f}} and
   {{blank.2022.signed_invalid|+.1f}} pp).

![Signed error by outcome](../../reports/figures/signed_error_by_outcome.png)

*Figure 2. Predicted minus observed share of registered voters, pooled over
covered areas, for both baselines and {{best.model}}.*

**Sensitivity.** We rerun every model with the hand-coded 1–7 scale (put on 0–1,
so the threshold is unchanged) and with its alternative families. With the 1–7
scale, {{sens.primary.split.best.model}} still has the lowest mean (H1 moves by
{{sens.primary.split.change.H1.mean|+.2f}} pp) and H0b still ranks
{{sens.primary.split.rank.H0b}}, but H2 is much worse
({{sens.primary.split.change.H2-abst.mean|+.1f}} pp for H2-abst): the hand-coded
scale put the left of 2017 and 2022 two steps from the centrist finalist, so H2
sent it to a non-vote. With the alternative families the lowest mean becomes
{{sens.alternative.split.best.model}}. The conclusion that matters holds on both scales:
H1 leads over five elections because of 2002, and without 2002 the lead goes to H0b
or to an H3 mixture that is almost H0b
({{sens.primary.split.best_without_2002.model}} on the 1–7 scale). The tie rule
matters little: {{ties.polls.count}} candidates are exactly halfway between the
finalists on the poll-based scale ({{ties.polls.elections}}), and sending them to
abstention instead of splitting them moves no mean by more than
{{sens.polls.abstention.max_abs_change|.2f}} pp. With blank ballots scored alone, the order of models
{{blank.2017.text.same_ranking}} in 2017 and {{blank.2022.text.same_ranking}} in 2022.

![Predicted against observed, 2022](../../reports/figures/predicted_vs_observed_2022.png)

*Figure 3. {{best.model}} against observed shares by area, 2022. Overseas areas
(Z-codes) and voters abroad (ZZ) are highlighted.*

In 2022, {{best.model}} scores {{territory.metropolitan.H1.2022}} pp in metropolitan
areas and {{territory.overseas.H1.2022}} pp overseas, where H0b scores
{{territory.overseas.H0b.2022}} pp.

**Interpretation.** These readings go beyond the numbers and carry the caveats of
section 7. First, most of the original baseline's error came from one modelling
choice, not from voters behaving unpredictably; the baseline to beat is H0b.
Second, **we cannot name one best assumption.** Ideological proximity describes
2002 far better than anything else, plausibly because that runoff opposed the
right and the far right and almost every other voter ended on the same side. In
the four other elections, "people who voted once vote again, in proportion to the
finalists' first-round strength" does as well or better. Five elections cannot
separate a general rule from one exceptional election. Third, H2's failure is
concentrated in 2002, the one runoff between the right and the far right: a
"too far from both, so stay home" rule predicts that the left abstains, while it
voted for Chirac. How much H2 fails also depends on where the candidates are
placed, since a threshold decides between all and none. The threshold was fixed before any result was seen and we add no
other, since choosing one now would be tuning on the evaluation elections. Fourth, a left–right scale built from national polls may
describe overseas electorates poorly; this is a hypothesis.

## 7. Limitations

- **Aggregate inference.** Many different individual behaviours give the same
  area totals. A matrix that fits is not an observed transfer.
- **An order, not a distance.** Within a poll, neighbouring candidates are
  always the same distance apart, whatever their real ideological gap. Institutes'
  table conventions also enter the scale: in 2007 they list the PS before the
  Greens, so Dominique Voynet sits slightly right of Ségolène Royal.
- **Few sources for 2002.** We found the original report of {{scale.polls.2002}}
  institute only; {{scale.from_paper}} of the {{scale.polls}} orders come from a
  published compilation, not the institutes' own reports.
- **Comparison scale.** The hand-coded 1–7 scale used as a comparison is a draft
  that two coders did not review ({{quality.draft_rows}} draft rows).
- **One dimension.** The scale ignores other dimensions (Europe, sovereignty,
  ecology).
- **Coverage.** 2002 and 2007 describe covered areas only; years are not
  identical geographic samples.
- **Combined blank/invalid.** The primary outcome mixes a deliberate act with
  mistakes; the separate analysis exists for two elections only.
- **Retained groups never move.** In every model, finalists' voters and first-round
  blank and abstaining voters keep their position, and errors are shares of
  registered voters averaged over four outcomes. Any real movement of retained
  groups is an error floor shared by all models, which compresses the differences
  between them; scores are not comparable with studies that use valid votes.
- **Few elections and model selection.** Eight models compared on five elections:
  the "best" is partly a selection effect. We dropped the planned H4 and H5 and
  two-dimensional distances, which needed data we could not justify.

## 8. Reproducibility and response to feedback

```bash
uv sync --locked --dev      # environment from the lock file
make data                   # acquire, process, scale, evaluate, bundle (all five elections)
make analysis               # the candidate scale, every model result, figure, table and number
make check                  # tests, lint, and processed-versus-bundled comparison
```

A clone already contains verified snapshots, so `make analysis` and the app run
offline. Every number in this report is read from `reports/results/numbers.json`;
the report is rendered from a template, so it cannot drift from the results. Raw
files are pinned by hash. What a command cannot reproduce is the extraction of the
poll orders from the institutes' reports, which is why each row of
`polling_axes.csv` links to its source; a test fails if the scale is not rebuilt
after the polls change.

**What changed after peer feedback** (`docs/response_to_reviews.md` lists every
comment). After the first review we dropped H4, H5 and all auxiliary datasets.
After the second we (i) added the second baseline H0b, which turned out to matter
more than any other change; (ii) replaced the unreviewed hand-coded candidate
table with positions built from polling institutes, as the reviewers' concern about
its accuracy and Magdaléna Tydrichová's advice suggested, and assessed it; (iii) normalised the storage and
moved to one predictions table; (iv) kept blank and invalid counts separately;
(v) fixed the reproduction commands; and (vi) produced the cross-election
figures the reviewers asked for.

AI assistance was used for code, tests and drafting. The team owns the
methodological decisions and the interpretation.
