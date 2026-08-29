.PHONY: install test lint fix api

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

fix:
	ruff check . --fix

api:
	uvicorn services.api.main:app --reload
