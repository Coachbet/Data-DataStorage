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
| Candidate positions | Manual 1–7 family scale replaces the planned CHES table (see below); draft candidate table and sources in `data/reference/`; CHES and alternative axes remain possible sensitivity references |
| Individual transfers | Not observed; describe aggregate model patterns |
| 2027 | Hypothetical simulation, not a forecast |
| Fitted methods | The note plans a methodological discussion before H3/H5 fitting |

## Change from the acquisition note: candidate positions

The approved note planned a candidate-to-party table built from the Chapel Hill
Expert Survey (CHES) for H1, H2 and H5. The current input is instead a manually
coded table of seven political families (`data/reference/candidate_positions.csv`).
This is a deliberate change to the approved plan and must be presented as such:

- **Why:** CHES rates national parties, not candidacies. The note already expected
  small candidates to be missing and to be "placed by bloc"; with 61 first-round
  candidacies, including independents and minor parties, that placement becomes
  the dominant coding step anyway. A single documented family scale applies the
  same rule to every candidate. *The team should confirm this rationale.*
- **Cost:** the scores are a project operationalisation, not an external expert
  measurement. Two coders could reasonably disagree (for example PCF as Left or
  Far left), so the coding is a potential source of measurement bias.
- **Mitigation, before H1/H2 use:** two members code every row independently,
  without looking at model fit; report their agreement and resolve disagreements
  in the notes. `alternative_family` supports a sensitivity analysis, and CHES
  can still serve as an external check where it covers a party.

Until this review is done, every row stays `draft`. Since 15 November 2026 the
models H1–H3 read the draft scores so the pipeline can be built and tested, and
every output that depends on them is labelled "draft coding". The review kit is
in `data/reference/review/`.

## Model sequence

Status on 15 November 2026 (decisions recorded in `docs/methodology.md`):

| Hypothesis | Assumption | Implementation status |
|---|---|---|
| H0a | Eliminated support splits like the remaining electorate, abstainers included | Implemented (the original H0, unchanged) |
| H0b | Eliminated support splits between the finalists and blank/invalid only | Implemented; added after the second peer review |
| H1 | Nearest finalist on the 1–7 scale; ties split 50/50 | Implemented on the draft coding |
| H2 | As H1, with a non-vote when at least two steps from both finalists (abstention or blank variants) | Implemented on the draft coding; one-dimensional only |
| H3 | A calibrated share does not follow the closest-candidate rule | Implemented with leave-one-election-out; professor's approval pending |
| H4 | Strategic first-round voting masks broader preferences | **Dropped** (first peer review); future work |
| H5 | Transfers learned by political family | **Dropped** (first peer review); future work |

## Remaining milestones

See `docs/handoff.md` for the checklist. In short: the two-coder review of the
candidate table, the professor's answer on H3, and the final editing of the
report and slides. Cross-source comparison with the consolidated results for
2002–2017 remains optional further validation.

2002 and 2007 have partial national coverage. Every historical summary must say
"covered areas", not "France".
