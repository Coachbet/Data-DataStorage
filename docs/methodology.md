# Modelling and evaluation choices

## Denominators and outcomes

For each reporting unit and round, divide each candidate's vote count, combined
blank/invalid count and abstention count by that round's registered-voter count.
The shares sum to one. Do not divide candidate votes by valid ballots in model
inputs. Preserve both rounds' registration totals: their populations can differ.

## H0a: the original baseline (unchanged)

The acquisition note says eliminated candidates' voters split like the rest of
the electorate, but does not completely specify non-voting transitions. The
initial implementation makes this choice explicit:

1. Let `x` contain the first-round shares of all candidates, blank/invalid and abstention.
2. Let `K = {finalist A, finalist B, blank/invalid, abstention}`.
3. Retained groups stay in their own option. Each eliminated group is allocated
   according to `q[k] = x[k] / sum(x[t] for t in K)`.
4. Thus `predicted[k] = x[k] + eliminated_share * q[k] = q[k]`.

This corresponds to a nonnegative transfer matrix with rows summing to one:
retained groups have identity rows, and eliminated groups have the same row `q`.
It has no fitted parameters. It uses only first-round counts and the identities
of the two finalists, never observed second-round vote shares. A zero retained
mass is undefined and rejected.

On 31 October 2026 the team confirmed that no first-round abstainer is mobilised
under H0. This is already the implemented behaviour, so predictions do not change.
It does not imply equal abstention shares in the two rounds: some eliminated
support is also allocated to abstention. The other behavioural details remain an
explicit starting definition, not observed transfers. Other definitions should
be separate named models.

From 15 November 2026 this model is named **H0a**. Its definition and its
predictions are unchanged.

## The transfer-matrix form shared by all models

Every assumption is a matrix `β` with one row per first-round group (each
candidate, `blank_invalid`, `abstention`) and one column per second-round outcome
`(finalist A, finalist B, blank_invalid, abstention)`. Rows are nonnegative and
sum to one. For an area with first-round shares `x`, the prediction is
`ŝ[k] = Σ_g x[g] · β[g, k]`, which also sums to one.

- **Finalist A** is the finalist with more first-round votes over the covered
  areas, **finalist B** the other. The labels use first-round information only.
- **Retained groups** (both finalists, `blank_invalid`, `abstention`) have identity
  rows in every model: they stay where they were. No model mobilises first-round
  abstainers or moves first-round finalist voters.
- Models differ only in the rows of **eliminated candidates**.

The rules below were fixed by the team on 15 November 2026, before any H0b–H3
result was computed. None was chosen or adjusted by looking at fit.

### H0b: proportional split without abstention

Each eliminated group splits between finalist A, finalist B and `blank_invalid`
in proportion to the area's own first-round shares, with nothing sent to
abstention:

`β[g, k] = x[k] / (x[A] + x[B] + x[blank_invalid])` for `k ∈ {A, B, blank_invalid}`, and `β[g, abstention] = 0`.

H0a is the same rule with abstention included among the destinations. Both are
reported. H0a answers "what if eliminated voters behaved like everyone else,
abstainers included"; H0b answers "what if people who voted once vote again".
Because both depend on `x`, their matrices differ from area to area.

### H1: nearest finalist

Let `s(c)` be the 1–7 score of candidate `c` and `d(c, F) = |s(c) − s(F)|`.
An eliminated group goes entirely to the nearer finalist:

- `d(c, A) < d(c, B)`: row `(1, 0, 0, 0)`;
- `d(c, B) < d(c, A)`: row `(0, 1, 0, 0)`;
- **tie** `d(c, A) = d(c, B)`: row `(½, ½, 0, 0)`.

Named sensitivity variant `tie=abstention`: a tied group gets row `(0, 0, 0, 1)`.

### H2: nearest finalist with a distance threshold

As H1, **unless** `d(c, A) ≥ 2` **and** `d(c, B) ≥ 2`. A group at least two steps
from both finalists goes to a non-vote outcome. Two named variants are always
reported together, and neither is selected by fit:

- **H2-abst**: row `(0, 0, 0, 1)`;
- **H2-blank**: row `(0, 0, 1, 0)`.

The threshold is checked first, so a group exactly two steps from both finalists
is a non-vote, not a tie. Below the threshold, ties follow the H1 rule. "At least
two" includes distance two exactly.

### Missing scores

A candidate with no score (Jacques Cheminade, 2012 and 2017) cannot be placed.
In H1 and H2 that group uses its **H0b row**. A missing score is never read as
Centre or zero, and the votes are never dropped. A finalist without a score, or a
candidate absent from the reference table, stops the evaluation with an error.

### H3: a calibrated share that does not follow the rule

`β_H3 = (1 − p) · β_base + p · β_H0b`, with `base ∈ {H1, H2-abst, H2-blank}` and
one parameter `p ∈ [0, 1]`: the share of each eliminated group that ignores
ideological proximity and splits as in H0b. `p = 0` is the base model; `p = 1` is
H0b. Since prediction is linear in `β`, `ŝ_H3 = (1 − p) · ŝ_base + p · ŝ_H0b`.

**Fitting.** Grid search over `p = 0.00, 0.01, …, 1.00`. The objective is the
primary score averaged over the training elections, each election counting once.
If several values tie, the smallest `p` is kept.

**Validation: leave-one-election-out.** For each election in turn, `p` is fitted
on the other four and the model is scored on the fifth. Areas of one election are
never split between training and test. Only these held-out scores are reported
for H3 and only held-out predictions are stored. The fitted `p` of every fold is
in `evaluation_report.json`. A fit on all five elections is also recorded; it is
used only by the 2027 scenario page, where no election is being scored.

With five elections there are five folds. Held-out scores describe how the rule
transfers between these elections; they support no significance statement.

**A note on weights.** The 31 October text below says registered-voter weights
"must not enter model fitting". That sentence was written to stop second-round
information from the evaluated election being used as a predictor. The H3
protocol agreed on 15 November minimises the primary score on *training*
elections, and that score uses their round-two weights. The held-out election's
weights and outcomes never enter the fit. The tension between the two statements
is listed in `docs/handoff.md` for the team to confirm.

### Variants and what is reported

| Variant | Meaning |
|---|---|
| `positions=primary;tie=split` | **Main analysis**: `ideology_score`, 50/50 ties |
| `positions=primary;tie=abstention` | Tie sensitivity |
| `positions=alternative;tie=split` | Coding sensitivity: every row that lists an `alternative_family` uses it, all at once |
| `positions=alternative;tie=abstention` | Both changes together; the only setting pair in which the tie rule can matter if the primary coding produces no tie |

The alternative coding is one alternative scenario, not a search over codings.
H0a and H0b read no scores; their variant is `default`.

Until two coders have reviewed the candidate table, every score is a draft and
every H1–H3 output is labelled **draft coding** (the label is derived from the
table's `review_status` column, not typed by hand).

## Errors and aggregation

- Unit/outcome absolute error: `100 * abs(predicted_share - actual_share)`, in
  percentage points (pp).
- Unit MAE: mean of its four outcome errors; no weighting among outcomes.
- **Primary score, agreed 31 October 2026:** average the unit MAEs with weights
  `registered_round_2[unit] / sum(registered_round_2[selected_units])`.
  This measures accuracy within departments/reporting areas. Compute absolute
  errors before pooling so opposite local errors cannot cancel.
  The team chose registered voters rather than resident population. Round-two
  registration matches the evaluated round and needs no INSEE population join.
- National comparison: weight unit predictions by round-two registered counts,
  then compare with actual counts divided by the same national denominator.
  These weights are for retrospective evaluation, not model fitting.
- National MAE: mean absolute error across the four nationally aggregated outcomes.
  This is a secondary diagnostic, labelled "Gap in combined results" in the app.
  It is different from the primary weighted unit MAE; errors can cancel during aggregation.

The primary score includes all available reporting areas by default, including
non-department territories and voters abroad. Filters recompute weights over the
selected areas. A filtered score or a partial historical coverage score must not
be labelled a complete France score. These are registered-electorate weights,
not resident-population weights. They are retrospective evaluation weights and
must not enter model fitting or be used as predictive second-round information.

The app includes every reporting area present in both original files, including
territories and voters abroad. The two rounds must cover the same unit codes;
missing areas cause a processing failure. Polling stations are validated within
each round, then aggregated independently. This does not infer station-level
transitions or harmonise historical commune boundaries.

Every model is computed for all five elections. Parameter-free models (H0a, H0b,
H1, H2) are fitted to nothing, so each election is a test for them. H3 is the
only fitted model and is scored on held-out elections only.


## Historical source coverage

The original 2002 file covers 100 reporting units; 2007 covers 101; 2012, 2017 and
2022 cover 107. All units within each source have both rounds. Compared with 2022
codes, 2002 lacks `ZM`, `ZN`, `ZP`, `ZS`, `ZW`, `ZX`, `ZZ`; 2007 lacks `ZN`, `ZP`,
`ZS`, `ZW`, `ZX`, `ZZ`. This is a coverage description, not a claim that all of
those administrative codes existed unchanged in earlier years.

Consequently, use "all covered units" for historical pooled results. Do not
compare these totals as identical national electorates. A future matched-geography
study must explicitly select common units and review boundary changes.
Before 2017, only combined blank/invalid counts are available (voters minus valid
votes). The separate counts remain null in interim tables; the model outcome is
combined for every year, so its definition stays consistent.

## Manual ideological reference and distance rules

The team chose seven families on 31 October 2026: Far left (1), Left (2),
Centre-left (3), Centre (4), Centre-right (5), Right (6), Far right (7).
`data/reference/candidate_positions.csv` supplies the manually coded party and
family for each first-round candidate-election pair. The scale is agreed;
individual classifications are drafts and Cheminade's two positions are unresolved.
See the reference README for the codebook, sources and sensitivity alternatives.

The one-dimensional distance is `abs(score_candidate - score_finalist)`.
Using differences assumes equally spaced categories. This is a modelling
convention, not an empirical measurement. Candidate positions do not establish
their voters' individual preferences. H0a and H0b do not read these scores.

The tie rule, the threshold ("at least two from both finalists"), the treatment
of first-round blank/invalid and abstention groups (identity rows) and of missing
positions (H0b row) are defined above. Before 2017 the evaluated outcome remains
combined blank/invalid, even where the behavioural reading concerns blank voting;
for 2017 and 2022 a sensitivity analysis scores blank ballots alone.

## Out of scope

- **H4 (strategic first-round voting) and H5 (transfers learned by family)** were
  dropped on the recommendation of the first peer review: both depend on a single
  2017 preference dataset. They are future work.
- **Two-dimensional distances** are not computed: no two-dimensional coding of
  the 61 candidacies exists.
- **Forecasting.** The 2027 page applies a chosen assumption to the 2022
  first-round electorate. It is a hypothetical scenario, not a forecast.
