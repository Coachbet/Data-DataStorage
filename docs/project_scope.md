# Project scope and implementation roadmap

## Controlling project description

The supplied acquisition note dated **2 October 2026** explicitly changes the
original proposal. It is the current research specification, rather than an
instruction to execute every activity mentioned in the PDF immediately.

Question: **Which assumptions about voter behaviour best explain second-round
results in French presidential elections (2002–2022)?**

One observation is one department in one election. All input and output shares
use registered voters, including abstention and blank/invalid ballots. The current
raw files also contain reporting areas that are not departments; retain them
explicitly so national aggregation does not silently omit overseas voters.

## Decisions reconciled with the previous repository

| Topic | Current decision |
|---|---|
| Primary election data | Original Ministry files; harmonise them ourselves |
| Consolidated election data | Independent validation reference only |
| Socioeconomic indicators and media mentions | Removed from active scope |
| Small-department shrinkage | Not assumed; revisit only with evidence |
| Candidate positions | Poll-based scale from polling institutes' left-to-right orders (since 20 November 2026); the hand-coded 1–7 families are kept as a comparison (see below) |
| Individual transfers | Not observed; describe aggregate model patterns |
| 2027 | Dropped on 20 November 2026 (see below) |
| Fitted methods | The note plans a methodological discussion before H3/H5 fitting |

## Change from the acquisition note: candidate positions

The approved note planned a candidate-to-party table built from the Chapel Hill
Expert Survey (CHES) for H1, H2 and H5. Two changes followed, and both must be
presented as deliberate changes to the approved plan.

**First change (31 October 2026): a hand-coded 1–7 family scale.** CHES rates
national parties, not candidacies, and misses most of the 61 first-round
candidacies (independents and minor parties). The team coded seven political
families by hand (`data/reference/candidate_positions.csv`). The second peer
review found that no one had checked this table, although it is the only input
H1 and H2 add to the baseline.

**Second change (20 November 2026): a poll-based scale.** Following the advice
of Magdaléna Tydrichová, candidates are placed with the left-to-right orders that
polling institutes publish in their reports, which cover every candidate:

- `data/reference/polling_axes.csv`: 22 polls collected by the team (2002: 1,
  2007: 3, 2012: 3, 2017: 7, 2022: 8), each with its source link;
- `notebooks/candidate_scale.ipynb` turns them into a score from 0 (left) to 1
  (right), sets aside candidates it cannot place and writes
  `data/reference/candidate_scores.csv`.

Why: the positions come from outside the team instead of our own judgement, and
the source covers minor candidates. Cost: the scale is an order, not a measured
distance, and 2002 rests on one institute. The 1–7 table is kept, unreviewed, as
a sensitivity comparison; the main conclusion is the same on both scales.

## Change from the proposal: the 2027 scenario

The proposal's "applied version" asked what a hypothetical pair of 2027 finalists
would imply, department by department. It was implemented as a page applying an
assumption to the 2022 electorate, then **dropped on 20 November 2026** to keep
the project on its main question (how eliminated candidates' voters transfer in
the second round) and on the five elections we can evaluate.

## Model sequence

Status on 20 November 2026 (decisions recorded in `docs/methodology.md`):

| Hypothesis | Assumption | Implementation status |
|---|---|---|
| H0a | Eliminated support splits like the remaining electorate, abstainers included | Implemented (the original H0, unchanged) |
| H0b | Eliminated support splits between the finalists and blank/invalid only | Implemented; added after the second peer review |
| H1 | Nearest finalist on the poll-based scale; ties split 50/50 | Implemented |
| H2 | As H1, with a non-vote when at least one third of the scale from both finalists (abstention or blank variants) | Implemented; one-dimensional only |
| H3 | A calibrated share does not follow the closest-candidate rule | Implemented with leave-one-election-out; professor's approval pending |
| H4 | Strategic first-round voting masks broader preferences | **Dropped** (first peer review); future work |
| H5 | Transfers learned by political family | **Dropped** (first peer review); future work |

## Remaining milestones

Checking the 22 poll orders against their sources, the professor's answer on H3,
the decision record, the final report and the slides. Cross-source comparison with
the consolidated results for 2002–2017 remains optional further validation.

2002 and 2007 have partial national coverage. Every historical summary must say
"covered areas", not "France".
