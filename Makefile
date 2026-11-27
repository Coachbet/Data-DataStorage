.PHONY: setup app acquire process scale evaluate bundle data analysis check archive
setup:
	uv sync --locked --dev
app:
	uv run streamlit run site/app.py
acquire:
	uv run vote-transfer acquire --all-years
process:
	uv run vote-transfer process --all-years
# The poll-based candidate scale: data/reference/polling_axes.csv -> candidate_scores.csv.
scale:
	cd notebooks && uv run jupyter nbconvert --to notebook --execute --inplace candidate_scale.ipynb
evaluate:
	uv run vote-transfer evaluate --all-models --all-years
bundle:
	uv run vote-transfer bundle --all-years
# Full rebuild from the original Ministry files to the versioned snapshots.
data: acquire process scale evaluate bundle
# Every model result, figure, table and rendered document, from processed/bundled data.
analysis: scale evaluate
	uv run vote-transfer bundle --all-years
	uv run vote-transfer analyse
check:
	uv run pytest -q
	uv run ruff check backend site tests
	uv run ruff format --check backend site tests
	uv run vote-transfer check-snapshots
# Tracked files only: no .git, .gitignore, .venv, raw downloads or OS metadata.
archive:
	git archive --format=zip --prefix=vote-transfer/ -o vote-transfer-$$(git rev-parse --short HEAD).zip HEAD ":(exclude)*.gitignore"
