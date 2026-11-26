# Website

The Streamlit website of the project, written like an academic paper:
introduction, data, hypotheses (with animated flows and two playgrounds),
results, exploration, method and limits, and the report. It reads the versioned
snapshots (`data/bundled`, `data/reference`, `reports/results`) and the backend,
writes nothing, and recomputes every score live (the Method page checks it
against `reports/results/model_comparison.csv`).

```bash
make setup   # uv sync --locked --dev
make app     # uv run streamlit run site/app.py
```

To show the final LaTeX report on the Report page, put the compiled PDF at
`site/report.pdf`. Without it, the page shows the generated draft
`docs/report/report.md`.

To deploy on Streamlit Community Cloud, use the main file path `site/app.py`.

| File | Role |
|---|---|
| `app.py` | Entry point: page setup, navigation, sidebar, pager, footer |
| `nav.py` | Table of contents: every page, section number and anchor |
| `ui.py` | Shared layout pieces and the stylesheet |
| `data.py` | Data access, built on the backend functions |
| `views/` | One module per page |
| `assets/fonts/` | Embedded Source Sans 3 and Source Serif 4 (OFL licences) |
