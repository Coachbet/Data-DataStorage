# Paper site

A second Streamlit front end, written as an academic paper: introduction, data,
hypotheses (with animated flows and two playgrounds), results, exploration,
method and limits, and the report. It reads the same versioned snapshots and
backend as `site/`, changes none of them, and recomputes every score live (the
Method page checks it against `reports/results/model_comparison.csv`).

```bash
uv sync --locked --dev
uv run streamlit run paper/app.py
```

To show the final LaTeX report on the Report page, put the compiled PDF at
`paper/report.pdf`. Without it, the page shows the generated draft
`docs/report/report.md`.

To deploy on Streamlit Community Cloud, create a new app from this branch with
main file path `paper/app.py`. The existing app (`site/app.py`) is unaffected.
