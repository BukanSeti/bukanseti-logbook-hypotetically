.PHONY: install test lint refresh example

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

refresh:
	coradine refresh-references

example:
	coradine process examples/sample.csv --owner "Example Lion Air Pilot" --start-processing --allow-pdf-fallback
