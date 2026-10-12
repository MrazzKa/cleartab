# ClearTab progress log

Each phase appends a summary of at most 15 lines.

## Phase 0 - Repository and project memory (2026-10-12)
- Monorepo created: pipeline/, db/, api/, web/ (Vite + React + TS), docs/, research/{registry,h1,h2,h3,accuracy_check}, data/raw (gitignored), data/processed.
- README, LICENSE (MIT; the proposal names no license), CONTRIBUTING, issue and PR templates, CI (ruff + pytest, eslint + tsc, migrations on a Postgres 16 service).
- docker-compose.yml with Postgres 16 and pg_trgm. Migrations 0001-0002: hospitals, source_files, procedures (full-text + trigram indexes), payers, payer_aliases, prices. Applied twice cleanly.
- hospital_registry.csv was not supplied; it was exported unchanged from the audit XLSX (46 rows: 8 Tucson, 38 Phoenix, 15 Banner). Loaded into hospitals: 39 with a direct file URL, 3 blocked by robots.txt, 4 with no URL.
- Local checks: ruff clean, pytest 2/2, eslint clean, tsc clean.
- Failed: gh CLI not installed and Docker daemon not running on this machine. Postgres ran as a user instance instead.
- Human: create the GitHub repository, protect main and open the milestone issues (done 2026-10-13).
