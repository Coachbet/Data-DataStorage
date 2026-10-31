# Vote Transfer Lab

**Which assumptions about voter behaviour best explain second-round results in
French presidential elections (2002–2022)?**

A small Python library and a Streamlit frontend. The current implementation
acquires the original Ministry files for **2002, 2007, 2012, 2017 and 2022**,
validates both rounds,
builds department-level tables, and evaluates an explicit H0 baseline against
observed results. The app explores actual data; no demo figures are substituted.
The eventual 2027 feature will be a **simulation, not a forecast**.

## Quick start

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required.
From the repository root:

```bash
uv sync --locked --dev
uv run streamlit run site/app.py
```

Open <http://localhost:8501>. **No election-data download is needed.** The repository
includes verified department/reporting-area aggregates for all five elections in
`data/bundled/` (about 326 KB of dataset files in total). The app uses these on a
clean clone, or prefers complete local processed outputs when available.
Installation needs access to the Python package registry; subsequent data exploration
runs offline. No Git LFS, database server or external data hosting is needed.

To rebuild every dataset from the original source files (optional):

```bash
uv run vote-transfer acquire --all-years
uv run vote-transfer process --all-years
uv run vote-transfer bundle --all-years
```

Acquisition downloads about 293 MB once across the five elections. Existing files
are verified and reused. The files combining both rounds in 2002–2012 are downloaded
only once per year. Use `--year 2017` or `--year 2017 2022` for a smaller rebuild.
`bundle` explicitly refreshes the small versioned snapshots after processing; it
never includes raw or station-level data. Without either processed or bundled data,
the app displays setup instructions.

`uv sync` creates the local `.venv/` and installs the backend in editable mode.
You can alternatively activate it with `source .venv/bin/activate` and run
`vote-transfer` or `streamlit` directly. No credentials are required. To store
data elsewhere, export `VOTE_TRANSFER_DATA_DIR=/absolute/path/to/data` before
running the CLI or app. `.env` files are not loaded automatically.

## Repository structure

```text
site/app.py                 Streamlit frontend, in English
backend/vote_transfer/      Installable Python backend
  application/              Validation, aggregation, H0 and evaluation
  domain/                   Research definitions and source metadata types
  infrastructure/           Source adapters, downloads and original-file parser
  cli.py                    acquire / process / bundle command line interface
  config.py                 Shared paths and optional environment override
data/
  raw/official/<year>/         Original files and provenance manifest
  interim/<year>/             Normalised station turnout and candidate votes
  processed/<year>/           Results, H0 errors and quality report used by the app
  bundled/<year>/           Small versioned aggregates for immediate offline use
  reference/                Versioned manual candidate positions and source notes
  external/                 Local downloads for future external references
  archive/legacy/           Preserved old local datasets, excluded from Git
docs/                       Scope, methodology, data contracts and development notes
  references/               The two supplied project PDFs
  references/archive/       Earlier course/proposal documents, unchanged
  archive/                  Earlier report/presentation placeholders
tests/                      Offline processing, modelling, acquisition and UI checks
.streamlit/config.toml      Shared visual configuration, no secrets
pyproject.toml + uv.lock    Dependencies and reproducible environment
```

Streamlit calls the Python package directly: no separate HTTP service is needed.
Parquet is the initial storage format. Direct runtime dependencies are Streamlit,
pandas, PyArrow and requests. DuckDB and Plotly were removed because the current
workflow does not need them. Git ignores environments, secrets, caches and
large/generated datasets; small raw manifests and curated `data/bundled/` snapshots
and documented manual inputs in `data/reference/` are the explicit versioned exceptions.

## What is implemented

- Original 2002–2022 polling-station downloads resolved through the official dataset API,
  with source URLs, retrieval timestamps, sizes and SHA-256 hashes in
  `data/raw/official/<year>/manifest.json`.
- Strict parsing of repeated candidate blocks and stable candidate IDs across
  rounds (the Ministry's panel numbers change between rounds). Historical long-format
  imports count repeated turnout once and preserve missing blank/invalid splits as null.
- Checks for missing/duplicate keys, integer counts, turnout accounting,
  candidate totals, and matching territorial coverage between rounds.
- Department/reporting-area shares over **registered voters**, including
  abstention and a combined blank/invalid outcome.
- H0 predictions and a primary score averaging territorial errors with round-two
  registered-voter weights. The gap after pooling results is a separate diagnostic.
- A [manual candidate reference](data/reference/README.md): 61 candidacies with
  historical party labels, draft political families, a 1–7 scale and source notes.
  Cheminade's two positions remain unresolved. H0 does not use political scores.
- A guided English app: introduction, observed results, H0 explanation, and sources/limits.
- Year/area/round controls, labelled charts, data-driven readings, a glossary and CSV exports.
- Local styling and fonts; no external assets or election-data requests are needed.

The [2 October acquisition note](docs/references/data-acquisition-note.pdf)
explicitly revises the [original proposal](docs/references/project-proposal.pdf).
The current scope follows that revision: raw Ministry files are primary,
consolidated data are a validation reference, and media/socioeconomic variables
are out of scope. See [the scope and roadmap](docs/project_scope.md).

## Verification and development

```bash
uv run pytest -q
uv run ruff check backend site tests
uv run ruff format --check backend site tests
```

`make setup`, `make acquire`, `make process`, `make bundle`, `make app` and `make check` are
shortcuts. Tests use synthetic fixtures, temporary directories and the small shipped
aggregates, with no network or dependence on raw downloads. See [development notes](docs/development.md),
[acquisition details](docs/data_acquisition.md), [data contracts](docs/data_dictionary.md),
[H0 methodology](docs/methodology.md) and the [validation record](docs/validation.md).

**Coverage:** 2002 and 2007 omit some overseas territories and voters abroad.
Their combined totals are not full national totals. The app flags this limitation;
cross-year comparisons require matching geography.

Individual voter choices are unobserved. H0 is a transparent, provisional
baseline, not evidence that voters actually behave that way. H1–H5, cross-election
evaluation and the 2027 scenario interface remain to be implemented.
