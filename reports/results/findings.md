<!-- Generated from docs/templates/findings.md by `vote-transfer analyse`. Edit the template, not this file. -->

# Findings

Status of the candidate table: **poll-based scale**. Every result for H1, H2 and
H3 depends on it and will change when the two-coder review is merged.
`[PENDING: coder agreement]`

All numbers below are read from `reports/results/numbers.json`, written by
`vote-transfer analyse`. Scores are the primary score in percentage points (pp):
the mean absolute error over the four outcomes in each area, weighted by
round-two registered voters. Lower is closer to the observed result. H3 scores
are held-out (leave-one-election-out).

## Observations

What the numbers show. No explanation is offered in this section.

### 1. Model comparison (`model_comparison.csv`, figure `model_comparison`)

| Model | 2002 | 2007 | 2012 | 2017 | 2022 | Mean | Mean without 2002 |
|---|---:|---:|---:|---:|---:|---:|---:|
| H0a | 19.0 | 4.3 | 5.6 | 8.6 | 6.1 | 8.7 | 6.2 |
| H0b | 13.5 | 1.5 | 1.4 | 6.1 | 3.0 | 5.1 | 3.0 |
| H1 | 4.4 | 5.0 | 4.1 | 5.8 | 4.4 | 4.7 | 4.8 |
| H2-abst | 19.4 | 5.5 | 4.2 | 5.2 | 3.7 | 7.6 | 4.7 |
| H2-blank | 18.4 | 5.0 | 4.1 | 5.2 | 3.1 | 7.2 | 4.3 |
| H3(H1) | 11.7 | 4.5 | 3.5 | 4.8 | 3.7 | 5.6 | 4.1 |
| H3(H2-abst) | 14.4 | 1.9 | 1.4 | 6.1 | 3.0 | 5.4 | 3.1 |
| H3(H2-blank) | 14.6 | 2.0 | 1.5 | 6.1 | 3.0 | 5.4 | 3.2 |

- Order by mean score over the five elections, best first: **H1 < H0b < H3(H2-abst) < H3(H2-blank) < H3(H1) < H2-blank < H2-abst < H0a**.
- The lowest mean is **H1** (4.74 pp).
- H0b is below H0a in 5 of 5 elections; its mean is
  -3.63 pp relative to H0a.
- H1 is below H0b in 2 of 5 elections and below H0a in
  4.
- H2-abst is below H0a in 3 of 5 elections and
  H2-blank in 4. Neither is below H0b in more than
  1 election(s) (H2-abst: 1).

### 2. 2002 with and without

- 2002 has the largest score of every model except H1: H0a 19.0,
  H0b 13.5, H1 4.4 pp.
- In 2002 abstention fell between rounds. H0a predicts 49.7%
  abstention against 19.7% observed; H0b and H1 predict
  27.9%.
- Order by mean score **without 2002**: **H0b < H3(H2-abst) < H3(H2-blank) < H3(H1) < H2-blank < H2-abst < H1 < H0a**.
- Without 2002, H1 is no longer first: it ranks
  7 of 8 (4.82 pp), and the
  lowest mean is H0b (3.01 pp).
  H0b is at 3.01 pp.
- Among the parameter-free models, the lowest mean is
  H1 with 2002 and
  H0b without it.

### 3. Signed errors by outcome (`signed_errors.csv`, figure `signed_error_by_outcome`)

Signed error = predicted minus observed share of registered voters, pooled over
covered areas.

- **H0a over-predicts abstention in 5 of
  5 elections**, by 8.6 to
  30.0 pp.
- H0b's abstention error lies between -3.2 and
  +8.2 pp. The same holds for H1, which shares H0b's
  abstention prediction by construction.
- Every model in the main set under-predicts blank/invalid in 2017 and 2022 except
  H2-blank (H0b: -4.3 and
  -3.1 pp; H2-blank:
  -5.2 and -2.0 pp).
- In 2017, H0b and H1 over-predict finalist B (Le Pen) by
  +11.7 and -1.5 pp.
- In 2022, H1 over-predicts finalist A (Macron) by
  +8.0 pp; H0b over-predicts finalist B by
  +4.3 pp.
- H2-abst over-predicts abstention by -1.9 pp in 2017
  and +0.9 pp in 2022.

### 4. H3: fitted share `p` per fold (`h3_folds.csv`)

| Base | Test 2002 | Test 2007 | Test 2012 | Test 2017 | Test 2022 | All five (scenario page only) |
|---|---:|---:|---:|---:|---:|---:|
| H1 | 0.83 | 0.15 | 0.19 | 0.34 | 0.21 | 0.44 |
| H2-abst | 0.80 | 0.86 | 0.98 | 1.00 | 1.00 | 1.00 |
| H2-blank | 0.77 | 0.81 | 0.95 | 1.00 | 1.00 | 0.98 |

- `p` is the share of each eliminated group that splits as in H0b instead of
  following the base rule. `p = 1` is H0b.
- On the H2 bases the fitted `p` is between 0.77 and
  1.00 in every fold.
- On H1, `p` is between 0.15 and 0.34 in four folds and
  0.83 in the fold that tests on 2002 (that is, when 2002 is not in the
  training data).
- Held-out, H3(H1) has a higher mean score than H1 itself
  (5.63 against 4.74 pp); the difference comes
  from 2002 (11.7 against 4.4 pp).

### 5. Sensitivity (`sensitivity.csv`, `tied_groups.csv`, `blank_only.csv`)

**Coding.** With `alternative_family` on the 41 rows that
list one:

- order by mean: H3(H2-blank) < H1 < H0b < H3(H2-abst) < H3(H1) < H0a < H2-blank < H2-abst;
- the ranking changes; the lowest mean belongs
  to a different model (H3(H2-blank));
- H1's mean moves by +0.27 pp, H2-abst by
  +2.99 pp, H2-blank by
  +2.19 pp;
- H2-abst and H2-blank rank 8 and
  7 of 8 under the alternative coding,
  against 7 and 6 under the primary coding;
- H0b and H0a rank 3 and
  6 under the alternative coding, against
  2 and 8.

**Ties.** Number of eliminated candidates equidistant from both finalists:
0 under the primary coding and 0 under
the alternative coding. The largest change in any model's mean score between
`tie=split` and `tie=abstention` is 2.85 pp.

**Blank ballots alone (2017 and 2022).** With blank and invalid ballots scored as
separate outcomes (first-round invalid ballots kept as invalid, every modelled
inflow counted as blank):

- invalid ballots are 26% of the combined
  second-round category in 2017 and 26% in 2022;
- every model under-predicts invalid ballots by the same amount:
  -1.6 pp in 2017 and -1.1 pp
  in 2022;
- on blank ballots alone, H2-blank's error is -3.6 pp
  (2017) and -0.9 pp (2022); H0b's is
  -2.7 and -1.9 pp;
- the order of models is unchanged in 2017 and
  is unchanged in 2022 when the five-outcome score replaces the
  four-outcome score.

### 6. Territories, 2022 (`territory_scores.csv`, figure `predicted_vs_observed_2022`)

| Model | Metropolitan (96 areas) | Overseas (10) | Abroad (1) |
|---|---:|---:|---:|
| H0a | 5.8 | 11.3 | 8.5 |
| H0b | 3.0 | 3.3 | 1.7 |
| H1 | 4.3 | 8.1 | 2.0 |

### 7. Candidate table (`candidate_table_quality.json`)

- 61 rows; 59 draft, 0 reviewed,
  2 without a score (2012 and 2017 and 2017; H0b row used).
- Consistency: of 33 party labels, those coded with more than
  one family across elections are PS, UDF.
- Accuracy (two-coder agreement): pending: two-coder review not done.
  `[PENDING: coder agreement]`

### 8. What the H2 threshold removes (`h2_threshold.csv`)

Shares are first-round shares of registered voters, all covered areas pooled,
under the primary coding. H2 sends these groups to abstention (H2-abst) or to a
blank ballot (H2-blank) in full.

| Election | Finalist scores (A, B) | Eliminated supporters at least 0.3 steps from both finalists | …of which exactly 0.3 steps away (scores) |
|---|---|---:|---:|
| 2002 | 0.8, 0.9 | 29.9% | 3.7% (0.467) |
| 2007 | 0.8, 0.5 | 1.4% | 0.0% (none) |
| 2012 | 0.4, 0.8 | 0.4% | 0.0% (none) |
| 2017 | 0.5, 0.9 | 1.3% | 0.0% (none) |
| 2022 | 0.5, 0.9 | 2.6% | 0.0% (none) |

- In 2017 and 2022 the finalists are coded 0.5 and
  0.9. A group coded none is exactly 0.3 steps
  from the nearer finalist, so the rule "at least 0.3 steps from both"
  applies to it: 0.0% of registered voters in 2017 and
  0.0% in 2022 sit exactly on the threshold.
- In 2002 the finalists are coded 0.8 and
  0.9, and 29.9% of registered voters are in
  groups beyond the threshold.
- In 2007 and 2012 the corresponding shares are 1.4% and
  0.4%.
- H2-abst and H2-blank score 5.5 and 5.0 pp in
  2007 and 4.2 and 4.1 pp in 2012, against
  5.2 and 5.2 pp in 2017.

## Interpretations

What the observations may mean. Each point is a reading of aggregate patterns
under a draft coding, not a statement about how individuals voted.

1. **The original baseline was weak for one identifiable reason.** H0a sends part
   of every eliminated group to abstention, and it over-predicts abstention in
   every election. Removing that single channel (H0b) lowers the error in every
   election. This answers the reviewers' question: most of H0a's error came from
   that choice, so H0b is the baseline later models should be judged against.

2. **There is no stable winner; the answer depends on 2002.** H1 has the
   lowest five-election mean, but it is no longer first once 2002 is set
   aside, where H0b and the H3 mixtures that collapse onto it do at least as well.
   One reading: ideological proximity describes 2002 well because that runoff
   opposed a right and a far-right candidate and nearly all other voters ended on
   one side, while in the other four elections a proportional split among people
   who vote again is as good or better. With five elections we cannot tell a rule
   from a single-election effect. **The evidence does not support naming one
   assumption as the best explanation.**

3. **A fixed threshold on a coarse ordinal scale is fragile: this is a finding
   about thresholds, not about voters.** H2 fits badly where the threshold removes
   a large group in one piece, and the mechanism is arithmetic (observation 8).
   With finalists at 0.5 and 0.9,
   every group coded none is exactly 0.3 steps
   from the nearer finalist, so the "at least 0.3 steps" rule sends the
   whole left to a non-vote; on a seven-point scale one step is the difference
   between "all of them vote for the nearer finalist" and "none of them do". Where
   few voters are beyond the threshold (2007, 2012), H2 stays close to H1
   (4.2 against 4.1 pp in 2012). H3 agrees:
   allowed to ignore the H2 rule for a share `p`, the fit puts nearly everyone in
   that share. The threshold and the equal spacing of the scale were fixed before
   any result was computed and were not changed afterwards. We add no variant with
   another threshold: choosing one after seeing these scores would be tuning on
   the evaluation elections.

4. **H3 adds little here.** It is at best equal to the better of its two
   ingredients, and for H1 the fitted share is unstable because one election
   (2002) pulls it. This is a useful negative result: one fitted parameter is
   already more than five elections can pin down.

5. **Blank and invalid ballots.** All models but H2-blank under-predict the rise
   of blank/invalid ballots in 2017 and 2022, and H2-blank over-predicts it by
   far more. About a quarter of the combined category is invalid ballots, whose
   rise no rule here addresses. A model for the rise of blank voting is still
   missing; we do not claim one.

6. **Overseas areas fit worse under H1 than under H0b in 2022.** Their
   first-round patterns differ from metropolitan areas (the scatter shows H1
   placing too much on finalist A and too little on finalist B there). A
   left–right scale coded for national politics may describe these electorates
   poorly. This is a hypothesis, not a finding.

7. **The coding matters.** Under the alternative coding the order of models
   changes. Conclusions that depend on the
   position of H1 relative to H0b should be treated as provisional until the
   two-coder review is done. The tie rule, in contrast, is irrelevant in practice:
   no tie occurs under either coding.

## Caveats that apply to everything above

- Aggregate (ecological) inference: many different individual behaviours produce
  the same area totals. A matrix that fits is not an observed transfer.
- 2002 and 2007 cover fewer areas (100 and 101 against
  107); scores describe covered areas only.
- Naming a "best" model after comparing eight on the same five elections is
  itself a selection; no significance is claimed.
- The scale is one-dimensional and assumed equally spaced.
- The alternative coding moves all 41 listed rows at once,
  finalists included. It is a single alternative scenario, not a per-candidate
  sensitivity analysis.
- H3 is reported pending approval of its fitted parameter.
  `[PENDING: professor approval]`
