# French Presidential Vote Transfer

Reproducible data project studying how votes for candidates eliminated after the
first round of French presidential elections redistribute in the second round,
including abstention. The final interface will let users compare hypothetical
2027 finalists and explore estimated transfers by department.

## Research question

> How do voters of candidates eliminated in the first round of a French
> presidential election transfer their vote in the second round?

The project uses aggregate election results, so it estimates ecological flows;
it does not observe individual voter choices. Every result must therefore be
presented as an estimate with its assumptions and uncertainty.

## Repository layout

```text
.
|-- data/                  # raw, interim and processed data (large files ignored)
|-- Doc/                   # assignment, proposal and teacher feedback
|-- docs/                  # project decisions and data documentation
|-- presentation/          # final presentation sources and exported slides
|-- reports/               # report sources and generated figures
|-- src/vote_transfer/     # domain, application and infrastructure code
|-- tests/                 # automated tests
`-- webapp/                # Streamlit communication layer
```

The Python code follows a lightweight domain-driven design:

- `domain` contains election concepts and rules without framework dependencies;
- `application` coordinates use cases;
- `infrastructure` will contain APIs, files, databases and external adapters;
- `webapp` is the presentation adapter and depends on the application layer.

## Setup with uv

Install Python 3.12 and [`uv`](https://docs.astral.sh/uv/), then run:

```bash
uv sync --dev
uv run streamlit run webapp/Home.py
```

Inspect and acquire the documented sources with:

```bash
uv run python -m vote_transfer.infrastructure.collect --list
uv run python -m vote_transfer.infrastructure.collect --source core
uv run python -m vote_transfer.infrastructure.collect --source elections --download
```

The second command is a read-only simulation. A download only occurs when
`--download` is explicitly supplied. Every acquisition writes a provenance
manifest containing the source URL, retrieval time, byte count and SHA-256 hash.

Run the checks with:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Reproducibility rules

1. Keep immutable source files in `data/raw/` or document how to reacquire them.
2. Never modify raw data in place; write transformations to `interim/` or
   `processed/`.
3. Record provenance, retrieval dates, licences, schemas and known limitations.
4. Define every analytical measure before calculating it.
5. Keep observations separate from interpretations in the report and web app.

See [docs/project_scope.md](docs/project_scope.md) for the current scope and
[docs/data_dictionary.md](docs/data_dictionary.md) for operational definitions.
