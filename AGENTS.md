# Project conventions

- Write documentation, UI text, code comments and CLI messages in English.
- Read `docs/project_scope.md` and `docs/methodology.md` before changing research behaviour.
- Keep the Streamlit frontend in `site/` and reusable Python code in `backend/vote_transfer/`.
- Preserve original data. Write derived outputs only to interim/processed directories.
- Never treat aggregate model estimates as observed individual transfers or forecasts.
- Keep synthetic test data clearly separate from real election results.
- Use `uv sync --locked --dev` for setup and `make check` for verification.
- Do not commit raw/interim/processed datasets, virtual environments or secrets.
- Small verified aggregates in `data/bundled/` are the explicit exception for offline review.
  Regenerate them with `vote-transfer bundle`; retain checksums and provenance.
