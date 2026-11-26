# Vote transfer

Website of the project: <https://vote-transfer.streamlit.app/>

## Research question

Which assumptions about voter behaviour best explain second-round results in
French presidential elections (2002 to 2022)?

In a French presidential election only two candidates reach the second round, so
the voters of all the other candidates have to choose again. The vote is secret,
which means the official results only give totals: we know how many people chose
each option in each round, but not who moved where. So we cannot observe the
transfers directly. What we do instead is write possible behaviours as precise
rules, use each rule to predict the second round of every area from its first
round, and measure which prediction is the closest to the real result. Our results
describe patterns in the totals, not what individual voters did.

## How to run it

You need Python 3.12 and [uv](https://docs.astral.sh/uv/). Every step is a make
command, and make calls uv for us, so nothing has to be installed by hand. From
the root of the repository:

```bash
make setup      # install the exact package versions from uv.lock
make app        # open the website on http://localhost:8501
make analysis   # rebuild every result, figure, table and document
make check      # run the tests, the linter and the data checks
make data       # download the Ministry files again and rebuild everything
```

`make setup`, `make app`, `make analysis` and `make check` work on a fresh clone
without downloading any data, because the cleaned results of the five elections
and all the predictions are already in `data/bundled/`. Only `make data` needs
internet: it downloads about 293 MB from data.gouv.fr and checks every file
against the SHA-256 hash we recorded, so it stops if a file has changed.

`make data` is the same as running `make acquire`, `make process`, `make scale`,
`make evaluate` and `make bundle` one after the other. On Windows, where make is
not installed by default, you can run the commands written in the `Makefile`
directly (for example `uv run streamlit run site/app.py`).

## Data collection

We use two inputs.

The first one is the official results of the Ministry of the Interior, published
on data.gouv.fr with one line per polling station, for the two rounds of 2002,
2007, 2012, 2017 and 2022. Together this is 673,228 polling-station records. For
each station we keep the registered voters, the abstentions, the blank and invalid
ballots and the votes of each candidate, and then we add them up by area
(department, overseas territory or voters abroad). The original files are never
modified: their source, date and hash are in `data/raw/official/<year>/manifest.json`.
If a check fails (duplicates, negative counts, totals that do not add up, rounds
that do not cover the same areas), the build stops, because we never remove, fill
in or correct an observation. The 2002 and 2007 files do not include the voters
abroad and some overseas areas, so for these years the results only describe the
covered areas (100 and 101 areas, against 107 in 2022). The cleaned tables are
stored as Parquet: all of them take about 0.6 MB, against about 11.6 MB in CSV.

The second input is a left-right position for each of the 61 first-round
candidacies. Polling institutes list the candidates from left to right in their
reports, so we collected 22 of these orders from 9 institutes: 7 from the
institutes' own reports (2002 to 2012) and 15 from the compilation of Delemazure,
Dong, Peters and Tydrichová (2024, arXiv:2405.04525) for 2017 and 2022. Inside each
poll the candidates are evenly spaced between 0 and 1, and then we take the average
over the institutes. Three candidacies cannot be placed (Cheminade 2012, Cheminade
2017 and Lassalle 2017), and their voters follow the H0b rule. The polls are in
`data/reference/polling_axes.csv` and the scale is built by
`notebooks/candidate_scale.ipynb` (`make scale`).

## Hypotheses

Every hypothesis is a transfer table: it says where the voters of each eliminated
candidate go in the second round. The voters of the two finalists, the blank
voters and the abstainers of the first round keep their choice in every model. We
test nine models:

- H0a: the eliminated voters split like the whole electorate, abstainers included.
  This was our first baseline.
- H0b: they split like the people who voted, so nobody newly abstains. We added it
  after the second peer review.
- H1: each group votes for the finalist who is the closest to its candidate on the
  left-right scale.
- H1-soft: each group splits between the two finalists, and the closer one gets the
  bigger share.
- H2-abst and H2-blank: like H1, but when the candidate is at least one third of the
  scale away from both finalists, the group abstains or votes blank.
- H3(H1), H3(H2-abst) and H3(H2-blank): a share p of each group behaves like H0b and
  the rest follows H1 or H2. p is the only number we fit, on four elections, and we
  always test it on the fifth one.

The score of a model is the average gap, in percentage points (pp), between its
predicted second round and the observed one, computed area by area and weighted by
the registered voters. Lower means closer.

## Results

No single assumption explains every election. H1 has the lowest average gap over
the five elections (4.7 pp), but it beats H0b only in two of them, and most of its
advantage comes from 2002, where it scores 4.4 pp against 13.5 pp for H0b. If we set
2002 aside, H1 falls to rank 8 out of 9 and the best model is H0b (3.0 pp).

Some other results:

- The first baseline, H0a, is the worst model (8.7 pp), because it sends part of the
  eliminated voters to abstention. H0b, which only removes this effect, is closer in
  all five elections (5.1 pp).
- The distance threshold of H2 really matters in only one election: in 2002 both
  finalists were on the right of the scale, so H2 sends 29.9% of the registered
  voters to a non-vote, while most of them in fact voted.
- H3 does not help much. With the H2 rules the fitted p is between 0.77 and 1, so
  the model almost becomes H0b, and H3(H1) has an average gap of 5.6 pp, which is
  worse than H1 alone.

Because the data is made of totals, a model that fits well does not prove that
people really voted that way. All the tables, figures and the draft report are
generated by `make analysis`, in `reports/` and `docs/report/`.

## Repository structure

```text
site/            the website (Streamlit): one file per page in site/views/
backend/         the Python code: download, checks, cleaning, models and scores
data/            original file manifests, cleaned snapshots and the poll orders
notebooks/       the notebook that builds the left-right scale
reports/         generated results and figures
docs/            report templates; make analysis writes the report in docs/report/
tests/           automatic tests on the data, the models and the website
Makefile         the commands above
pyproject.toml   the project and its dependencies (locked in uv.lock)
```

AI helped with the code, the tests and the drafting. The project team is
responsible for the methodological choices, the collection of the poll orders and
the interpretation of the results.
