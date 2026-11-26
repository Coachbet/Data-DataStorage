# Vote Transfer Lab

**Which assumptions about voter behaviour best explain second-round results in
French presidential elections (2002–2022)?**

A reproducible data workflow: it acquires the original Ministry of the Interior
files for **2002, 2007, 2012, 2017 and 2022**, validates and aggregates them by
reporting area, evaluates five families of assumptions (H0a, H0b, H1, H2, H3)
against the observed second rounds, and presents the results in a report and a
Streamlit app. Results describe **aggregate patterns, never individual
transfers**.

> H1–H3 place candidates on a **poll-based scale**: the left-to-right orders that
> polling institutes publish in their reports (22 polls, 2002–2022, collected by us
> in `data/reference/polling_axes.csv`), turned into a 0–1 score by
> `notebooks/candidate_scale.ipynb`. The earlier hand-coded 1–7 scale is kept only
> as a comparison.

## Quick start

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required. From the repository root:

```bash
uv sync --locked --dev
uv run streamlit run site/app.py
```

Open <http://localhost:8501>. **No download is needed.** The repository includes
verified aggregates for all five elections and every model's predictions in
`data/bundled/`. Installation needs the Python package registry once; everything
else runs offline.

## Rebuild everything

```bash
make data        # acquire -> process -> scale -> evaluate -> bundle, all five elections
make analysis    # the candidate scale, every model result, figure, table and document
make check       # tests, lint, format, processed-versus-bundled comparison
```

The same steps as explicit commands:

```bash
uv run vote-transfer acquire --all-years                 # about 293 MB, verified against pinned hashes
uv run vote-transfer process --all-years                 # raw -> interim -> processed tables
make scale                                               # polling_axes.csv -> candidate_scores.csv
uv run vote-transfer evaluate --all-models --all-years   # one long predictions table
uv run vote-transfer bundle --all-years                  # refresh the versioned snapshots
uv run vote-transfer analyse                             # reports/ and rendered documents
uv run vote-transfer crosscheck --year 2022              # optional: compare with published totals
```

`make analysis` works on a fresh clone without `make data`: it uses the bundled
snapshots. `make archive` builds a zip of tracked files only (`git archive`).
To store data elsewhere, export `VOTE_TRANSFER_DATA_DIR=/absolute/path/to/data`.
No credentials are required and `.env` files are not loaded.

## Where things are

```text
site/app.py                 Streamlit app entry: page setup, navigation, sidebar, pager
site/nav.py                 Table of contents: every page, section number and anchor
site/ui.py, site/data.py    Shared layout and stylesheet; data access through the backend
site/views/                 One module per page (introduction, data, hypotheses, results, ...)
docs/design/                Design audit, brief and verification notes (screenshots: capture.py)
backend/vote_transfer/
  infrastructure/           Download with pinned hashes; parsers for the three file layouts
  application/processing.py Validation and the normalised areas/outcomes/options tables
  application/models.py     Every assumption as a transfer matrix; H3 leave-one-election-out
  application/evaluation.py The single scoring rule
  application/positions.py  Loads and checks the poll-based scale and the 1–7 comparison
  application/review.py     Quality checks on the hand-coded 1–7 comparison table
  application/analysis.py   Generated tables, numbers and documents
  application/figures.py    Report figures (PNG and SVG)
  cli.py                    The vote-transfer command
data/
  raw/official/<year>/      Original files (ignored) and their manifests (versioned)
  interim/, processed/      Generated tables (ignored)
  bundled/                  Small verified snapshots and predictions (versioned)
  reference/                Collected poll orders, the poll-based scale, the 1–7 comparison table
notebooks/
  candidate_scale.ipynb     Builds the poll-based scale (run with `make scale`)
reports/
  results/                  Generated CSV/JSON, numbers.json, findings.md
  figures/                  Generated figures
docs/
  report/report.md          Report draft, rendered from docs/templates/report.md
  templates/                Templates whose numbers come from reports/results/numbers.json
  methodology.md            Exact model definitions and evaluation
  data_dictionary.md        Table contracts
  storage_comparison.md     Parquet compared with SQLite/PostgreSQL and DuckDB
  response_to_reviews.md    Every review comment and what we did
tests/                      Offline tests on synthetic fixtures and the bundled snapshots
```

## How numbers reach the documents

No number in the report, findings, outline or storage comparison is typed by hand.
`vote-transfer analyse` writes `reports/results/numbers.json` and renders the
Markdown templates in `docs/templates/` from it. **Edit the templates, not the
rendered files.** A test fails if a committed result or document differs from a
fresh run.

## Candidate positions

`data/reference/polling_axes.csv` has one row per poll: institute, fieldwork
dates, client, source link and the candidates in left-to-right order. The
notebook gives each candidate an evenly spaced position from 0 to 1 in each poll,
averages it across institutes, and sets aside candidates it cannot place
(Cheminade, and anyone whose positions differ by more than 0.4 between
institutes). After editing the polls, run `make analysis`: a test fails if the
scale is not rebuilt.

## Limits to keep in mind

- **Aggregate inference.** Different individual behaviours can produce the same
  area totals. A model that fits is not an observed transfer.
- **Coverage.** The 2002 and 2007 files omit voters abroad and some overseas
  areas; their totals describe covered areas only.
- **Blank and invalid ballots** are one combined outcome in every election; the
  separate counts exist for 2017 and 2022 only.
- **The scale is an order.** Within a poll, candidates are evenly spaced whatever
  their real ideological gap; 2002 rests on one institute.
- **Scope.** H4, H5, two-dimensional positions and the 2027 scenario were dropped;
  see `docs/methodology.md`.

Further reading: [methodology](docs/methodology.md), [data contracts](docs/data_dictionary.md),
[acquisition](docs/data_acquisition.md), [quality and cleaning](docs/data_quality_and_cleaning.md), [candidate table quality](docs/candidate_table_quality.md),
[validation record](docs/validation.md), [development notes](docs/development.md),
[scope](docs/project_scope.md).

AI assisted with code, tests and drafting. The project team owns the
methodological decisions, the collection of the poll orders and the interpretation.
