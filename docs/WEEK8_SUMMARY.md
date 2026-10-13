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
  site not reachable). 16 discovery or access problems are documented with URL and date.
- **Files parsed:** 15 hospitals attempted, 15 files downloaded (Mayo: 21.5 GB, 57.5 million rows), 14 in the
  CMS template (6 JSON, 8 CSV tall), all 14 valid in the official CMS validator with 0 errors; 1 non-standard
  file (CORE).
- **H1 verdict: PROCEED.** 13 of 15 hospitals yield usable coded rows, across 9 health systems (11 of 13
  non-Banner), against the rule of at least 8 of 12. The second half of H1 is not supported at file level:
  0 of 14 files lack an applicable CY 2026 element. At record level only Mayo omits elements (11,886
  percent or algorithm records with neither median nor count). The real gaps are access (6 blocked
  hospitals), non-standard or mislabelled files, and 4 of 14 files with no negotiated rates at all.
- **Completeness score:** 12 hospitals at 90 or above, 2 at 80-89, 1 at 0. Equal weights of 20 per component.
  Limitation for the team: the Table 10 components do not reward negotiated rates (Carondelet scores 98.7
  without any).
- **Launch procedures:** 50 (45 CMS shoppable codes + 5 most published), every one published by at least 8 of
  the 13 usable hospitals; descriptions measured at grade 4.7 on average, none above grade 8.
- **Payer matching:** 2,391 raw strings (2,064 from Mayo) mapped to 11 canonical insurers + "other" (2,368 high,
  23 medium confidence, all provisional). Row coverage 72.6% without Mayo (target 60%) but 8.6% with Mayo,
  because Mayo's 51.8 million negotiated rows are mostly national administrators and out-of-state plans (3.0%
  canonical). Banner UMC Tucson (58.9%) and Mayo are below 60% per hospital.
- **Provisional H2 (Phoenix only):** median highest-to-lowest ratio 2.81 across the 50 procedures (40 of 50 at
  2 or more; same insurer 3.43), which meets the rule of 2. Cash price below the median negotiated rate for 5 of
  50 procedures (10%). Tucson cannot be measured: only one sampled Tucson hospital publishes negotiated rates.
  Provisional until the two raters accept the dictionary.
- **ETL:** 15 hospitals from 10 systems loaded (target 5 from 3), 142,727 price rows for the launch procedures;
  full re-run with unchanged files 11 minutes (most of it re-hashing Mayo); peak memory 3.1 GB after the
  out-of-memory fix.
- **Latency:** search p95 18.7 ms over HTTP with all 15 hospitals (target 500 ms), autocomplete p95 4.6 ms
  (target 150 ms).
- **GitHub:** public repository https://github.com/MrazzKa/cleartab with 7 branches, 14 milestone issues and
  6 stacked pull requests. Branch protection waits for GitHub Education; CI has not started any run yet (see
  open tasks).

## Open human tasks
1. GitHub Actions: open https://github.com/MrazzKa/cleartab/actions and read any banner. No run has been
   created for any push or pull request, although Actions is enabled and the workflow is registered; this is
   usually an account-level restriction only visible in the web interface.
2. When GitHub Education is approved: turn on branch protection for main (1 approving
   review, CI required). Until then, merge only after a team member who is not the author approves.
3. Decide whether docs/source/ClearTab_Signed_Proposal.pdf (signatures of six people) and the other source
   documents should stay in a public repository.
4. Manual downloads in MANUAL_DOWNLOADS.md (6 hospitals), saved to data/raw/manual/.
5. Inter-rater test: two people label research/h2/irr_rater_A.csv and _B.csv independently (about
   1-1.5 hours each, guide in labeling_guide.md), run irr_score.py, resolve disagreements, mark accepted,
   re-run research/h2/h2_provisional.py.
6. Decide with Dr. Li: completeness weights and whether negotiated rates should count; whether the 60% coverage
   rule is per hospital or pooled (Mayo changes the pooled figure from 72.6% to 8.6%); which hypothesis carries
   the paper given the H1 result.
7. Spot-check the largest surgical price ratios (prostate biopsy, shoulder arthroscopy, gallbladder removal) in
   the source files.
8. Read the terms of use still marked "Not checked" (8 hospitals) and ask the university about the Dignity
   Health automated-access clause, as the data-use memo proposed.
9. Fix the proposal citation: "without barriers" is 45 CFR 180.50(d)(3) and the .txt file is (d)(6).
10. Check CMS address data for CCN 030037 (listed at 1800 E Van Buren St, Phoenix, not in Tempe).
11. A clinician or Dr. Li reads the 50 plain-language procedure names; IRB status before any H3 data is used
    for publication; phone accuracy check on Nov 21 (research/accuracy_check/plan.md).

## Paragraph for Dr. Li
We loaded the CMS price files of 15 Tucson and Phoenix hospitals from 10 health systems into the ClearTab
database, and all 14 files in the CMS template passed the official CMS validator with no errors. H1 is met under
the pre-written rule, since 13 of the 15 hospitals we tried yield usable coded prices, but its second half is
largely not supported, because no file leaves out a required CY 2026 element as a column and only Mayo omits
them in some records, while the larger gaps are blocked access, non-standard files and files without any
negotiated rates. On provisional payer matching, the median highest-to-lowest price ratio across our 50 launch
procedures in Phoenix is 2.81, which meets the H2 rule of 2, while Tucson cannot yet be measured because only
one sampled Tucson hospital publishes negotiated rates. The search API answers in under 20 ms at the 95th
percentile, and the two-rater payer test, the manual downloads and the phone accuracy check are the next human
steps. We would value your advice on the completeness score weights, on how to apply the 60% payer coverage
rule now that Mayo's national payer mix dominates the pooled rows, and on which hypothesis should carry the
paper.
