# Findings

Candidate positions: **{{coding_status}}**. H1, H2 and H3 place candidates with
the left-to-right orders of {{scale.polls}} polls by {{scale.institutes}} polling
institutes (`data/reference/polling_axes.csv`, built into
`data/reference/candidate_scores.csv` by `notebooks/candidate_scale.ipynb`). The
hand-coded 1–7 scale is kept as a comparison ({{comparison_coding_status}}).

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
| H0a | {{score.H0a.2002}} | {{score.H0a.2007}} | {{score.H0a.2012}} | {{score.H0a.2017}} | {{score.H0a.2022}} | {{score.H0a.mean}} | {{score.H0a.mean_without_2002}} |
| H0b | {{score.H0b.2002}} | {{score.H0b.2007}} | {{score.H0b.2012}} | {{score.H0b.2017}} | {{score.H0b.2022}} | {{score.H0b.mean}} | {{score.H0b.mean_without_2002}} |
| H1 | {{score.H1.2002}} | {{score.H1.2007}} | {{score.H1.2012}} | {{score.H1.2017}} | {{score.H1.2022}} | {{score.H1.mean}} | {{score.H1.mean_without_2002}} |
| H2-abst | {{score.H2-abst.2002}} | {{score.H2-abst.2007}} | {{score.H2-abst.2012}} | {{score.H2-abst.2017}} | {{score.H2-abst.2022}} | {{score.H2-abst.mean}} | {{score.H2-abst.mean_without_2002}} |
| H2-blank | {{score.H2-blank.2002}} | {{score.H2-blank.2007}} | {{score.H2-blank.2012}} | {{score.H2-blank.2017}} | {{score.H2-blank.2022}} | {{score.H2-blank.mean}} | {{score.H2-blank.mean_without_2002}} |
| H3(H1) | {{score.H3(H1).2002}} | {{score.H3(H1).2007}} | {{score.H3(H1).2012}} | {{score.H3(H1).2017}} | {{score.H3(H1).2022}} | {{score.H3(H1).mean}} | {{score.H3(H1).mean_without_2002}} |
| H3(H2-abst) | {{score.H3(H2-abst).2002}} | {{score.H3(H2-abst).2007}} | {{score.H3(H2-abst).2012}} | {{score.H3(H2-abst).2017}} | {{score.H3(H2-abst).2022}} | {{score.H3(H2-abst).mean}} | {{score.H3(H2-abst).mean_without_2002}} |
| H3(H2-blank) | {{score.H3(H2-blank).2002}} | {{score.H3(H2-blank).2007}} | {{score.H3(H2-blank).2012}} | {{score.H3(H2-blank).2017}} | {{score.H3(H2-blank).2022}} | {{score.H3(H2-blank).mean}} | {{score.H3(H2-blank).mean_without_2002}} |

- Order by mean score over the five elections, best first: **{{ranking.all}}**.
- The lowest mean is **{{best.model}}** ({{best.mean|.2f}} pp).
- H0b is below H0a in {{wins.H0b.vs_H0a}} of {{n.elections}} elections; its mean is
  {{delta.H0b.vs_H0a.mean|+.2f}} pp relative to H0a.
- H1 is below H0b in {{wins.H1.vs_H0b}} of {{n.elections}} elections and below H0a in
  {{wins.H1.vs_H0a}}.
- H2-abst is below H0a in {{wins.H2-abst.vs_H0a}} of {{n.elections}} elections and
  H2-blank in {{wins.H2-blank.vs_H0a}}. Neither is below H0b in more than
  {{wins.H2-blank.vs_H0b}} election(s) (H2-abst: {{wins.H2-abst.vs_H0b}}).

### 2. 2002 with and without

- 2002 has the largest score of every model except H1: H0a {{score.H0a.2002}},
  H0b {{score.H0b.2002}}, H1 {{score.H1.2002}} pp.
- In 2002 abstention fell between rounds. H0a predicts {{predicted.H0a.2002.abstention}}%
  abstention against {{actual.2002.abstention}}% observed; H0b and H1 predict
  {{predicted.H0b.2002.abstention}}%.
- Order by mean score **without 2002**: **{{ranking.without_2002}}**.
- Without 2002, {{best.model}} {{text.best_without_2002}}: it ranks
  {{best.rank_without_2002}} of {{n.models}} ({{best.mean_without_2002|.2f}} pp), and the
  lowest mean is {{best_without_2002.model}} ({{best_without_2002.mean_without_2002|.2f}} pp).
  H0b is at {{score.H0b.mean_without_2002|.2f}} pp.
- Among the parameter-free models, the lowest mean is
  {{best_parameter_free.model}} with 2002 and
  {{best_parameter_free_without_2002.model}} without it.

### 3. Signed errors by outcome (`signed_errors.csv`, figure `signed_error_by_outcome`)

Signed error = predicted minus observed share of registered voters, pooled over
covered areas.

- **H0a over-predicts abstention in {{signed_positive_elections.H0a.abstention}} of
  {{n.elections}} elections**, by {{signed_min.H0a.abstention}} to
  {{signed_max.H0a.abstention}} pp.
- H0b's abstention error lies between {{signed_min.H0b.abstention|+.1f}} and
  {{signed_max.H0b.abstention|+.1f}} pp. The same holds for H1, which shares H0b's
  abstention prediction by construction.
- Every model in the main set under-predicts blank/invalid in 2017 and 2022,
  H2-blank included (H0b: {{signed.H0b.2017.blank_invalid|+.1f}} and
  {{signed.H0b.2022.blank_invalid|+.1f}} pp; H2-blank:
  {{signed.H2-blank.2017.blank_invalid|+.1f}} and {{signed.H2-blank.2022.blank_invalid|+.1f}} pp).
- Error on finalist B ({{finalist_b.2017}}) in 2017: H0b {{signed.H0b.2017.finalist_b|+.1f}} pp,
  H1 {{signed.H1.2017.finalist_b|+.1f}} pp.
- Error on finalist A ({{finalist_a.2022}}) in 2022: H1 {{signed.H1.2022.finalist_a|+.1f}} pp;
  error on finalist B: H0b {{signed.H0b.2022.finalist_b|+.1f}} pp.
- H2-abst's error on abstention is {{signed.H2-abst.2017.abstention|+.1f}} pp in 2017
  and {{signed.H2-abst.2022.abstention|+.1f}} pp in 2022, against
  {{signed.H2-abst.2002.abstention|+.1f}} pp in 2002.

### 4. H3: fitted share `p` per fold (`h3_folds.csv`)

| Base | Test 2002 | Test 2007 | Test 2012 | Test 2017 | Test 2022 | Fitted on all five (description only) |
|---|---:|---:|---:|---:|---:|---:|
| H1 | {{p.H1.2002|.2f}} | {{p.H1.2007|.2f}} | {{p.H1.2012|.2f}} | {{p.H1.2017|.2f}} | {{p.H1.2022|.2f}} | {{p.H1.all|.2f}} |
| H2-abst | {{p.H2-abst.2002|.2f}} | {{p.H2-abst.2007|.2f}} | {{p.H2-abst.2012|.2f}} | {{p.H2-abst.2017|.2f}} | {{p.H2-abst.2022|.2f}} | {{p.H2-abst.all|.2f}} |
| H2-blank | {{p.H2-blank.2002|.2f}} | {{p.H2-blank.2007|.2f}} | {{p.H2-blank.2012|.2f}} | {{p.H2-blank.2017|.2f}} | {{p.H2-blank.2022|.2f}} | {{p.H2-blank.all|.2f}} |

- `p` is the share of each eliminated group that splits as in H0b instead of
  following the base rule. `p = 1` is H0b.
- On the H2 bases the fitted `p` is between {{p.H2-blank.min|.2f}} and
  {{p.H2-abst.max|.2f}} in every fold.
- On H1, `p` is between {{p.H1.2007|.2f}} and {{p.H1.2017|.2f}} in four folds and
  {{p.H1.2002|.2f}} in the fold that tests on 2002 (that is, when 2002 is not in the
  training data).
- Held-out, H3(H1) has a higher mean score than H1 itself
  ({{score.H3(H1).mean|.2f}} against {{score.H1.mean|.2f}} pp); the difference comes
  from 2002 ({{score.H3(H1).2002}} against {{score.H1.2002}} pp).

### 5. Sensitivity (`sensitivity.csv`, `tied_groups.csv`, `blank_only.csv`)

**Candidate positions.** Every model is rerun on the hand-coded 1–7 scale (put on
0–1, same threshold) and on its alternative families. Changes are relative to the
main, poll-based results.

- Hand-coded 1–7 scale: order by mean {{sens.primary.split.ranking}}; the ranking
  {{sens.primary.split.text.same_ranking}} and the lowest mean belongs to
  {{sens.primary.split.text.same_best}} ({{sens.primary.split.best.model}}). H1's mean
  moves by {{sens.primary.split.change.H1.mean|+.2f}} pp, H2-abst by
  {{sens.primary.split.change.H2-abst.mean|+.2f}} pp, H2-blank by
  {{sens.primary.split.change.H2-blank.mean|+.2f}} pp. Without 2002 the lowest mean is
  {{sens.primary.split.best_without_2002.model}}.
- Alternative families ({{quality.with_alternative}} rows that list one): order by
  mean {{sens.alternative.split.ranking}}; the lowest mean belongs to
  {{sens.alternative.split.text.same_best}} ({{sens.alternative.split.best.model}}).
  H1's mean moves by {{sens.alternative.split.change.H1.mean|+.2f}} pp, H2-abst by
  {{sens.alternative.split.change.H2-abst.mean|+.2f}} pp.
- H2-abst and H2-blank rank {{sens.primary.split.rank.H2-abst}} and
  {{sens.primary.split.rank.H2-blank}} of {{n.models}} on the 1–7 scale, against
  {{rank.H2-abst}} and {{rank.H2-blank}} on the poll-based scale. H0b ranks
  {{rank.H0b}} on the poll-based scale, {{sens.primary.split.rank.H0b}} on the 1–7 scale
  and {{sens.alternative.split.rank.H0b}} under the alternative families.

**Ties.** On the poll-based scale, {{ties.polls.count}} eliminated candidates are
exactly equidistant from both finalists ({{ties.polls.elections}}); on the 1–7 scale
{{ties.primary.count}}, and {{ties.alternative.count}} under the alternative families.
Sending tied groups to abstention instead of splitting them changes no model's mean
by more than {{sens.polls.abstention.max_abs_change|.2f}} pp.

**Blank ballots alone ({{blank.years}}).** With blank and invalid ballots scored as
separate outcomes (first-round invalid ballots kept as invalid, every modelled
inflow counted as blank):

- invalid ballots are {{blank.2017.invalid_share_of_combined|.0f}}% of the combined
  second-round category in 2017 and {{blank.2022.invalid_share_of_combined|.0f}}% in 2022;
- every model under-predicts invalid ballots by the same amount:
  {{blank.2017.signed_invalid|+.1f}} pp in 2017 and {{blank.2022.signed_invalid|+.1f}} pp
  in 2022;
- on blank ballots alone, H2-blank's error is {{blank.H2-blank.2017.signed_blank|+.1f}} pp
  (2017) and {{blank.H2-blank.2022.signed_blank|+.1f}} pp (2022); H0b's is
  {{blank.H0b.2017.signed_blank|+.1f}} and {{blank.H0b.2022.signed_blank|+.1f}} pp;
- the order of models {{blank.2017.text.same_ranking}} in 2017 and
  {{blank.2022.text.same_ranking}} in 2022 when the five-outcome score replaces the
  four-outcome score.

### 6. Territories, 2022 (`territory_scores.csv`, figure `predicted_vs_observed_2022`)

| Model | Metropolitan ({{territory.metropolitan.areas.2022}} areas) | Overseas ({{territory.overseas.areas.2022}}) | Abroad ({{territory.abroad.areas.2022}}) |
|---|---:|---:|---:|
| H0a | {{territory.metropolitan.H0a.2022}} | {{territory.overseas.H0a.2022}} | {{territory.abroad.H0a.2022}} |
| H0b | {{territory.metropolitan.H0b.2022}} | {{territory.overseas.H0b.2022}} | {{territory.abroad.H0b.2022}} |
| H1 | {{territory.metropolitan.H1.2022}} | {{territory.overseas.H1.2022}} | {{territory.abroad.H1.2022}} |

### 7. Candidate positions (`candidate_scores.csv`, `candidate_table_quality.json`)

- Poll-based scale: {{scale.polls}} polls ({{scale.polls.2002}} in 2002,
  {{scale.polls.2007}} in 2007, {{scale.polls.2012}} in 2012, {{scale.polls.2017}} in
  2017, {{scale.polls.2022}} in 2022); {{scale.from_reports}} taken from the institutes'
  reports and {{scale.from_paper}} from the compilation by Delemazure, Dong, Peters
  and Tydrichová (2024). `[PENDING: poll orders checked against sources]`
- {{scale.unplaced}} candidacies unplaced ({{scale.unplaced_list}}; H0b row used).
  Largest disagreement between institutes for a placed candidate:
  {{scale.max_range_placed|.2f}} (unplaced above 0.4).
- Comparison scale (hand-coded 1–7): {{quality.rows}} rows; {{quality.draft_rows}}
  draft, {{quality.reviewed_rows}} reviewed, {{quality.without_score}} without a score.
  Party labels coded with more than one family across elections:
  {{quality.inconsistent_parties}}.

### 8. What the H2 threshold removes (`h2_threshold.csv`)

Shares are first-round shares of registered voters, all covered areas pooled,
on the poll-based scale (0 = left, 1 = right). H2 sends these groups to abstention (H2-abst) or to a
blank ballot (H2-blank) in full.

| Election | Finalist scores (A, B) | Eliminated supporters at least one third of the scale from both finalists | …of which exactly one third away (scores) |
|---|---|---:|---:|
| 2002 | {{h2.2002.finalist_a_score}}, {{h2.2002.finalist_b_score}} | {{h2.2002.beyond_pct}}% | {{h2.2002.on_threshold_pct}}% ({{h2.2002.on_threshold_scores}}) |
| 2007 | {{h2.2007.finalist_a_score}}, {{h2.2007.finalist_b_score}} | {{h2.2007.beyond_pct}}% | {{h2.2007.on_threshold_pct}}% ({{h2.2007.on_threshold_scores}}) |
| 2012 | {{h2.2012.finalist_a_score}}, {{h2.2012.finalist_b_score}} | {{h2.2012.beyond_pct}}% | {{h2.2012.on_threshold_pct}}% ({{h2.2012.on_threshold_scores}}) |
| 2017 | {{h2.2017.finalist_a_score}}, {{h2.2017.finalist_b_score}} | {{h2.2017.beyond_pct}}% | {{h2.2017.on_threshold_pct}}% ({{h2.2017.on_threshold_scores}}) |
| 2022 | {{h2.2022.finalist_a_score}}, {{h2.2022.finalist_b_score}} | {{h2.2022.beyond_pct}}% | {{h2.2022.on_threshold_pct}}% ({{h2.2022.on_threshold_scores}}) |

- In 2002 both finalists are on the right of the scale
  ({{h2.2002.finalist_a_score|.2f}} and {{h2.2002.finalist_b_score|.2f}}), and
  {{h2.2002.beyond_pct}}% of registered voters are in groups at least one third away
  from both, the whole left among them. {{h2.2002.on_threshold_pct}}% sit exactly on
  the threshold (Noël Mamère, {{h2.2002.on_threshold_scores}}).
- In the other elections the threshold removes little: {{h2.2007.beyond_pct}}% in
  2007, {{h2.2012.beyond_pct}}% in 2012, {{h2.2017.beyond_pct}}% in 2017 and
  {{h2.2022.beyond_pct}}% in 2022.
- H2-abst and H2-blank score {{score.H2-abst.2007}} and {{score.H2-blank.2007}} pp in
  2007 and {{score.H2-abst.2012}} and {{score.H2-blank.2012}} pp in 2012, against
  {{score.H2-abst.2017}} and {{score.H2-blank.2017}} pp in 2017.

## Interpretations

What the observations may mean. Each point is a reading of aggregate patterns
on the poll-based scale, not a statement about how individuals voted.

1. **The original baseline was weak for one identifiable reason.** H0a sends part
   of every eliminated group to abstention, and it over-predicts abstention in
   every election. Removing that single channel (H0b) lowers the error in every
   election. This answers the reviewers' question: most of H0a's error came from
   that choice, so H0b is the baseline later models should be judged against.

2. **There is no stable winner; the answer depends on 2002.** {{best.model}} has the
   lowest five-election mean, but it {{text.best_without_2002}} once 2002 is set
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
   H2-abst scores {{score.H2-abst.2002}} pp against {{score.H1.2002}} for H1. Where few
   voters are beyond the threshold, H2 stays close to H1
   ({{score.H2-abst.2012}} against {{score.H1.2012}} pp in 2012). The size of the
   failure also depends on where candidates are placed: on the hand-coded 1–7 scale,
   the left of 2017 and 2022 sat exactly on the threshold and H2 was much worse
   ({{sens.primary.split.change.H2-abst.mean|+.1f}} pp on average). H3 agrees:
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
   {{sens.primary.split.text.same_ranking}} (H2 falls), and under its alternative
   families it {{sens.alternative.split.text.same_ranking}} again; but on every scale
   H1 leads over five elections only because of 2002, and H0b or an H3 mixture close
   to it leads without 2002. The tie rule matters little: {{ties.polls.count}}
   candidates sit exactly halfway between the finalists ({{ties.polls.elections}}),
   and the abstention tie rule moves no mean by more than
   {{sens.polls.abstention.max_abs_change|.2f}} pp.

## Caveats that apply to everything above

- Aggregate (ecological) inference: many different individual behaviours produce
  the same area totals. A matrix that fits is not an observed transfer.
- 2002 and 2007 cover fewer areas ({{areas.2002}} and {{areas.2007}} against
  {{areas.2022}}); scores describe covered areas only.
- Naming a "best" model after comparing eight on the same five elections is
  itself a selection; no significance is claimed.
- The scale is one-dimensional and is an order: within a poll, candidates are
  equally spaced whatever their real ideological gap.
- 2002 rests on one institute ({{scale.polls.2002}} poll), and
  {{scale.from_paper}} of {{scale.polls}} orders come from a published compilation.
- The comparison 1–7 scale is an unreviewed draft; its alternative coding moves all
  {{quality.with_alternative}} listed rows at once.
- H3 is reported pending approval of its fitted parameter.
  `[PENDING: professor approval]`
