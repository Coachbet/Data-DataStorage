# Vote Transfer Lab

**Which assumptions about voter behaviour best explain second-round results in
French presidential elections (2002–2022)?**

A reproducible data workflow: it acquires the original Ministry of the Interior
files for **2002, 2007, 2012, 2017 and 2022**, validates and aggregates them by
reporting area, evaluates five families of assumptions (H0a, H0b, H1, H2, H3)
against the observed second rounds, and presents the results in a report and a
Streamlit app. Results describe **aggregate patterns, never individual
transfers**. The 2027 page is a **hypothetical scenario, not a forecast**.

> Candidate positions used by H1–H3 are **draft codes** until two team members
> have coded them independently. Every output states the coding status.

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
make data        # acquire -> process -> evaluate -> bundle, all five elections
make analysis    # every model result, figure, table, and the rendered report
make check       # tests, lint, format, processed-versus-bundled comparison
```

The same steps as explicit commands:

```bash
uv run vote-transfer acquire --all-years                 # about 293 MB, verified against pinned hashes
uv run vote-transfer process --all-years                 # raw -> interim -> processed tables
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
site/app.py                 Streamlit app: explore, H0a explained, compare models, 2027 scenarios
backend/vote_transfer/
  infrastructure/           Download with pinned hashes; parsers for the three file layouts
  application/processing.py Validation and the normalised areas/outcomes/options tables
  application/models.py     Every assumption as a transfer matrix; H3 leave-one-election-out
  application/evaluation.py The single scoring rule
  application/review.py     Blind coding sheet, coder agreement, candidate-table quality
  application/analysis.py   Generated tables, numbers and documents
  application/figures.py    Report figures (PNG and SVG)
  application/scenario.py   Hypothetical runoffs on the 2022 electorate
  cli.py                    The vote-transfer command
data/
  raw/official/<year>/      Original files (ignored) and their manifests (versioned)
  interim/, processed/      Generated tables (ignored)
  bundled/                  Small verified snapshots and predictions (versioned)
  reference/                Hand-coded candidate table, sources, review kit
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
  handoff.md                What is done, what humans must still do
tests/                      Offline tests on synthetic fixtures and the bundled snapshots
```

## How numbers reach the documents

No number in the report, findings, outline or storage comparison is typed by hand.
`vote-transfer analyse` writes `reports/results/numbers.json` and renders the
Markdown templates in `docs/templates/` from it. **Edit the templates, not the
rendered files.** A test fails if a committed result or document differs from a
fresh run.

## Candidate coding review

`data/reference/review/` contains a blind coding sheet and instructions for two
independent coders. `vote-transfer review-agreement --coder-a A.csv --coder-b B.csv`
reports percentage agreement, quadratic-weighted kappa, the confusion matrix and
the disagreements. After the review, `make evaluate bundle analysis` updates
every result.

## Limits to keep in mind

- **Aggregate inference.** Different individual behaviours can produce the same
  area totals. A model that fits is not an observed transfer.
- **Coverage.** The 2002 and 2007 files omit voters abroad and some overseas
  areas; their totals describe covered areas only.
- **Blank and invalid ballots** are one combined outcome in every election; the
  separate counts exist for 2017 and 2022 only.
- **Scope.** H4, H5 and two-dimensional positions were dropped; see
  `docs/methodology.md`.

Further reading: [methodology](docs/methodology.md), [data contracts](docs/data_dictionary.md),
[acquisition](docs/data_acquisition.md), [quality and cleaning](docs/data_quality_and_cleaning.md), [candidate table quality](docs/candidate_table_quality.md),
[validation record](docs/validation.md), [development notes](docs/development.md),
[scope](docs/project_scope.md). The [2 October acquisition note](docs/references/data-acquisition-note.pdf)
revises the [original proposal](docs/references/project-proposal.pdf).

AI assisted with code, tests and drafting. The project team owns the
methodological decisions, the candidate coding and the interpretation.
