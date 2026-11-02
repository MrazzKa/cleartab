# ClearTab

ClearTab helps people in Arizona check a medical bill. It compares the bill with the insurer's explanation of
benefits (EOB), with federal billing rules, and with the prices the hospital itself published, then explains what
looks wrong, what to ask, and whether the person may qualify for the hospital's financial assistance.

- **Check a bill** (`billcheck/`): a deterministic rule engine. EOB arithmetic, bill against EOB, duplicate
  charges, CMS medically unlikely edits (units), CMS NCCI code pairs, the allowed amount against the hospital's
  published rate for the insurer, self-pay charges against the published cash price, and No Surprises Act
  protections (emergency care, air and ground ambulance, good faith estimate disputes). Every finding names its
  source. A dispute letter and phone script are built from the findings; personal details are filled in the
  browser only.
- **Help paying** (`billcheck/assistance.py`, `data/processed/assistance_policies.json`): financial assistance
  policies of eight Arizona health systems, read from their own documents, and the 2026 HHS poverty guidelines.
- **Look up a price**: what 19 Tucson and Phoenix hospitals published for 50 common procedures (machine-readable
  files required by 45 CFR 180.50), with the source file URL and download time for every number.

No accounts, nothing stored: bill and income data are used for one answer and never logged. No language model
produces a price or a finding. University of Arizona ISTA 498 senior capstone, Team Trace, Fall 2026. Faculty
advisor: Dr. Lingyao Li. Plan: docs/PLAN_V2.md.

## Run locally

```bash
docker compose up -d db                      # Postgres 16 with pg_trgm on localhost:5432
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export DATABASE_URL=postgresql://cleartab:cleartab@localhost:5432/cleartab
.venv/bin/python db/migrate.py               # apply migrations
.venv/bin/python -m pipeline.load_registry   # load data/processed/hospital_registry.csv
.venv/bin/python -m pipeline.run             # ETL: download, validate, parse, normalize, load
.venv/bin/python -m billcheck.fetch_reference  # CMS MUE tables into data/raw/reference (PTP: see MANUAL_DOWNLOADS.md)
.venv/bin/python -m billcheck.build_ptp       # after the PTP zips are in data/raw/manual/ncci_ptp
.venv/bin/uvicorn api.main:app --reload      # API on :8000
cd web && npm install && npm run dev         # web app; /api is proxied to :8000 (CLEARTAB_API to change)
```

Tests: `.venv/bin/pytest` and `.venv/bin/ruff check .`; web: `npm run lint && npx tsc --noEmit`.

## License
MIT (see LICENSE). The proposal says "open source" without naming a license; MIT was chosen as the default.
