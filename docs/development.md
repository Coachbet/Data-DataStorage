# Development and repository decisions

## Boundaries

`site/` is the frontend. Do not add an `__init__.py` to it or import it as a Python
package: Python already has a standard-library module named `site`.
The app is launched by file path and imports the installed `vote_transfer` library.

`backend/vote_transfer/` is the backend package. Keep modelling and validation out
of the interface so the CLI, tests and future report can reproduce the same numbers.
A separate FastAPI service is unnecessary for this single-process application.

Five direct runtime dependencies are sufficient: Streamlit, pandas, PyArrow,
requests and Matplotlib (added on 15 November 2026 for the report's static PNG and
SVG figures; the app's interactive charts still use Streamlit's Vega-Lite). Development adds pytest and Ruff. `uv.lock` and `.python-version` are
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
- `Doc/` → `docs/references/` and `reports/`, `presentation/` → `docs/archive/`;
  both folders were removed on 20 November 2026 (course documents are kept outside
  the repository).
- `old_data/` was moved to an ignored local folder on the machine that did the
  migration. It is not part of the repository or of any archive; nothing in the
  workflow reads it.
- The previous placeholder interface is also retained locally in ignored
  `tmp/legacy_webapp/` during this migration. Git history retains its tracked version.

All authored documentation, code messages and UI text are English. Published
candidate names, original field names and source resource titles remain unchanged.

## AI assistance

AI assisted with repository restructuring, code, documentation and tests. Claims
about source coverage and model performance must remain traceable to real checks.
The project team owns methodological decisions, final interpretation and submission.


## Frontend

The website is written like an academic paper. Its pages are listed once in
`site/nav.py` (number, title, anchors), which the sidebar, page headings and
cross-references all read. `site/app.py` builds the navigation from that list and
runs one module per page in `site/views/`. `site/data.py` reads the versioned
snapshots through the backend functions and recomputes every score live;
`site/ui.py` holds the shared layout pieces and the stylesheet. Fonts are vendored
in `site/assets/fonts/` with their licences and embedded in the page: nothing is
fetched from the network. On 26 November 2026 this site (first written in `paper/`)
replaced the earlier four-page site.

UI tests (`tests/test_site.py`) run every page on the bundled snapshots with HTTP
blocked and check that each one renders without an error.
