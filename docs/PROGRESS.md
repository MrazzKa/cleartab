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

## Phase 2 - H1 parse test (2026-10-12)
- H1 rule copied into research/h1/REPORT.md before downloading. 15 hospitals attempted (11 system labels); 13 files downloaded once each (sha256 and size in data/processed/downloads.csv).
- Replacements logged: Northwest x2 (robots.txt) -> Exceptional, East Valley; Valleywise (portal dropped 2 GETs) -> CORE. Mayo (21.5 GB) still resuming at about 1 MB/s.
- Formats: 6 CMS JSON, 6 CMS CSV tall, 0 wide, 1 non-standard (CORE). All 12 template files are v3.0.0 and pass the CMS validator (CLI 1.10.8) with 0 errors (data/processed/h1_validator.csv).
- Streaming parser pipeline/parsers/cms.py (JSON via ijson, CSV tall and wide) -> one long table per hospital (data/raw/normalized/*.parquet). 13 pytest tests, fixtures cut from real files.
- H1 verdict: PROCEED. 11 of 15 attempted hospitals yield usable coded rows (>= 100 priced CPT/HCPCS/MS-DRG codes) across 7 systems; 9 of the 11 are non-Banner.
- 2026 elements: org NPI, attester, attestation present in 12/12; allowed-amount elements present wherever applicable; 0 of 12 files omit an applicable element. Most percent/algorithm records lack a median, but all of those report count 0. The "substantial share omit" half of H1 is not supported.
- 4 of 12 template files have no negotiated rates at all (Carondelet x2, East Valley, Exceptional). Exceptional labels CPT codes as "CDM" (not relabelled).
- Completeness score: equal weights 20 x 5, formula in REPORT.md; 11 hospitals >= 90. Limitation: the Table 10 components do not reward negotiated rates (Carondelet 98.7, Exceptional 80.0). PM and Dr. Li to decide.
- Outputs: h1_file_profile.csv, h1_required_elements.csv, payer_strings.csv (raw payer/plan with row counts).
- Human: manual downloads (MANUAL_DOWNLOADS.md, now 7 incl. Valleywise); decide on the score limitation; rerun `python -m pipeline.h1_profile 030103` when Mayo finishes.
