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

## Phase 1 - Finish the registry (2026-10-12)
- Re-checked 7 unresolved rows from this machine (cms-hpt.txt, then price page): 3 resolved, 4 still need a human.
- Resolved: HonorHealth Tempe (file on price page, still missing from cms-hpt.txt); East Valley (audit URL now 404, new 2026-08 file on price page; cms-hpt.txt still lists an Oklahoma hospital); CORE (new 2026-09 CSVs replace the 2019 XLSX; cms-hpt.txt returns HTTP 404).
- Still blocked: TMC (robots.txt Disallow: /), City of Hope Phoenix (HTTP 403 to our downloader), AZOSH (site not reachable, TLS failure), Northwest x3 (robots.txt /Uploads/*). All 6 hospitals listed in MANUAL_DOWNLOADS.md.
- HEAD freshness for 39 reachable files: none older than 12 months by Last-Modified (oldest Banner UMC South 2026-03-04). HonorHealth HEAD reports 20 bytes (to verify on download); Mayo file is 21.5 GB, above the 2 GB design limit.
- research/registry/compliance_findings.md: 16 findings with URL and date.
- Incident: the first robots.txt checker (urllib.robotparser) ignored `*` wildcards, so one HEAD request (no body) went to each of the 3 Northwest file URLs. Replaced with an RFC 9309 matcher (pipeline/robots.py, 7 tests); not repeated.
- Proposal citation error found: "without barriers" is 45 CFR 180.50(d)(3), the .txt file is (d)(6), not (b)(3) and (d).
- Human: do the 6 manual downloads; read terms of use for the 8 hospitals still "Not checked".
