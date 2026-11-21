# Candidate positions

This folder holds the inputs that place the 61 first-round candidacies (16 in
2002, 12 in 2007, 10 in 2012, 11 in 2017 and 12 in 2022) on a left-right axis.
Every roster is checked against the verified Ministry aggregates. H0a and H0b use
none of these files.

| File | What it is | Who writes it |
|---|---|---|
| `polling_axes.csv` | **Collected data.** One row per poll: year, institute, fieldwork dates, client, source type, source link and the candidates in the institute's left-to-right order | The team, by hand, from the institutes' reports |
| `candidate_scores.csv` | **The main scale.** One row per candidacy: score from 0 (left) to 1 (right), lowest and highest position across institutes, number of institutes, status (`placed` or `unplaced`) and reason | `notebooks/candidate_scale.ipynb` (`make scale`) |
| `candidate_positions.csv`, `sources.json` | **Comparison scale.** The hand-coded 1–7 families used until 20 November 2026, with sources for each party affiliation | The team, by hand (version 0.1, 31 October 2026) |

## The poll-based scale (main)

**Sources.** The last pre-election poll we could find for each institute. 2002:
Ipsos, 15–16 April (no other institute's original report was found). 2007:
Ipsos, Ifop and CSA (CSA through a press article reproducing its table). 2012:
Ifop, Harris Interactive and Ipsos. 2017 and 2022: the orders of 7 and 8
institutes compiled by Delemazure, Dong, Peters and Tydrichová (2024),
"Comparing Ways of Obtaining Candidate Orderings from Approval Ballots",
arXiv 2405.04525, Tables 2 and 7. Each row of `polling_axes.csv` links to its
source; candidate identifiers are the Ministry-derived slugs.

**Score.** In a poll of `n` candidates, the candidate in place `i` (from 0) gets
`i / (n − 1)`; the score is the mean across the election's institutes. The file
keeps every decimal: rounding to three decimals would break exact ties (Christine
Boutin in 2002 is exactly halfway between Chirac and Le Pen).

**Unplaced candidates.** Jacques Cheminade is always unplaced, because
institutes list him last by default, not because he is the furthest right. Any
candidate whose positions differ by more than 0.4 between institutes is also
unplaced (Jean Lassalle in 2017). Unplaced candidates are removed from their
election's polls and the scale is recomputed without them; their score is empty
and H1 and H2 use the H0b row for their voters. Both rules were fixed before any
model was run on the scale.

**Limits.** The scale is an order: neighbours in a poll are evenly spaced
whatever their real gap, and institutes' table conventions enter it (in 2007 they
list the PS before the Greens). Scores compare candidates within one election,
not across elections. A test recomputes the scale from `polling_axes.csv` and
fails if `make scale` was not rerun after an edit.

## The hand-coded 1–7 families (comparison)

The team approved the scale and its direction, but never reviewed the individual
classifications, and no outside source checked them: every assigned row is
`draft`. Since 20 November 2026 the table is used only as a sensitivity
comparison (`positions=primary` and `positions=alternative`), put on the 0–1
scale with `(score − 1) / 6`.

### Coding convention

| Family | Score | Working interpretation |
|---|---:|---|
| Far left | 1 | Revolutionary socialist and anti-capitalist parties |
| Left | 2 | Communist, radical parliamentary and green left |
| Centre-left | 3 | Mainstream social-democratic and radical centre-left |
| Centre | 4 | Centrist candidacies |
| Centre-right | 5 | Moderate conservative and liberal-centrist candidacies |
| Right | 6 | Conservative, liberal and sovereignist right |
| Far right | 7 | Nationalist far right |

These are project conventions. In particular, distinguishing Left from Far left
or Centre-left is a modelling choice. Scores order families; equal spacing is an
additional assumption if differences are used as distances. An ordinal scale
alone does not prove that every adjacent pair is equally far apart.

`Unclassified` is a missing classification, not an eighth political family.
Cheminade's two records have no score: the sources describe conflicting political
traditions. Do not replace missing values with zero or Centre, drop the associated
votes, or run a complete distance model until this case has an explicit treatment.
Asselineau's Right assignment is particularly tentative because he rejects the
left-right divide. Review it alongside a sovereignty axis.

Mainstream PS candidacies are provisionally Centre-left, while Hamon's 2017
candidacy is Left. PCF and Melenchon are Left under the parliamentary-left
convention, with Far left as a sensitivity alternative. Macron is Centre in both
years, with Centre-right as an alternative. These choices must be reviewed before
comparing model performance, rather than adjusted to improve the observed fit.

### Columns and provenance

| Column | Meaning |
|---|---|
| `year` | Election year |
| `candidate_id` | Exact Ministry-derived slug; join on year and this ID |
| `candidate_name` | Canonical display spelling, with accents |
| `party_abbreviation`, `party_name` | Party or candidacy movement at the first round; independent where applicable |
| `political_family` | Proposed project family, or Unclassified |
| `ideology_score` | Nullable integer 1–7; Far left = 1, Far right = 7 |
| `alternative_family` | One plausible sensitivity alternative, not an exhaustive list or a second active score |
| `review_status` | `draft`, `reviewed` or `unresolved`; no row currently reviewed by the team |
| `classification_note` | Reason for the coding and relevant ambiguity |
| `source_ids` | Semicolon-separated keys into `sources.json` |

French party names are retained as proper names. Supporting a candidacy does not
necessarily mean party membership: Schivardi and Bove are recorded as independent
in the OSCE report. Melenchon's 2012 party is PG and his candidacy coalition was
Front de gauche. Historical names are retained (UDF in 2007, DLR in 2012, FN and
En Marche in 2017, LREM in 2022).

`sources.json` records reference URLs and their purposes, consulted on
31 October 2026. References substantiate affiliations and background; they do not
endorse our seven-category scores. RFI's older pages were available through search
excerpts but direct retrieval timed out. The 2002 overview is a secondary reference
and should receive a primary-source cross-check during the group's review.
France 24 also lists some unsuccessful prospective candidates: only names present
in the Ministry results enter this CSV. H0a and H0b do not use this table.

### Checks

Automated checks on this table (same party coded identically across elections;
rows without a score) are written to `reports/results/candidate_table_quality.json`
by `vote-transfer analyse`. `alternative_family` drives the `positions=alternative`
variant: every row that lists an alternative uses it, all at once.
