.PHONY: lint lint-imports lint-ruff lint-mypy

lint: lint-ruff lint-mypy lint-imports

lint-ruff:
	ruff check .

lint-mypy:
	mypy .

lint-imports:
	lint-imports --cache-dir .cache/import_linter_cache
