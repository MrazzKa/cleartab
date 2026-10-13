# ETL report - Phase 5 (Oct 14 milestone: ETL loads 5 hospitals end to end)

Command: `make etl` (= `python -m pipeline.run`), or `python -m pipeline.run CCN ...`. Stages per hospital:
registry load -> download (one conditional GET) -> CMS validator (cached by sha256) -> streaming parse to
parquet (cached by sha256) -> Feature 4 normalization -> COPY into `prices` -> completeness score and status
in `hospitals`. Every run appends to data/processed/etl_runs.csv. Postgres used for this report: a local
PostgreSQL 16.11 with pg_trgm (the Docker daemon was not running on this machine; docker-compose.yml is
provided for the team).

## Result: 14 hospitals from 9 systems loaded (target 5 from 3)
Prices are loaded for the 50 launch procedures (CPT and HCPCS labels); the completeness score covers the whole
file. Dropped rows are loaded too, with a `dropped:<reason>` flag, so they stay auditable; the API never shows
them. Flag counts are over the whole file (data/processed/f4_flag_log.csv).

| CCN | Hospital | System | Price rows loaded | Completeness | Status | Flags over whole file |
|---|---|---|---|---|---|---|
| 030022 | Valleywise Health Medical Center | Valleywise Health | 7,714 | 88.1 | published | above_gross 58,923; under_1_dollar 116,171; gross_from_code 37,268; no_gross_to_check 651,623 |
| 030024 | St. Joseph's Hospital and Medical Center | Dignity Health | 6,112 | 96.9 | published | above_gross 1,811; under_1_dollar 1,627; no_gross_to_check 114,671 |
| 030036 | Chandler Regional Medical Center | Dignity Health | 5,861 | 97.8 | published | above_gross 980; under_1_dollar 1,978; no_gross_to_check 123,782 |
| 030064 | Banner UMC Tucson | Banner Health | 5,521 | 98.4 | published | above_gross 26,347; under_1_dollar 1,084; gross_from_code 7,908; no_gross_to_check 107,494 |
| 030065 | Banner Desert Medical Center | Banner Health | 4,734 | 98.3 | published | above_gross 34,306; under_1_dollar 937; gross_from_code 4,411; no_gross_to_check 106,814 |
| 030030 | Abrazo Central Campus | Abrazo (Tenet) | 1,522 | 96.2 | published | above_gross 148; under_1_dollar 4,502; gross_from_code 3; no_gross_to_check 262,241 |
| 030092 | HonorHealth Deer Valley | HonorHealth | 974 | 96.0 | published | above_gross 5,440; under_1_dollar 2,263; gross_from_code 50,855; no_gross_to_check 198,214 |
| 030038 | HonorHealth Scottsdale Osborn | HonorHealth | 974 | 96.1 | published | above_gross 5,287; under_1_dollar 2,263; gross_from_code 50,834; no_gross_to_check 197,461 |
| 030153 | East Valley ER & Hospital | Nutex | 156 | 100.0 | published | under_1_dollar 65 |
| 030011 | St. Joseph's Hospital (Tucson) | Carondelet (Tenet) | 154 | 98.7 | published | under_1_dollar 412 |
| 030010 | St. Mary's Hospital | Carondelet (Tenet) | 152 | 98.7 | published | under_1_dollar 410 |
| 030107 | Arizona Spine and Joint Hospital | USPI | 117 | 98.3 | published | above_gross 4; no_gross_to_check 6,080 |
| 030152 | Exceptional Community Hospital - Maricopa | Exceptional Healthcare | 0 | 80.0 | not published (codes labelled CDM) | under_1_dollar 20 |
| 030108 | The CORE Institute Specialty Hospital | Independent | 0 | 0 | not published (non-standard file) | - |

Totals in the database: 33,991 price rows, 14 source_files rows, 50 launch procedures, 12 payers.
Mayo Clinic (030103) is not in this run: its 21.5 GB download was still in progress in another process, and
running the ETL on it would have overwritten the partial file.

## Runtime (data/processed/etl_runs.csv)
| Run | Hospitals | Downloads | Total |
|---|---|---|---|
| 1 (21:26 UTC) | 14 | 13 unchanged (HTTP 304, files fetched in Phase 2), Valleywise downloaded (540 MB, 48 s) | 514 s |
| 2 (21:35 UTC) | 14 | 13 unchanged (304); Valleywise downloaded again because its portal sends no Last-Modified or ETag | 93 s |
| 3 (21:37 UTC) | 1 | Valleywise skipped after the size-only check was added | 15 s |
| 4 (21:42 UTC) | 14 | all 14 skipped; validator and parse cached by sha256 | 62 s |

Slowest stages on a cold cache: Valleywise parse 90 s and validator 47 s; Banner files about 23 s validator
and 30 s parse each. Run 1 is not a fully cold run, because 13 files were already on disk from Phase 2. The
F3 target of a full refresh under 60 minutes is met for these 14; the 21.5 GB Mayo file alone took several
hours to download at 1 to 3 MB/s, so a refresh that includes Mayo will not meet 60 minutes unless the file is
unchanged (one conditional GET) or the transfer is faster.

## Request policy
One conditional GET per file per run (If-None-Match / If-Modified-Since); plus one robots.txt per host per
run. Phase 2 used HEAD + GET (two requests) before this was changed. Servers that send no validators
(Valleywise) are compared by size only, and the run log says so; `python -m pipeline.run --force` downloads
everything again.
