PY ?= .venv/bin/python

.PHONY: etl etl-all test lint migrate api bench
migrate:
	$(PY) db/migrate.py
etl:
	$(PY) -m pipeline.run
etl-all:
	$(PY) -m pipeline.run --all
test:
	$(PY) -m pytest -q
lint:
	$(PY) -m ruff check .
api:
	$(PY) -m uvicorn api.main:app --port 8000
bench:
	$(PY) -m api.bench
