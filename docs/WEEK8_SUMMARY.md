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
- **Hospitals checked:** 46 in the registry (8 Tucson, 38 Phoenix; 15 Banner). 6 block or refuse automated
  download; a team member downloaded 4 of them by hand (Tucson Medical Center and the three Northwest
  Healthcare hospitals). City of Hope Phoenix (the available file is for Duarte, California) and Arizona
  Orthopedic and Surgical (its domain now shows a vendor page) have no usable file. 19 discovery or access
  problems are documented with URL and date.
- **Files parsed:** 19 hospitals, 19 files (Mayo: 21.5 GB, 57.5 million rows), 18 in the CMS template (6 JSON,
  9 CSV tall, 3 CSV wide), all 18 valid in the official CMS validator with 0 errors; 1 non-standard (CORE).
- **H1 verdict: PROCEED.** 17 of 19 hospitals yield usable coded rows, across 11 health systems (15 of 17
  non-Banner, 7 in Tucson), against the rule of at least 8 of 12. The second half of H1 is not supported at
  file level (no file lacks an applicable CY 2026 element) and only marginally at record level (Mayo: 11,886
  records with neither median nor count). The real gaps are access, non-standard or mislabelled files, 4 of 18
  files with no negotiated rates, and TMC expressing 83% of its negotiated rates as algorithms.
- **Completeness score:** 15 hospitals at 90 or above, 3 at 80-89, 1 at 0. Equal weights of 20 per component.
  The Table 10 components do not reward negotiated rates (Carondelet scores 98.7 without any).
- **Launch procedures:** 50 (45 CMS shoppable codes + 5 most published), each published by at least 9 of the
  17 usable hospitals; descriptions average reading grade 4.7, none above grade 8.
- **Payer matching:** 2,502 raw strings mapped to 11 canonical insurers + "other" (2,464 high, 38 medium
  confidence, all provisional). Row coverage 66.0% pooled without Mayo (target 60%), 12.8% with Mayo; per
  hospital, 5 of 14 are below 60% (Banner UMC Tucson, Sahuarita, Northwest, Oro Valley, Mayo).
- **Provisional H2: not resolved.** Median highest-to-lowest ratio 2.81 in Phoenix (40 of 50 procedures at 2 or
  more) and 1.63 in Tucson (9 of 49); pooled across both metros 1.99, just under the rule of 2, and the payer
  dictionary can move it (new aliases moved it from 2.13 to 1.99). Cash price below the median negotiated rate
  for 1 of 50 procedures. The final answer waits for the two-rater test.
- **ETL:** 19 hospitals from 13 systems loaded (target 5 from 3), 174,071 price rows for the launch procedures;
  full re-run with unchanged files about 11 minutes; peak memory 3.2 GB.
- **Latency:** search p95 39.3 ms over HTTP with all 19 hospitals (target 500 ms), autocomplete p95 8.4 ms
  (target 150 ms).
- **GitHub:** public repository https://github.com/MrazzKa/cleartab with 7 branches, 14 milestone issues and
  6 stacked pull requests.

## Open human tasks
1. Inter-rater test (decides H2): two people label research/h2/irr_rater_A.xlsx and irr_rater_B.xlsx
   independently, about 1-1.5 hours each (guide: research/h2/labeling_guide.md), then run
   `python research/h2/irr_score.py`, resolve disagreements together, mark the dictionary accepted and re-run
   research/h2/h2_provisional.py.
2. Decide with Dr. Li: completeness weights and whether negotiated rates should count; whether the 60% coverage
   rule is per hospital or pooled; whether H2's median is pooled across metros or judged per metro; which
   hypothesis carries the paper.
3. Spot-check the largest surgical price ratios (prostate biopsy, shoulder arthroscopy) in the source files.
4. Read the terms of use still marked "Not checked" (8 hospitals) and ask the university about the Dignity
   Health automated-access clause, as the data-use memo proposed.
5. Fix the proposal citation: "without barriers" is 45 CFR 180.50(d)(3) and the .txt file is (d)(6).
6. Check CMS address data for CCN 030037 (listed at 1800 E Van Buren St, Phoenix, not in Tempe); decide whether
   TMC Rincon Hospital should be added to the registry.
7. Record the exact TMC file URL in MANUAL_DOWNLOADS.md if it is still in the browser history.
8. A clinician or Dr. Li reads the 50 plain-language procedure names; IRB status before any H3 data is used for
   publication; phone accuracy check on Nov 21 (research/accuracy_check/plan.md).
9. Merge the six phase pull requests in order after a review by a team member who is not the author.

## Paragraph for Dr. Li
We have now loaded the CMS price files of 19 Tucson and Phoenix hospitals from 13 health systems, including
four files that robots.txt blocks and that we downloaded by hand, and all 18 files in the CMS template passed
the official CMS validator with no errors. H1 is met under the pre-written rule, since 17 of the 19 hospitals
yield usable coded prices, but its second half is largely not supported, because no file leaves out a required
CY 2026 element as a column and only Mayo omits them in some records. H2 is not resolved yet: on provisional
payer matching the median highest-to-lowest ratio is 2.81 in Phoenix and 1.63 in Tucson, 1.99 when both metros
are pooled, so the decision sits at the threshold and will be settled by the two-rater payer test. The search
API answers in under 40 ms at the 95th percentile across all 19 hospitals. We would value your advice on how to
read the H2 rule across metros, on the completeness score weights, on the 60% payer coverage rule, and on which
hypothesis should carry the paper.
