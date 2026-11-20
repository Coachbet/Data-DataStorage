<!-- Generated from docs/templates/findings.md by `vote-transfer analyse`. Edit the template, not this file. -->

# Findings

Candidate positions: **poll-based scale**. H1, H2 and H3 place candidates with
the left-to-right orders of 22 polls by 9 polling
institutes (`data/reference/polling_axes.csv`, built into
`data/reference/candidate_scores.csv` by `notebooks/candidate_scale.ipynb`). The
hand-coded 1–7 scale is kept as a comparison (draft coding).

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
- Every model in the main set under-predicts blank/invalid in 2017 and 2022,
  H2-blank included (H0b: -4.3 and
  -3.1 pp; H2-blank:
  -5.2 and -2.0 pp).
- Error on finalist B (Le Pen) in 2017: H0b +11.7 pp,
  H1 -1.5 pp.
- Error on finalist A (Macron) in 2022: H1 +8.0 pp;
  error on finalist B: H0b +4.3 pp.
- H2-abst's error on abstention is -1.9 pp in 2017
  and +0.9 pp in 2022, against
  +38.1 pp in 2002.

### 4. H3: fitted share `p` per fold (`h3_folds.csv`)

| Base | Test 2002 | Test 2007 | Test 2012 | Test 2017 | Test 2022 | Fitted on all five (description only) |
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

**Candidate positions.** Every model is rerun on the hand-coded 1–7 scale (put on
0–1, same threshold) and on its alternative families. Changes are relative to the
main, poll-based results.

- Hand-coded 1–7 scale: order by mean H1 < H0b < H3(H2-abst) < H3(H2-blank) < H3(H1) < H0a < H2-blank < H2-abst; the ranking
  changes and the lowest mean belongs to
  the same model (H1). H1's mean
  moves by -0.39 pp, H2-abst by
  +2.85 pp, H2-blank by
  +2.23 pp. Without 2002 the lowest mean is
  H3(H2-blank).
- Alternative families (41 rows that list one): order by
  mean H3(H2-blank) < H1 < H0b < H3(H2-abst) < H3(H1) < H0a < H2-blank < H2-abst; the lowest mean belongs to
  a different model (H3(H2-blank)).
  H1's mean moves by +0.27 pp, H2-abst by
  +2.99 pp.
- H2-abst and H2-blank rank 8 and
  7 of 8 on the 1–7 scale, against
  7 and 6 on the poll-based scale. H0b ranks
  2 on the poll-based scale, 2 on the 1–7 scale
  and 3 under the alternative families.

**Ties.** On the poll-based scale, 2 eliminated candidates are
exactly equidistant from both finalists (2002, 2007); on the 1–7 scale
0, and 0 under the alternative families.
Sending tied groups to abstention instead of splitting them changes no model's mean
by more than 0.10 pp.

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

### 7. Candidate positions (`candidate_scores.csv`, `candidate_table_quality.json`)

- Poll-based scale: 22 polls (1 in 2002,
  3 in 2007, 3 in 2012, 7 in
  2017, 8 in 2022); 7 taken from the institutes'
  reports and 15 from the compilation by Delemazure, Dong, Peters
  and Tydrichová (2024). `[PENDING: poll orders checked against sources]`
- 3 candidacies unplaced (Cheminade 2012, Cheminade 2017, Lassalle 2017; H0b row used).
  Largest disagreement between institutes for a placed candidate:
  0.36 (unplaced above 0.4).
- Comparison scale (hand-coded 1–7): 61 rows; 59
  draft, 0 reviewed, 2 without a score.
  Party labels coded with more than one family across elections:
  PS, UDF.

### 8. What the H2 threshold removes (`h2_threshold.csv`)

Shares are first-round shares of registered voters, all covered areas pooled,
on the poll-based scale (0 = left, 1 = right). H2 sends these groups to abstention (H2-abst) or to a
blank ballot (H2-blank) in full.

| Election | Finalist scores (A, B) | Eliminated supporters at least one third of the scale from both finalists | …of which exactly one third away (scores) |
|---|---|---:|---:|
| 2002 | 0.8, 0.9 | 29.9% | 3.7% (0.467) |
| 2007 | 0.8, 0.5 | 1.4% | 0.0% (none) |
| 2012 | 0.4, 0.8 | 0.4% | 0.0% (none) |
| 2017 | 0.5, 0.9 | 1.3% | 0.0% (none) |
| 2022 | 0.5, 0.9 | 2.6% | 0.0% (none) |

- In 2002 both finalists are on the right of the scale
  (0.80 and 0.93), and
  29.9% of registered voters are in groups at least one third away
  from both, the whole left among them. 3.7% sit exactly on
  the threshold (Noël Mamère, 0.467).
- In the other elections the threshold removes little: 1.4% in
  2007, 0.4% in 2012, 1.3% in 2017 and
  2.6% in 2022.
- H2-abst and H2-blank score 5.5 and 5.0 pp in
  2007 and 4.2 and 4.1 pp in 2012, against
  5.2 and 5.2 pp in 2017.

## Interpretations

What the observations may mean. Each point is a reading of aggregate patterns
on the poll-based scale, not a statement about how individuals voted.

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

3. **"Too far from both, so stay home" fails in the one election where it bites.**
   H2 fits badly where the threshold removes a large group in one piece
   (observation 8). In 2002 both finalists were on the right, so the rule sends the
   whole left to a non-vote, while the left voted for Chirac against Le Pen:
   H2-abst scores 19.4 pp against 4.4 for H1. Where few
   voters are beyond the threshold, H2 stays close to H1
   (4.2 against 4.1 pp in 2012). The size of the
   failure also depends on where candidates are placed: on the hand-coded 1–7 scale,
   the left of 2017 and 2022 sat exactly on the threshold and H2 was much worse
   (+2.9 pp on average). H3 agrees:
   allowed to ignore the H2 rule for a share `p`, the fit puts nearly everyone in
   that share. The threshold (one third, the original two steps out of six) and the
   equal spacing were fixed before any result was computed and not changed
   afterwards. We add no variant with
   another threshold: choosing one after seeing these scores would be tuning on
   the evaluation elections.

4. **H3 adds little here.** It is at best equal to the better of its two
   ingredients, and for H1 the fitted share is unstable because one election
   (2002) pulls it. This is a useful negative result: one fitted parameter is
   already more than five elections can pin down.

5. **Blank and invalid ballots.** Every model, H2-blank included, under-predicts
   the rise of blank/invalid ballots in 2017 and 2022. About a quarter of the combined category is invalid ballots, whose
   rise no rule here addresses. A model for the rise of blank voting is still
   missing; we do not claim one.

6. **Overseas areas fit worse under H1 than under H0b in 2022.** Their
   first-round patterns differ from metropolitan areas (the scatter shows H1
   placing too much on finalist A and too little on finalist B there). A
   left–right scale built from national polls may describe these electorates
   poorly. This is a hypothesis, not a finding.

7. **The placement of candidates matters for H2, less for the main conclusion.**
   On the hand-coded 1–7 scale the order of models
   changes (H2 falls), and under its alternative
   families it changes again; but on every scale
   H1 leads over five elections only because of 2002, and H0b or an H3 mixture close
   to it leads without 2002. The tie rule matters little: 2
   candidates sit exactly halfway between the finalists (2002, 2007),
   and the abstention tie rule moves no mean by more than
   0.10 pp.

## Caveats that apply to everything above

- Aggregate (ecological) inference: many different individual behaviours produce
  the same area totals. A matrix that fits is not an observed transfer.
- 2002 and 2007 cover fewer areas (100 and 101 against
  107); scores describe covered areas only.
- Naming a "best" model after comparing eight on the same five elections is
  itself a selection; no significance is claimed.
- The scale is one-dimensional and is an order: within a poll, candidates are
  equally spaced whatever their real ideological gap.
- 2002 rests on one institute (1 poll), and
  15 of 22 orders come from a published compilation.
- The comparison 1–7 scale is an unreviewed draft; its alternative coding moves all
  41 listed rows at once.
- H3 is reported pending approval of its fitted parameter.
  `[PENDING: professor approval]`
