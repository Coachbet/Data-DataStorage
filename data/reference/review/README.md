# Independent coding of the candidate table

Two team members each code all 61 first-round candidacies **independently**. The
purpose is to measure how reproducible our 1–7 scale is before any model result
is interpreted. Nothing in this folder contains a code: `coding_sheet_template.csv`
is blind.

## Rules

1. **Work alone.** Do not discuss rows with the other coder until both sheets are
   committed. Do not open `../candidate_positions.csv`, its Git history or the
   app's candidate table while coding: they show the draft codes.
2. **Do not look at model fit.** Do not run `vote-transfer evaluate` or open
   `reports/` to decide a code. A code is a judgement about the candidacy, not a
   way to improve a score.
3. **Code the candidacy at that election**, not the person's later career and
   not a later party name. The row gives the party at the first round.
4. **Use the sources** listed in `source_ids` (resolved in `../sources.json`),
   plus any reference you would cite. Note extra sources in `coder_note`.
5. **Every row gets exactly one value.** If you cannot place a candidacy on a
   left–right scale, write `Unclassified` and say why in `coder_note`. Do not
   leave the cell empty and do not use Centre as a default.

## Codebook

| Value to write | Score | Working definition |
|---|---:|---|
| `Far left` | 1 | Revolutionary socialist and anti-capitalist parties |
| `Left` | 2 | Communist, radical parliamentary and green left |
| `Centre-left` | 3 | Mainstream social-democratic and radical centre-left |
| `Centre` | 4 | Centrist candidacies |
| `Centre-right` | 5 | Moderate conservative and liberal-centrist candidacies |
| `Right` | 6 | Conservative, liberal and sovereignist right |
| `Far right` | 7 | Nationalist far right |
| `Unclassified` | – | No defensible single position on this scale |

Spelling and capitals must match exactly; the script rejects anything else.

## Steps

```bash
# 1. Each coder copies the template under their own name (do not edit the template).
cp data/reference/review/coding_sheet_template.csv data/reference/review/coder_a.csv   # coder A
cp data/reference/review/coding_sheet_template.csv data/reference/review/coder_b.csv   # coder B

# 2. Each coder fills `political_family` (and `coder_note` where useful) in their
#    own file, commits it, and only then tells the other coder.

# 3. When both files are committed:
uv run vote-transfer review-agreement \
  --coder-a data/reference/review/coder_a.csv \
  --coder-b data/reference/review/coder_b.csv
```

The command writes `reports/results/coding_agreement.json` with:

- **percentage agreement** over the 61 rows (exact same value);
- **quadratic-weighted Cohen's kappa** on the rows both coders placed on the
  scale. The scale is ordinal, so a disagreement of three steps counts nine
  times a disagreement of one step. Rows either coder left `Unclassified` are
  excluded from kappa and stay in the percentage and the matrix;
- the **confusion matrix** (coder A in rows, coder B in columns);
- the **list of disagreements**, with the number of steps between the two codes.

## After the comparison

1. Discuss each disagreement and agree on a final code. Record the reason in the
   row's `classification_note` in `../candidate_positions.csv`.
2. Update `political_family`, `ideology_score` and, where one remains plausible,
   `alternative_family`. Set `review_status` to `reviewed` on every agreed row
   (keep `unresolved` only where no score is assigned).
3. Rebuild everything that depends on the table:

   ```bash
   make evaluate bundle analysis
   make check
   ```

   Every output switches from "draft coding" to "reviewed coding" by itself once
   all scored rows are marked `reviewed`.
4. Report the agreement figures as measured, including if they are low. A low
   kappa is a finding about the scale, not a failure to hide.

## What the automated tests use

`tests/test_review.py` fills temporary copies of the template with mechanical
rules (for example "row number modulo seven"). Those sheets are synthetic, live
only in a temporary folder during the test and say nothing about any candidate.
No agreement figure exists for this project until two people have done the work.
