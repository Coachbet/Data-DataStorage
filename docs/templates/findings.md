# Findings

Status of the candidate table: **{{coding_status}}**. Every result for H1, H2 and
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
- Every model in the main set under-predicts blank/invalid in 2017 and 2022 except
  H2-blank (H0b: {{signed.H0b.2017.blank_invalid|+.1f}} and
  {{signed.H0b.2022.blank_invalid|+.1f}} pp; H2-blank:
  {{signed.H2-blank.2017.blank_invalid|+.1f}} and {{signed.H2-blank.2022.blank_invalid|+.1f}} pp).
- In 2017, H0b and H1 over-predict finalist B ({{finalist_b.2017}}) by
  {{signed.H0b.2017.finalist_b|+.1f}} and {{signed.H1.2017.finalist_b|+.1f}} pp.
- In 2022, H1 over-predicts finalist A ({{finalist_a.2022}}) by
  {{signed.H1.2022.finalist_a|+.1f}} pp; H0b over-predicts finalist B by
  {{signed.H0b.2022.finalist_b|+.1f}} pp.
- H2-abst over-predicts abstention by {{signed.H2-abst.2017.abstention|+.1f}} pp in 2017
  and {{signed.H2-abst.2022.abstention|+.1f}} pp in 2022.

### 4. H3: fitted share `p` per fold (`h3_folds.csv`)

| Base | Test 2002 | Test 2007 | Test 2012 | Test 2017 | Test 2022 | All five (scenario page only) |
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

**Coding.** With `alternative_family` on the {{quality.with_alternative}} rows that
list one:

- order by mean: {{sens.alternative.split.ranking}};
- the ranking {{sens.alternative.split.text.same_ranking}}; the lowest mean belongs
  to {{sens.alternative.split.text.same_best}} ({{sens.alternative.split.best.model}});
- H1's mean moves by {{sens.alternative.split.change.H1.mean|+.2f}} pp, H2-abst by
  {{sens.alternative.split.change.H2-abst.mean|+.2f}} pp, H2-blank by
  {{sens.alternative.split.change.H2-blank.mean|+.2f}} pp;
- H2-abst and H2-blank rank {{sens.alternative.split.rank.H2-abst}} and
  {{sens.alternative.split.rank.H2-blank}} of {{n.models}} under the alternative coding,
  against {{rank.H2-abst}} and {{rank.H2-blank}} under the primary coding;
- H0b and H0a rank {{sens.alternative.split.rank.H0b}} and
  {{sens.alternative.split.rank.H0a}} under the alternative coding, against
  {{rank.H0b}} and {{rank.H0a}}.

**Ties.** Number of eliminated candidates equidistant from both finalists:
{{ties.primary.count}} under the primary coding and {{ties.alternative.count}} under
the alternative coding. The largest change in any model's mean score between
`tie=split` and `tie=abstention` is {{sens.primary.abstention.max_abs_change|.2f}} pp.

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

### 7. Candidate table (`candidate_table_quality.json`)

- {{quality.rows}} rows; {{quality.draft_rows}} draft, {{quality.reviewed_rows}} reviewed,
  {{quality.without_score}} without a score ({{fallback.years}}; H0b row used).
- Consistency: of {{quality.parties_checked}} party labels, those coded with more than
  one family across elections are {{quality.inconsistent_parties}}.
- Accuracy (two-coder agreement): {{quality.accuracy_status}}.
  `[PENDING: coder agreement]`

## Interpretations

What the observations may mean. Each point is a reading of aggregate patterns
under a draft coding, not a statement about how individuals voted.

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

3. **The distance threshold, as fixed, does not help.** H2 sends every group at
   least two steps from both finalists to a non-vote. In 2002, 2017 and 2022 that
   removes large left-coded groups from the finalists entirely, and the scores are
   worse than H0b's. H3 confirms it: when a share `p` is allowed to ignore the H2
   rule, the fit puts nearly everyone in that share. The threshold of two steps
   and the equal spacing of the scale are assumptions we did not tune, on purpose;
   a different threshold might behave differently, and choosing it by fit would
   need more elections than we have.

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
   {{sens.alternative.split.text.same_ranking}}. Conclusions that depend on the
   position of H1 relative to H0b should be treated as provisional until the
   two-coder review is done. The tie rule, in contrast, is irrelevant in practice:
   no tie occurs under either coding.

## Caveats that apply to everything above

- Aggregate (ecological) inference: many different individual behaviours produce
  the same area totals. A matrix that fits is not an observed transfer.
- 2002 and 2007 cover fewer areas ({{areas.2002}} and {{areas.2007}} against
  {{areas.2022}}); scores describe covered areas only.
- Naming a "best" model after comparing eight on the same five elections is
  itself a selection; no significance is claimed.
- The scale is one-dimensional and assumed equally spaced.
