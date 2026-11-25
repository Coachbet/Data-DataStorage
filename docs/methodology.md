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

Let `s(c)` be the poll-based score of candidate `c`, between 0 (leftmost) and 1
(rightmost), and `d(c, F) = |s(c) − s(F)|` (see "Candidate positions" below). An
eliminated group goes entirely to the nearer finalist:

- `d(c, A) < d(c, B)`: row `(1, 0, 0, 0)`;
- `d(c, B) < d(c, A)`: row `(0, 1, 0, 0)`;
- **tie** `d(c, A) = d(c, B)`: row `(½, ½, 0, 0)`.

Scores are fractions, so distances that are equal on paper are compared with a
tolerance of 10⁻⁹: floating-point rounding never breaks a real tie (Christine
Boutin in 2002 is exactly halfway between Chirac and Le Pen).

Named sensitivity variant `tie=abstention`: a tied group gets row `(0, 0, 0, 1)`.

### H1-soft: a split that depends on distance

Added on 21 November 2026, after the results of the other models were known; the
formula has no parameter and was not adjusted afterwards. Instead of sending the
whole group to the nearer finalist, each finalist gets a share inversely
proportional to its distance:

`β[g, A] = d(c, B) / (d(c, A) + d(c, B))`, `β[g, B] = d(c, A) / (d(c, A) + d(c, B))`,
and nothing goes to `blank_invalid` or abstention.

The nearer finalist always gets more than half, and an equidistant group splits
50/50 by construction, so the tie rule does not apply. Unplaced candidates use the
H0b row. H1-soft is not an H3 base.

### H2: nearest finalist with a distance threshold

As H1, **unless** `d(c, A) ≥ 1/3` **and** `d(c, B) ≥ 1/3`. A group at least one
third of the scale from both finalists goes to a non-vote outcome. The threshold
is the rule fixed on 15 November 2026 on the 1–7 scale (two steps out of six),
carried over unchanged when the poll-based scale became the main one. Two named variants are always
reported together, and neither is selected by fit:

- **H2-abst**: row `(0, 0, 0, 1)`;
- **H2-blank**: row `(0, 0, 1, 0)`.

The threshold is checked first, so a group exactly one third from both finalists
is a non-vote, not a tie. Below the threshold, ties follow the H1 rule. "At least
one third" includes one third exactly (with the same tolerance).

### Missing scores

A candidate with no score cannot be placed: on the poll-based scale, Jacques
Cheminade (2012, 2017) and Jean Lassalle (2017). In H1 and H2 that group uses its
**H0b row**. A missing score is never read as
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
in `evaluation_report.json`. A fit on all five elections is also recorded as a
description; it is never scored.

With five elections there are five folds. Held-out scores describe how the rule
transfers between these elections; they support no significance statement.

**Weights in the fit.** `p` minimises the primary score on the *training*
elections, and that score uses their round-two registered-voter weights. The
held-out election's weights and outcomes never enter the fit.

### Variants and what is reported

| Variant | Meaning |
|---|---|
| `positions=polls;tie=split` | **Main analysis**: poll-based scale, 50/50 ties |
| `positions=polls;tie=abstention` | Tie sensitivity |
| `positions=primary;tie=split` | Scale sensitivity: the hand-coded 1–7 families, put on 0–1 |
| `positions=primary;tie=abstention` | Both changes together |
| `positions=alternative;tie=split` | The 1–7 families with every listed `alternative_family`, all at once |
| `positions=alternative;tie=abstention` | Both changes together |

The 1–7 scale is put on 0–1 with `(score − 1) / 6`, so its results are exactly
those of the original rules (two steps out of six is one third). The alternative
coding is one alternative scenario, not a search over codings. H0a and H0b read
no scores; their variant is `default`. Every output states that the main positions
are the **poll-based scale** and that the 1–7 comparison is a **draft coding**.

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
  These weights are for retrospective evaluation; the only fit that uses them is
  H3's, on training elections (see above).
- National MAE: mean absolute error across the four nationally aggregated outcomes.
  This is a secondary diagnostic, labelled "Gap in combined results" in the app.
  It is different from the primary weighted unit MAE; errors can cancel during aggregation.

The primary score includes all available reporting areas by default, including
non-department territories and voters abroad. Filters recompute weights over the
selected areas. A filtered score or a partial historical coverage score must not
be labelled a complete France score. These are registered-electorate weights,
not resident-population weights. They are retrospective evaluation weights.
Registered-voter weights from training elections may enter the H3 fit through the
primary score; the weights and outcomes of the election being evaluated never
enter a fit and are never used as predictive second-round information.

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

## Candidate positions

### Main: the poll-based scale (20 November 2026)

Polling institutes list the candidates in a left-to-right order in their
published reports, and these orders include every candidate, minor ones too.
Following the advice of Magdaléna Tydrichová, we use them instead of positions we
coded ourselves.

- **Collection.** `data/reference/polling_axes.csv`: one row per poll, with the
  institute, fieldwork dates, client, source type, source link and the candidates
  in left-to-right order. We used the last pre-election poll we could find for
  each institute. 2002: Ipsos (the only original report we found). 2007: Ipsos,
  Ifop, CSA (CSA through a press article). 2012: Ifop, Harris Interactive, Ipsos.
  2017 (7 institutes) and 2022 (8 institutes): the orders compiled by Delemazure,
  Dong, Peters and Tydrichová (2024), arXiv 2405.04525, Tables 2 and 7.
- **Score.** `notebooks/candidate_scale.ipynb` (`make scale`) writes
  `data/reference/candidate_scores.csv`. In a poll of `n` candidates, the
  candidate in place `i` (from 0) gets `i / (n − 1)`. A candidate's score is the
  mean of their positions across the institutes of that election. The file keeps
  every decimal, because rounding would break exact ties.
- **Unplaced candidates** (rules fixed before any model was run on the scale).
  A candidate is unplaced if institutes list them last by default (Jacques
  Cheminade), or if their positions differ by more than 0.4 between institutes.
  The first pass finds them (Cheminade 2012 and 2017, Lassalle 2017); they are
  removed from their election's polls and the second pass spreads the others
  again between 0 and 1. Their score is left empty and their voters follow the
  H0b row.
- **Checks.** Every candidate identifier matches the Ministry files; a test
  recomputes the scale from the polls and fails if `make scale` was not rerun.

The scale is an **order**, not a measured distance: within a poll, neighbours are
evenly spaced whatever their real ideological gap, and institutes' table
conventions enter it (in 2007 they list the PS before the Greens, so Dominique
Voynet sits slightly right of Ségolène Royal). Scores are comparable within an
election, not across elections.

### Comparison: the hand-coded 1–7 families

The team chose seven families on 31 October 2026: Far left (1), Left (2),
Centre-left (3), Centre (4), Centre-right (5), Right (6), Far right (7).
`data/reference/candidate_positions.csv` gives a hand-coded family for each
candidate-election pair, with sources for the party affiliation and an
alternative family where one is plausible. It was the main input until
20 November 2026. No outside source checked it and two coders never reviewed it,
so it is now only a sensitivity comparison (variants `primary` and `alternative`).

### Distance

The one-dimensional distance is `abs(score_candidate - score_finalist)`. This is a
modelling convention, not an empirical measurement. Candidate positions do not
establish their voters' individual preferences. H0a and H0b do not read them.

The tie rule, the threshold ("at least one third from both finalists"), the treatment
of first-round blank/invalid and abstention groups (identity rows) and of missing
positions (H0b row) are defined above. Before 2017 the evaluated outcome remains
combined blank/invalid, even where the behavioural reading concerns blank voting;
for 2017 and 2022 a sensitivity analysis scores blank ballots alone.

### Blank-only scoring (2017 and 2022)

The Ministry publishes blank and invalid ballots separately from 2017. For those
two elections `blank_only.csv` scores every model on five outcomes instead of
four: finalist A, finalist B, blank, invalid, abstention. The convention is the
same for every model and was confirmed by the team:

- **Invalid ballots stay invalid.** The predicted invalid share of an area is its
  first-round invalid share (an identity row). Invalid ballots partly reflect
  mistakes, so no behavioural rule here tries to explain their change.
- **Every modelled inflow is a blank ballot.** Predicted blank = the model's
  predicted `blank_invalid` share minus the first-round invalid share. Whatever a
  model sends to `blank_invalid` (H0a, H0b, H2-blank, H3) is counted as blank.
- The score is the same weighted area MAE, over five outcomes. The invalid error
  is therefore identical for all models, and the four-outcome score stays the
  primary score. The split does not exist before 2017 and is never imputed.

## Out of scope

- **H4 (strategic first-round voting) and H5 (transfers learned by family)** were
  dropped on the recommendation of the first peer review: both depend on a single
  2017 preference dataset. They are future work.
- **Two-dimensional distances** are not computed: no two-dimensional position of
  all 61 candidacies exists.
- **The 2027 scenario** (the proposal's "applied version": two hypothetical 2027
  finalists applied to the 2022 electorate) was dropped on 20 November 2026 to keep
  the project on its main question. No forecast is made.
- **Other sources of positions**, considered and rejected: Chapel Hill Expert
  Survey and ParlGov scores (parties only, most minor candidates missing), the
  Manifesto Project (legislative manifestos of parties with seats), scoring
  candidates' programmes ourselves (many 2002–2007 programmes unavailable, and
  more judgement calls than the family scale), and a two-coder review of the
  1–7 families (it measures agreement between us, not accuracy).
