.PHONY: setup app acquire process bundle check
setup:
	uv sync --locked --dev
app:
	uv run streamlit run site/app.py
acquire:
	uv run vote-transfer acquire --year 2022
process:
	uv run vote-transfer process --year 2022
bundle:
	uv run vote-transfer bundle --all-years
check:
	uv run pytest -q
	uv run ruff check backend site tests
	uv run ruff format --check backend site tests
