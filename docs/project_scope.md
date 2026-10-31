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
| Candidate positions | Manual 1–7 family scale agreed; draft candidate table and sources in `data/reference/`; CHES and alternative axes remain possible sensitivity references |
| Individual transfers | Not observed; describe aggregate model patterns |
| 2027 | Hypothetical simulation, not a forecast |
| Fitted methods | The note plans a methodological discussion before H3/H5 fitting |

## Model sequence

| Hypothesis | Assumption | Implementation status |
|---|---|---|
| H0 | Eliminated support splits like the remaining electorate | First-round-only operational definition implemented; see methodology |
| H1 | Nearest finalist in an ordinal left–right ordering | Pending documented positions and tie rules |
| H2 | Nearest finalist in 1D/2D ideological distance, with an abstention/blank threshold | Pending positions, scales and threshold definition |
| H3 | A calibrated fraction does not follow the closest-candidate rule | Pending fitting protocol and election-level holdout |
| H4 | Strategic first-round voting masks broader preferences | Extension, pending Voter Autrement 2017 |
| H5 | Transfers learned by political family | Extension, pending preference data and fitting protocol |

## Next milestones

1. Completed: original-file adapters for 2002, 2007, 2012, 2017 and 2022, with
   year-specific schemas, coverage notes and small versioned aggregate snapshots.
2. Automate comparisons with consolidated results and independent published totals.
   Preserve discrepancies rather than forcing sources to agree.
3. Review the versioned manual candidate-to-party/family table. Resolve missing
   positions and agree on tie and threshold rules. If CHES is used as a sensitivity
   reference, select historically appropriate waves and document party mappings.
4. Implement H1/H2 and evaluate each assumption using the same outcome definitions.
5. Fit eligible models on whole elections and test on held-out elections; never
   randomly split departments from one election across training and test sets.
6. Scope Voter Autrement, alternative 2D positions and dated 2027 polling tables.
7. Build the 2027 simulation interface only after its inputs and assumptions exist.

The current pipeline covers all five elections: acquisition → validation →
processing → H0 → app. Curated aggregates in `data/bundled/` allow review without
raw downloads. 2002 and 2007 have partial national coverage. Cross-source checking,
matched-geography comparison and H1–H5 remain research work.
