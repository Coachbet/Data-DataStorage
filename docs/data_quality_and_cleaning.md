# Raw data quality assessment and cleaning justification

Intermediate deliverable, 3 November 2026. Group: Victor Henz, Edgar Gusching,
Louis Bettelli, Lucas Magret Delord, Oscar Moulet.

**Question.** Which assumptions about voter behaviour best explain second-round
results in French presidential elections (2002–2022)?

## 1. Intended use and raw data

Quality is judged against our use. For each reporting area and both rounds, we
need counts that **sum exactly** to the registered electorate: candidate votes,
blank/invalid ballots and abstention. The two rounds must cover identical areas.

**Source.** Ministry of the Interior polling-station files, 2002–2022, from
data.gouv.fr: administrative, secondary data (291 MB; about 65,000–70,000 stations
per round). Our script calls the dataset API, selects a pinned resource ID and
records URL, time, size and SHA-256 in a versioned manifest. Any later download
must reproduce that hash. A clean re-download on 31 October 2026 reproduced all
of them. The files contain no personal data.

**Scope.** Our target is the electorate's behaviour between rounds. The frame
contains **registered** voters only. In 2002 and 2007, voters abroad and some
overseas areas are missing (100 and 101 areas, against 107 from 2012).
Within the frame the data is a census, so there is no sampling error. However,
aggregates **cannot reveal individual transfers**.

## 2. Quality assessment

**Checkable from the data.** These are official totals, so the threshold is
**zero violations**. A violation would be a parsing error on our side, and the
pipeline stops rather than repairing it.

| Characteristic | Metric | Result (all years) |
|---|---|---|
| Validity | Schema per layout; nonnegative integers; `voters ≤ registered`; `valid ≤ voters` | 0 violations |
| Completeness | Required counts present | 100% |
| Completeness | Separate blank and invalid counts | 0% before 2017, 100% after |
| Uniqueness | Duplicate station or (station, candidate) keys | 0 |
| Consistency | Candidate votes = valid ballots, per station; same areas in both rounds | 0 violations |
| Consistency (2002–12) | Station totals repeated on every candidate row agree | 0 violations |
| Consistency (2017–22) | Published abstentions, blank and invalid balance the totals | 0 violations |
| Consistency across sources | 2022 sums against the Ministry's national summaries | 26/26 fields match |

Before 2017 only registered voters, voters and valid ballots are published.
Abstention and blank/invalid are **derived**, so the accounting identities hold by
construction for those years. The informative checks there are the bounds,
repeated totals and candidate sums.

**Needing context.** We used IQR fences, which stay robust where z-scores would
be distorted by a few extreme areas. A flag means "look closer", not "wrong".

| Finding | Interpretation |
|---|---|
| 2022: about 10 stations per round with 0 registered voters, 34–35 with nobody voting | Contribute nothing to any total, or count as abstention |
| One station abroad with 123,838 registered voters (median: 753) | Consular "stations": a feature of the frame |
| 3–6% of stations are turnout outliers, mostly low-turnout, 50–63% of them overseas or abroad | Not small stations; same pattern as at area level |
| Abstention outliers: Corsica, overseas areas, voters abroad, sometimes Seine-Saint-Denis | Known participation differences: the phenomenon itself |
| Registration changes between rounds: −0.7% to +0.3% (voters abroad, 2012: +3.35%) | Each round keeps its own denominator |

**Format problems.** There are three file layouts, all Windows-1252. In 2017/2022
only the first candidate block has a header, so a naive reader would lose most
votes. Ballot panel numbers change between rounds. Area codes such as `01`, `2A`
and `ZZ` must stay text. Area names are missing before 2017.

## 3. Cleaning decisions

We **removed, imputed or corrected no observation**. Each count is used as
published or derived by an exact identity.

| Issue | Response | Justification |
|---|---|---|
| Upstream file changed | Stop (hash check) | Results must refer to the reviewed bytes |
| Layout differs by year | Year-specific parser; stop on an unknown schema | A silent schema change would shift columns |
| Unlabelled candidate blocks | Parse every block (wide → long) | Candidate sums prove no votes are lost |
| Panel numbers change between rounds | Key candidates by name, within each year | Names are stable within an election |
| Abstention, blank/invalid not published (2002–12) | Derive exactly; record in `derived_fields` | Arithmetic, not an estimate |
| Blank vs invalid split missing (2002–12) | Keep as null; use the combined outcome every year | No invented data; one definition across years |
| Comment lines, other round's rows | Filter, with counts | Out of scope; nothing else is skipped |
| Unusual areas or stations | **Flag and retain** | Valid evidence about the electorate we study |
| Missing areas in 2002/2007 | Retain; label as "covered areas" | Cannot be recovered; cross-year comparison needs matched geography |

**Ledger.** Every raw line is accounted for. For example, 2002 has 1,154,556 lines:
17 comments, 1 empty line, 1,026,256 round-1 and 128,282 round-2 candidate rows.
Aggregation then reduces each round from about 65,000–70,000 stations to 100–107
areas. This step cannot be reversed. Candidate totals are joined to area totals
as many-to-one, and an outer-join coverage check stops on unmatched stations.

**Effect on the analysis.** Keeping the flagged areas barely changes the baseline
(H0) score: in 2022 it is 6.12 pp over all areas and 5.82 pp over metropolitan
areas only. Combining blank and invalid ballots loses detail after 2017 but keeps
the outcome comparable across years. Open points: published totals are checked
for 2022 only, and the 2022 licence metadata (`notspecified`) is unconfirmed.

## 4. Storage (preliminary)

Raw text is kept unchanged. Interim and processed tables are Parquet files: for
2022, 49 MB of text becomes 2.9 MB. The data is written once and read column by
column by a single process, and Parquet keeps types such as text codes and
integer counts. A relational database (SQLite/PostgreSQL) would enforce keys
declaratively, but suits concurrent writes and ad hoc joins, which we do not
need; our keys are enforced by executable checks instead. CSV is untyped and
mangles codes like `01`. A full comparison will follow in the final report.

**Reproduce:** `uv run vote-transfer acquire --all-years`, then `process
--all-years`, then `crosscheck --year 2022`. Diagnostics are written to each
`quality_report.json`.
