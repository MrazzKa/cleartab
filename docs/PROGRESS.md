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

## Phase 3 - Launch procedure list (2026-10-12)
- Source list: 70 CMS shoppable services (84 FR 65524 Table 3, from federalregister.gov) + all codes in the 11 usable H1 files (data/processed/code_frequency.csv, 20,666 codes).
- CPT and HCPCS counted as one system (HonorHealth labels CPT codes "HCPCS"); labels kept as published.
- Rules written in pipeline/select_procedures.py; 50 picked: imaging 15, laboratory 15, endoscopy 8, outpatient surgery 12. 42 are CMS shoppable codes, 8 most-published.
- 47 of 50 are published by >= 8 of 11 hospitals; 3 endoscopies by 7 (no other endoscopy reaches 8).
- Plain names, 2-4 synonyms and one-line descriptions written for all 50 (data/processed/procedure_text.csv); loaded into procedures (is_launch = true); full-text + trigram search works ("knee mri" -> 73721).
- Per hospital: 50/50 at HonorHealth x2, St. Joseph's Phoenix, Abrazo Central; 47-49 at Chandler, Banner x2, East Valley; 30 Carondelet x2; 22 AZ Spine and Joint; 0 Exceptional (codes labelled CDM).
- Excluded and why: listed in research/procedures/README.md (E&M, OB delivery, inpatient DRGs, cancer surgery, pediatric, < 8 hospitals).
- Human: a clinician or Dr. Li should read the 50 plain names; reading level not measured with a tool.

## Phase 4 - Normalization and payer matching, H2 groundwork (2026-10-12)
- F4 targets and the H2 rule copied into research/h2/REPORT.md first. Canonical list: 11 insurers + "other"; AHCCCS plans from the AHCCCS Population by Contractor report (Sep 2026).
- Payer dictionary (data/processed/payer_aliases.csv): 227 raw strings (target 150), deterministic rules only; 217 high, 10 medium confidence; all provisional.
- Row coverage by canonical insurers: 75.2% overall (target 60%); per hospital 58.9% (Banner UMC Tucson, below target) to 100%.
- Outlier rules: 74,323 rows dropped above gross, 15,561 under $1; 1,116,757 negotiated rows have no gross to check (flagged, kept). Log: data/processed/f4_flag_log.csv.
- Provisional H2: median highest-to-lowest ratio 2.81 (50 procedures, Phoenix only, 7 hospitals); same-insurer sensitivity 3.33. Cash below median negotiated: 12 of 50 procedures (24%). Tucson cannot be measured (1 hospital with negotiated rates).
- IRR: 200 strings sampled (seed 20261012), rater files, labeling guide and irr_score.py ready; not filled, no agreement estimated.
- Human: two raters (suggest Timur and Artyom) label 200 rows independently, about 1-1.5 hours each, then run irr_score.py and resolve disagreements together (about 30 minutes). Spot-check the top surgical ratios in the source files.

## Phase 5 - ETL loads hospitals end to end (2026-10-12)
- One command: `make etl` / `python -m pipeline.run` (registry -> download -> validator -> parse -> F4 -> prices -> completeness). Docs: docs/etl_report.md.
- Loaded 14 hospitals from 9 systems (target 5 from 3): 33,991 price rows for the 50 launch procedures, 14 source_files; 12 published, 2 not published (Exceptional, CORE).
- Re-runs skip unchanged files: conditional GET (HTTP 304) for 13 files; Valleywise (no Last-Modified/ETag) by size, logged. Validator and parse cached by sha256. Run times: 514 s (first), 62 s (all cached).
- Downloader now makes one request per file per run (F3); Phase 2 used HEAD + GET.
- Correction to Phases 2-4: Valleywise downloaded on the 3rd attempt. H1 now 12 of 15 usable (8 systems); launch list re-selected under the same rules (77065, 66984 replace 72114, 10060; 44 CMS + 6, all >= 8 hospitals); dictionary 327 strings, coverage 72.6% (Valleywise 68.2%, Banner UMC Tucson 58.9% below 60%); provisional H2 median ratio 2.81 (40/50 >= 2), cash below median negotiated 7/50 (14%). Reports updated.
- Mayo (21.5 GB) still downloading; not loaded. Human: run `python -m pipeline.run 030103` and `python -m pipeline.h1_profile 030103` when data/processed/downloads.csv shows it ok.

## Phase 6 - Search API and screen specification (2026-10-12)
- FastAPI (api/main.py): GET /search?q=&plan=&zip= (best-matching launch procedure via full-text + pg_trgm; up to 10 hospitals in the user's metro, sorted by applicable price; gross, cash, negotiated or allowed range with methodology labels; completeness; city; straight-line distance; provenance), GET /procedures/suggest, GET /plans. Logs keep the path only (no procedure or ZIP).
- Latency (api/bench.py, 500 mixed requests over 14 hospitals / 33,991 price rows): search p95 9.6 ms over HTTP, 11.9 ms in-process (target 500 ms); suggest p95 4.9 ms (target 150 ms). Must be re-measured when more hospitals are loaded.
- ZIP centroids: 2020 ZCTA internal points for 417 AZ ZCTAs from Census TIGERweb (the gazetteer on www2.census.gov is disallowed by its robots.txt when read strictly per RFC 9309). Hospital phones and addresses from CMS Hospital General Information; 37 of 46 geocoded by the Census Geocoder, the rest at their ZIP centroid (flagged in hospital_geo.csv).
- docs/results_screen_spec.md, web/wireframes/results.html (grayscale, 5 real results, explainer, call summary). Explainer 91 words, Flesch-Kincaid 7.2; procedure descriptions rewritten so none is above grade 8 (mean 4.7).
- research/h3/study_plan_draft.md (5 tasks, between-subjects, measures, recruitment, power note: 39 per arm for 50% vs 80%); research/accuracy_check/plan.md + phone_check.csv (10 pairs, 10 hospitals, both metros).
- Data issue for a human: CMS lists CCN 030037 (registry: HonorHealth Tempe) at 1800 E Van Buren St, Phoenix.
- Tests: 20 passing (pytest), ruff clean.

## FINAL - Team summary (2026-10-12)
- docs/WEEK8_SUMMARY.md written: per-phase status, key numbers, 10 open human tasks, 5-sentence paragraph for Dr. Li.
- Branches: main (Phase 0) <- pipeline/phase1-registry <- ... <- api/phase6-search (stacked, one per phase); one PR per phase.
- Still running at the time of writing: Mayo (21.5 GB) validation and parse in pipeline.run (log: data/raw/mayo_etl.log).

## Addendum - Mayo loaded, repository published (2026-10-13)
- Mayo (21.5 GB, 57.5 million rows) validated (0 errors), parsed and loaded: 109,424 price rows, completeness 94.8. H1 now 13 of 15 usable (9 systems); Mayo is the only file with records missing 2026 elements (11,886).
- Out-of-memory fix: F4 normalization and the code frequency script now stream in batches (peak 3.1 GB; identical results for the other hospitals).
- Launch list under the same rules: 66821 replaces 10140 (45 CMS + 5). Dictionary 2,391 strings; coverage 72.6% without Mayo, 8.6% with Mayo (Mayo 3.0%). H2 unchanged at 2.81; cash below median negotiated 5 of 50.
- Database: 15 hospitals, 142,727 price rows; search p95 18.7 ms over HTTP.
- GitHub: public repo MrazzKa/cleartab, 14 issues, 6 stacked PRs. Branch protection pending GitHub Education; no CI run has been created yet.
