# ClearTab advisor data pack (2026-10-16)

Data pack for the meeting with Dr. Lingyao Li on 2026-10-16. Every file was produced by committed code
(`python -m research.advisor_pack`, then `--zip`) from the CSVs in `data/processed/` and the local parquet
files the pipeline writes. Nothing in it was edited by hand.

**Data date.** Hospital files were downloaded on 2026-10-12 and 2026-10-13. The dates the hospitals put
inside their files (`last_updated_on`) range from 2026-02-01 to 2026-09-25 (see `source_files.csv`). The payer
dictionary is the post-round-1 version of 2026-10-13 and is **provisional**: inter-rater round 1 reached 68%
(target 85%), round 2 is not scored yet, so H2 figures in `h2_tables/` are provisional too.

**Not included.** Raw hospital files (up to 21.5 GB each). Their URLs, sha256 and sizes are in
`source_files.csv`, so anyone can download the same files and check the hash. Several hospital systems
(Banner, HonorHealth, Dignity, Tenet, Mayo) restrict reproduction in their website terms, so please do not
post this pack publicly.

## Files
| File | Rows | What it is |
|---|---|---|
| `hospitals.csv` | 46 | Registry: the 46 Tucson and Phoenix hospitals in the project registry (from the team's audit), with address, phone, how its file was found, robots.txt and terms flags, and (for the 19 in the H1 sample) the completeness score and its 5 components (C1-C5, 20 points each). |
| `source_files.csv` | 19 | One row per hospital file: URL, sha256, size, format, CMS schema version, the file's own date, CMS validator result (errors, warnings), download note. |
| `prices_launch_procedures.csv` | 174,071 | Every normalized row for the 50 launch procedures, from 17 hospitals (the 2 hospitals without usable codes have none). Columns: hospital, metro, code, procedure name, setting, payer canonical, raw payer, raw plan, price type, amount, methodology label, flags, source URL. Same rows as the `prices` table behind the search API. Rows dropped by the F4 rules are kept here with `drop_reason` (796 rows) so you can see them. |
| `payer_aliases.csv` | 2,502 | Full payer dictionary: raw payer + raw plan -> canonical insurer and plan type, with method (alias table, regex, network contract), confidence (high, medium), note and row count. |
| `h1_tables/` | | Tables behind research/h1/REPORT.md (copy included): file profile with C1-C5, 2026 required elements per file, validator output, download manifest, code frequency, launch procedure selection, robots.txt snapshots; completeness score options (completeness_options.md and .csv). |
| `h2_tables/` | | Tables behind research/h2/REPORT.md (copy included): H2 ratio per procedure and metro (main and payer-rule sensitivity run), payer coverage per hospital, F4 flag log, raw payer strings, launch procedures, inter-rater round 1 files, score and labeling guide; the follow-up for this meeting: advisor_followup.md (H2 with CIs, per metro, subsampling, exploratory factors, two charts) and coverage_followup.md (coverage with clustered CIs, Mayo sensitivity) with their CSVs and hospital_context.csv. |
| `samples/` | | Parsing check by eye, see below. `samples/index.csv` lists per hospital how many rows were sampled and matched. |

Key columns in `prices_launch_procedures.csv`:
- `price_type`: gross, cash, negotiated_dollar, negotiated_percent, negotiated_algorithm, allowed_median,
  allowed_p10, allowed_p90, allowed_count (CY 2026 allowed-amount elements).
- `methodology_label`: fixed dollar, percent of charges, per diem, algorithm. `headline_ok` is true only for
  fixed dollar rows that survived the F4 rules; only these may be shown as a headline price.
- `drop_reason`: under_1_dollar, above_gross, unparseable (row excluded from all analyses).
- `check_flag`: no_gross_to_check, gross_from_code (kept, but the "above gross" rule could not use the item's
  own gross).
- `payer_canonical` "other" means the plan did not map to one of the 11 named insurers ("plan not matched" in
  the product).

## samples/
For each of the 19 hospitals: 50 records drawn at random from the raw file (reservoir sampling over the whole
file in one streaming pass, seed `20261016-<CCN>`, so the draw is reproducible).
- `<ccn>_raw.csv`: the raw records as column/value pairs (non-empty cells only; a wide CSV row has hundreds
  of empty payer columns). `record` is the line number in the CSV, or the item and charge index in a JSON file.
- `<ccn>_normalized.csv`: the rows the pipeline stored for the same records (joined on `sample_id`), with
  canonical payer, methodology label, drop reason and flags. Identical repeated rows are shown once.
- `found_in_pipeline_output` = False marks a parsed value that is missing from the pipeline output. There
  are 8 such rows (Banner UMC Tucson 2, HonorHealth Deer Valley 2, TMC 2, Mayo 2), all gross or cash. Cause: in tall
  CSV files the parser keeps gross and cash once per (code, description, setting, billing class, modifiers),
  but some files list two chargemaster lines with the same key and different prices (for example HonorHealth
  CBC 85025 at $23 and $281). Only the first is kept. Affected launch-procedure keys: HonorHealth Deer Valley 7
  of 91, HonorHealth Osborn 7 of 91, TMC 2 of 163, Mayo 1 of 140, Banner, Valleywise, East Valley,
  Exceptional 0. Not fixed
  yet; reported to the team.
- CORE (non-standard layout) and Exceptional (codes labelled CDM) show raw rows; CORE has no normalized rows.

## Pipeline in 10 lines
1. Registry: 46 Tucson and Phoenix hospitals (base list: CMS Hospital General Information), each file found
   through the hospital's cms-hpt.txt, else its price transparency page; fallbacks logged.
2. Download: one request per file per run, robots.txt respected, descriptive User-Agent; blocked files were
   downloaded by a team member by hand. sha256 and size recorded.
3. Validation: official CMS validator (hpt-validator-cli 1.10.8, data dictionary 3.0.0) on every template file.
4. Parsing: streaming parser for CMS JSON (ijson), CSV tall and CSV wide; one long table, one row per code,
   setting, payer, plan and price type. Bad values are flagged, never fixed.
5. Payer matching: deterministic rules and an alias table map raw payer + plan strings to 11 Arizona insurers
   or "other"; two-rater check (85% target) before the dictionary is accepted.
6. F4 rules: drop rates under $1 and negotiated rates above the gross charge; label methodology; only fixed
   dollar rows can be a headline price.
7. Completeness (F5): 5 components x 20 points (file found, schema valid, share of coded rows, share with a
   dollar or allowed amount, 2026 elements present), computed over the whole file.
8. Load: launch-procedure rows into PostgreSQL 16 (`prices`), with source URL and retrieval time on every row.
9. H1 and H2 scripts read the same outputs (research/h1, research/h2).
10. This pack: `python -m research.advisor_pack --zip` (tables, samples and zip; the Mayo sample pass reads
    the 21.5 GB file once).
