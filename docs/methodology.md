# Initial modelling and evaluation choices

## Denominators and outcomes

For each reporting unit and round, divide each candidate's vote count, combined
blank/invalid count and abstention count by that round's registered-voter count.
The shares sum to one. Do not divide candidate votes by valid ballots in model
inputs. Preserve both rounds' registration totals: their populations can differ.

## H0: explicit, provisional operational definition

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

This is one defensible starting definition, not a claim that the project team has
approved all behavioural details. In particular, no first-round abstainer is
mobilised under this baseline. Other definitions should be separate named models.

## Errors and aggregation

- Unit/outcome absolute error: `100 * abs(predicted_share - actual_share)`, in
  percentage points (pp).
- Unit MAE: mean of its four outcome errors; no weighting among outcomes.
- National comparison: weight unit predictions by round-two registered counts,
  then compare with actual counts divided by the same national denominator.
  These weights are for retrospective evaluation, not model fitting.
- National MAE: mean absolute error across the four nationally aggregated outcomes.
  It is different from the mean unit MAE; errors can cancel during aggregation.

The app includes every reporting area present in both original files, including
territories and voters abroad. The two rounds must cover the same unit codes;
missing areas cause a processing failure. Polling stations are validated within
each round, then aggregated independently. This does not infer station-level
transitions or harmonise historical commune boundaries.

H0 is now computed separately for all five elections. This does not establish
cross-election generalisation for fitted models. H3/H5 need
whole-election holdouts and a fitted-method protocol before implementation.


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
