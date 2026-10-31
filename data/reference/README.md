# Manual candidate positions

`candidate_positions.csv` contains **61 candidate-election records**: 16 in 2002,
12 in 2007, 10 in 2012, 11 in 2017 and 12 in 2022. It covers candidates who
actually contested the first round, not everyone who announced an intention to run.
The candidate roster is checked against the verified Ministry aggregates.

Version: **0.1, 31 October 2026**. This is a manually authored research input.
It is tracked in Git and works offline. It is not an official political
classification, a CHES extract or a measurement of voters' individual positions.
The team approved the scale and its direction, but has not reviewed the individual
classifications. Every assigned row is therefore marked `draft`.

## Coding convention

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

## Columns and provenance

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
in the Ministry results enter this CSV. H0 does not use this table.

When reviewing, update the year-specific row, its notes and sources together.
Record the reviewer and rationale in the Git change. Keep party affiliation
separate from the chosen political family and preserve unresolved cases explicitly.
