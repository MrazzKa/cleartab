# ETL report - Phase 5 (Oct 14 milestone: ETL loads 5 hospitals end to end)

Command: `make etl` (= `python -m pipeline.run`), or `python -m pipeline.run CCN ...`. Stages per hospital:
registry load -> download (one conditional GET) -> CMS validator (cached by sha256) -> streaming parse to
parquet (cached by sha256) -> Feature 4 normalization -> COPY into `prices` -> completeness score and status
in `hospitals`. Every run appends to data/processed/etl_runs.csv. Postgres used for this report: a local
PostgreSQL 16.11 with pg_trgm (the Docker daemon was not running on this machine; docker-compose.yml is
provided for the team).

## Result: 19 hospitals from 13 systems loaded (target 5 from 3)
Prices are loaded for the 50 launch procedures (CPT and HCPCS labels); the completeness score covers the whole
file. Dropped rows are loaded too, with a `dropped:<reason>` flag, so they stay auditable; the API never shows
them. Flag counts over each whole file are in data/processed/f4_flag_log.csv. Four files were downloaded by a
team member in a browser (robots.txt blocks automated access) and read from data/raw/manual/ without any
network request.

| CCN | Hospital | System | Metro | Price rows loaded | Completeness | Status |
|---|---|---|---|---|---|---|
| 030085 | Northwest Medical Center (manual file) | Northwest Healthcare | Tucson | 10,449 | 91.2 | published |
| 030114 | Oro Valley Hospital (manual file) | Northwest Healthcare | Tucson | 10,430 | 91.0 | published |
| 030148 | Northwest Medical Center Sahuarita (manual file) | Northwest Healthcare | Tucson | 7,461 | 91.5 | published |
| 030064 | Banner UMC Tucson | Banner Health | Tucson | 5,343 | 98.4 | published |
| 030006 | Tucson Medical Center (manual file) | TMC Health | Tucson | 4,095 | 80.4 | published |
| 030011 | St. Joseph's Hospital (Tucson) | Carondelet (Tenet) | Tucson | 154 | 98.7 | published |
| 030010 | St. Mary's Hospital | Carondelet (Tenet) | Tucson | 152 | 98.7 | published |
| 030103 | Mayo Clinic Hospital (Phoenix) | Mayo Clinic | Phoenix | 108,322 | 94.8 | published |
| 030022 | Valleywise Health Medical Center | Valleywise Health | Phoenix | 7,736 | 88.1 | published |
| 030024 | St. Joseph's Hospital and Medical Center | Dignity Health | Phoenix | 6,064 | 96.9 | published |
| 030036 | Chandler Regional Medical Center | Dignity Health | Phoenix | 5,703 | 97.8 | published |
| 030065 | Banner Desert Medical Center | Banner Health | Phoenix | 4,431 | 98.3 | published |
| 030030 | Abrazo Central Campus | Abrazo (Tenet) | Phoenix | 1,523 | 96.2 | published |
| 030092 | HonorHealth Deer Valley | HonorHealth | Phoenix | 970 | 96.0 | published |
| 030038 | HonorHealth Scottsdale Osborn | HonorHealth | Phoenix | 970 | 96.1 | published |
| 030153 | East Valley ER & Hospital | Nutex | Phoenix | 156 | 100.0 | published |
| 030107 | Arizona Spine and Joint Hospital | USPI | Phoenix | 112 | 98.3 | published |
| 030152 | Exceptional Community Hospital - Maricopa | Exceptional Healthcare | Phoenix | 0 | 80.0 | not published (codes labelled CDM) |
| 030108 | The CORE Institute Specialty Hospital | Independent | Phoenix | 0 | 0 | not published (non-standard file) |

Totals in the database: 174,071 price rows, 19 source_files rows, 50 launch procedures, 12 payers.

### Memory on large files
The first Mayo load was killed by the kernel (out of memory, 7.2 GB resident on a 7.6 GB machine) in the
Feature 4 step, which read the 57.5 million-row table at once. normalize_file now processes 1 million-row
batches against small lookup tables; results for the other 14 hospitals are identical (flag log and coverage
compared line by line). Peak memory for the full 19-hospital run: 3.2 GB. The code frequency script was
changed the same way (6.9 GB to 2.1 GB, identical counts).

## Runtime (data/processed/etl_runs.csv)
| Run | Hospitals | Downloads | Total |
|---|---|---|---|
| 1 (21:26 UTC) | 14 | 13 unchanged (HTTP 304, files fetched in Phase 2), Valleywise downloaded (540 MB, 48 s) | 514 s |
| 2 (21:35 UTC) | 14 | 13 unchanged (304); Valleywise downloaded again because its portal sends no Last-Modified or ETag | 93 s |
| 3 (21:37 UTC) | 1 | Valleywise skipped after the size-only check was added | 15 s |
| 4 (21:42 UTC) | 14 | all 14 skipped; validator and parse cached by sha256 | 62 s |
| 5 (Oct 13, 01:03 UTC) | 15 incl. Mayo | all skipped (304); Mayo re-hashed locally (371 s) and normalized in batches (200 s) | 664 s |
| 6 (Oct 13, 01:53 UTC) | 4 manual files | read from data/raw/manual/, no network | 451 s |
| 7 (Oct 13, 02:12 UTC) | 19 | 14 unchanged (304), Valleywise by size, 4 manual | 638 s |

Slowest stages on a cold cache: Valleywise parse 90 s and validator 47 s; Banner files about 23 s validator
and 30 s parse each. Run 1 is not a fully cold run, because 13 files were already on disk from Phase 2. The
F3 target of a full refresh under 60 minutes is met for these 19 when files are unchanged; the 21.5 GB Mayo file took several hours to
download at 1 to 3 MB/s, so a refresh in which Mayo's file has changed will not meet 60 minutes. When it is
unchanged, the run takes about 11 minutes, mostly re-hashing the local copy.

## Request policy
One conditional GET per file per run (If-None-Match / If-Modified-Since); plus one robots.txt per host per
run. Phase 2 used HEAD + GET (two requests) before this was changed. Servers that send no validators
(Valleywise) are compared by size only, and the run log says so; `python -m pipeline.run --force` downloads
everything again.
