# Development and repository decisions

## Boundaries

`site/` is the frontend. Do not add an `__init__.py` to it or import it as a Python
package: Python already has a standard-library module named `site`.
The app is launched by file path and imports the installed `vote_transfer` library.

`backend/vote_transfer/` is the backend package. Keep modelling and validation out
of the interface so the CLI, tests and future report can reproduce the same numbers.
A separate FastAPI service is unnecessary for this single-process application.

Four direct runtime dependencies are sufficient: Streamlit, pandas, PyArrow and
requests. Development adds pytest and Ruff. `uv.lock` and `.python-version` are
tracked; `.venv/` is not. Add dependencies only when an implemented feature needs them.

## Checks

`make check` runs offline tests and formatting/lint checks. Synthetic fixtures
exercise repeated candidate blocks, changing panel numbers, invalid vote totals,
missing territorial coverage, H0 mass conservation and Streamlit interactions.
They are not historical election data. A real-data run is a separate integration
check, documented in the quality report and validation notes.

The UI reads verified bundled aggregate snapshots on a clean clone; it shows an
empty state only when the selected data root has neither local nor bundled outputs. Its tests use Streamlit's
[AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
with synthetic temporary outputs and the shipped aggregate snapshots rather than
depending on local raw downloads. Bundled-data tests exercise all five years without network.

## Repository reorganisation (28 October 2026)

- `src/` → `backend/`, with editable-package configuration updated.
- Replaced the French placeholder `webapp/` with `site/app.py`.
- `Doc/` → `docs/references/archive/`; copied the two supplied PDFs into
  `docs/references/` under stable English filenames. Original source documents
  remain unchanged.
- `reports/` and `presentation/` → `docs/archive/` so they do not clutter the root.
- `old_data/` → `data/archive/legacy/`; no historical data were deleted.
- The previous placeholder interface is also retained locally in ignored
  `tmp/legacy_webapp/` during this migration. Git history retains its tracked version.

All authored documentation, code messages and UI text are English. Published
candidate names, original field names and source resource titles remain unchanged.

## AI assistance

AI assisted with repository restructuring, code, documentation and tests. Claims
about source coverage and model performance must remain traceable to real checks.
The project team owns methodological decisions, final interpretation and submission.


## Guided frontend

The Streamlit app presents four views: Start here, Explore results, Understand the
model, and Sources & limits. Navigation uses native controls and preserves the
selected election/area. Detailed tables, mathematical notation, provenance JSON
and reproduction commands are expandable rather than placed on arrival.

`site/styles.css` provides local editorial styling, responsive font sizes and
visible keyboard focus. No fonts, scripts or imagery are fetched externally.
The homepage mini-chart also exposes its numbers in an HTML table and gives its
stacked bars accessible descriptions. Exploratory charts include explicit value
labels, named series, tooltips and a downloadable table alternative.

`application/exploration.py` supplies registered-electorate summaries and weighted
model-error readings. The H0 algorithm and stored datasets are unchanged. The
100-voter example on the model page is explicitly illustrative, not historical data.

UI tests cover all four views for all five shipped elections without acquisition
network access, area navigation, missing-area resets, empty/corrupt data states and
Vega-Lite schema validation. Native Chrome inspection timed out during this
redesign; desktop/mobile visual verification remains outstanding.
