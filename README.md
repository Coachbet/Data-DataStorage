# Vote Transfer Lab

**Which assumptions about voter behaviour best explain second-round results in
French presidential elections (2002–2022)?**

A small Python library and a Streamlit frontend. The current implementation
acquires the original Ministry files for **2022**, validates both rounds,
builds department-level tables, and evaluates an explicit H0 baseline against
observed results. The app explores actual data; no demo figures are substituted.
The eventual 2027 feature will be a **simulation, not a forecast**.

## Quick start

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required.
From the repository root:

```bash
uv sync --locked --dev
uv run vote-transfer acquire --year 2022
uv run vote-transfer process --year 2022
uv run streamlit run site/app.py
```

Open <http://localhost:8501>. Acquisition downloads about 50 MB once; subsequent
runs verify and reuse the original files. The app itself makes no acquisition
requests. Without processed data it displays setup instructions.

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
  cli.py                    acquire / process command line interface
  config.py                 Shared paths and optional environment override
data/
  raw/official/2022/         Original files and provenance manifest
  interim/2022/             Normalised station turnout and candidate votes
  processed/2022/           Results, H0 errors and quality report used by the app
  external/                 Future documented reference/mapping tables
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
large/generated datasets; small raw provenance manifests remain versionable.

## What is implemented

- Original 2022 polling-station downloads resolved through the official dataset API,
  with source URLs, retrieval timestamps, sizes and SHA-256 hashes in
  `data/raw/official/2022/manifest.json`.
- Strict parsing of repeated candidate blocks and stable candidate IDs across
  rounds (the Ministry's panel numbers change between rounds).
- Checks for missing/duplicate keys, integer counts, turnout accounting,
  candidate totals, and matching territorial coverage between rounds.
- Department/reporting-area shares over **registered voters**, including
  abstention and a combined blank/invalid outcome.
- H0 predictions, unit errors and a registered-voter-weighted national comparison.
- An English app with year/territory/round controls, charts, CSV export and provenance.

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

`make setup`, `make acquire`, `make process`, `make app` and `make check` are
shortcuts. Tests use synthetic fixtures and temporary directories, with no network
or dependence on downloaded data. See [development notes](docs/development.md),
[acquisition details](docs/data_acquisition.md), [data contracts](docs/data_dictionary.md)
[H0 methodology](docs/methodology.md) and the [validation record](docs/validation.md).

Individual voter choices are unobserved. H0 is a transparent, provisional
baseline, not evidence that voters actually behave that way. H1–H5, cross-election
evaluation and the 2027 scenario interface remain to be implemented.
