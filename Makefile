.PHONY: setup app acquire process evaluate bundle data check archive
setup:
	uv sync --locked --dev
app:
	uv run streamlit run site/app.py
acquire:
	uv run vote-transfer acquire --all-years
process:
	uv run vote-transfer process --all-years
evaluate:
	uv run vote-transfer evaluate --all-models --all-years
bundle:
	uv run vote-transfer bundle --all-years
# Full rebuild from the original Ministry files to the versioned snapshots.
data: acquire process evaluate bundle
check:
	uv run pytest -q
	uv run ruff check backend site tests
	uv run ruff format --check backend site tests
	uv run vote-transfer check-snapshots
# Tracked files only: no .venv, raw downloads or OS metadata.
archive:
	git archive --format=zip --prefix=vote-transfer/ -o vote-transfer-$$(git rev-parse --short HEAD).zip HEAD
