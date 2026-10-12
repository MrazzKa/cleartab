# ClearTab - Weeks 7 and 8 catch-up summary (as of 2026-10-12)

Plain-English summary of the catch-up session against the signed proposal (Table 14 milestones through
Oct 14). Every number below comes from committed code and CSVs; the phase logs are in docs/PROGRESS.md.

## What is done, by phase
| Phase | Done | Main outputs |
|---|---|---|
| 0 Repository | Monorepo, README, MIT license, CONTRIBUTING, templates, CI, docker-compose, migrations, registry loader | `db/migrations/`, `.github/workflows/ci.yml` |
| 1 Registry | 7 open rows re-checked, freshness HEAD for 39 files, 16 compliance findings | `research/registry/compliance_findings.md`, `MANUAL_DOWNLOADS.md` |
| 2 H1 parse test | 15 hospitals attempted, CMS validator on every file, streaming parser, completeness score | `research/h1/REPORT.md`, `data/processed/h1_*.csv` |
| 3 Launch procedures | 50 procedures with plain names, synonyms and descriptions, loaded and searchable | `research/procedures/README.md`, `data/processed/procedures.csv` |
| 4 Normalization | Payer dictionary, outlier and methodology rules, coverage, provisional H2, inter-rater kit | `research/h2/REPORT.md`, `data/processed/payer_aliases.csv` |
| 5 ETL | One command loads 14 hospitals end to end; re-runs skip unchanged files | `pipeline/run.py`, `docs/etl_report.md` |
| 6 API and specs | Search API, benchmark, screen spec, wireframe, H3 and accuracy plans | `api/main.py`, `docs/results_screen_spec.md`, `web/wireframes/results.html` |

## Key numbers
- **Hospitals checked:** 46 in the registry (8 Tucson, 38 Phoenix; 15 Banner). 40 have a known direct file link,
  3 of which robots.txt blocks (Northwest x3); in total 6 cannot be reached automatically (Northwest x3 and
  Tucson Medical Center by robots.txt, City of Hope Phoenix refuses our downloader, Arizona Orthopedic and Surgical
  site not reachable). 16 discovery or access
  problems are documented with URL and date.
- **Files parsed:** 15 hospitals attempted, 14 files downloaded, 13 in the CMS template (6 JSON, 7 CSV tall),
  all 13 valid in the official CMS validator with 0 errors; 1 non-standard file (CORE). Mayo Clinic's file is
  21.5 GB; it finished downloading and its validation and parse were still running at the time of writing.
- **H1 verdict: PROCEED.** 12 of 15 hospitals yield usable coded rows, across 8 health systems (10 of 12
  non-Banner), against the rule of at least 8 of 12. The second half of H1 is not supported: 0 of 13 files omit
  an applicable CY 2026 element (missing medians all carry an allowed count of 0). The real gaps are access
  (6 blocked hospitals), non-standard or mislabelled files, and 4 of 13 files with no negotiated rates at all.
- **Completeness score:** 11 hospitals at 90 or above, 2 at 80-89, 2 at 0. Equal weights of 20 per component.
  Limitation for the team: the Table 10 components do not reward negotiated rates (Carondelet scores 98.7
  without any).
- **Launch procedures:** 50 (44 CMS shoppable codes + 6 most published), every one published by at least 8 of
  the 12 usable hospitals; descriptions measured at grade 4.7 on average, none above grade 8.
- **Payer matching:** 327 raw strings mapped to 11 canonical insurers + "other" (304 high, 23 medium
  confidence, all provisional). Row coverage 72.6% overall (target 60%); Banner UMC Tucson 58.9% is below the
  target.
- **Provisional H2 (Phoenix only):** median highest-to-lowest ratio 2.81 across the 50 procedures (40 of 50 at
  2 or more; same insurer 3.43), which meets the rule of 2. Cash price below the median negotiated rate for 7 of
  50 procedures (14%). Tucson cannot be measured: only one sampled Tucson hospital publishes negotiated rates.
  Provisional until the two raters accept the dictionary.
- **ETL:** 14 hospitals from 9 systems loaded (target 5 from 3), 33,991 price rows for the launch procedures;
  first run 514 s, re-run with unchanged files 62 s.
- **Latency:** search p95 9.6 ms over HTTP (target 500 ms), autocomplete p95 4.9 ms (target 150 ms), measured
  on the 14 loaded hospitals; to be re-measured when more are loaded.

## Open human tasks
1. Install Docker or start its daemon if the team wants `docker compose`.
2. Manual downloads in `MANUAL_DOWNLOADS.md` (6 hospitals), saved to `data/raw/manual/`.
3. Inter-rater test: two people label `research/h2/irr_rater_A.csv` and `_B.csv` independently (about
   1-1.5 hours each, guide in `labeling_guide.md`), run `irr_score.py`, resolve disagreements, mark accepted,
   re-run `research/h2/h2_provisional.py`.
4. Decide with Dr. Li: completeness weights and whether negotiated rates should count; whether the 60% coverage
   rule is per hospital (Banner UMC Tucson) or overall; which hypothesis carries the paper given the H1 result.
5. Spot-check the largest surgical price ratios (prostate biopsy, fluid drainage, shoulder arthroscopy) in the
   source files.
6. When Mayo finishes: `python -m pipeline.run 030103` (if not already loaded) and
   `python -m pipeline.h1_profile 030103`, then update H1 and H2.
7. Read the terms of use still marked "Not checked" (8 hospitals) and ask the university about the Dignity
   Health automated-access clause, as the data-use memo proposed.
8. Fix the proposal citation: "without barriers" is 45 CFR 180.50(d)(3) and the .txt file is (d)(6).
9. Check CMS address data for CCN 030037 (listed at 1800 E Van Buren St, Phoenix, not in Tempe).
10. A clinician or Dr. Li reads the 50 plain-language procedure names; IRB application status before any H3
    data is used for publication.

## Paragraph for Dr. Li
We loaded the CMS price files of 14 Tucson and Phoenix hospitals from 9 health systems into the ClearTab
database, and all 13 files in the CMS template passed the official CMS validator with no errors. H1 is met
under the pre-written rule, since 12 of the 15 hospitals we tried yield usable coded prices, but its second half
is not supported, because none of the 13 files leaves out a required CY 2026 element and the real gaps are
blocked access, non-standard files and files without any negotiated rates. On provisional payer matching, the
median highest-to-lowest price ratio across our 50 launch procedures in Phoenix is 2.81, which meets the H2
rule of 2, while Tucson cannot yet be measured because only one sampled Tucson hospital publishes negotiated
rates. The search API answers in under 10 ms at the 95th percentile, and the two-rater payer test, the
manual downloads and the phone accuracy check are the next human steps. We would value your advice on the
completeness score weights and on which hypothesis should carry the paper.
