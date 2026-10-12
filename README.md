# ClearTab

ClearTab is a free, open-source web app that compares what hospitals in the Tucson and Phoenix (Arizona) metro areas charge for the same procedure.
It reads the machine-readable price files hospitals must publish under 45 CFR 180.50, normalizes them, and shows gross charge, discounted cash price and negotiated rate side by side.
Every number carries its source file URL, download time and methodology label, and hospitals that publish nothing usable are listed as "not published".
University of Arizona ISTA 498 senior capstone, Team Trace, Fall 2026. Faculty advisor: Dr. Lingyao Li.
The core product uses no machine learning; search is PostgreSQL full-text plus trigram matching.

## Run locally

```bash
docker compose up -d db                      # Postgres 16 with pg_trgm on localhost:5432
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export DATABASE_URL=postgresql://cleartab:cleartab@localhost:5432/cleartab
.venv/bin/python db/migrate.py               # apply migrations
.venv/bin/python -m pipeline.load_registry   # load data/processed/hospital_registry.csv
.venv/bin/python -m pipeline.run             # ETL: download, validate, parse, normalize, load
.venv/bin/uvicorn api.main:app --reload      # API on :8000
cd web && npm install && npm run dev         # web app
```

Tests: `.venv/bin/pytest` and `.venv/bin/ruff check .`; web: `npm run lint && npx tsc --noEmit`.

## License
MIT (see LICENSE). The proposal says "open source" without naming a license; MIT was chosen as the default.
