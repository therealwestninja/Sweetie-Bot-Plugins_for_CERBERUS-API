.PHONY: bootstrap test lint tree seed-github

bootstrap:
	python -m pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

tree:
	python scripts/tree.py

seed-github:
	python scripts/github_seed.py --dry-run
