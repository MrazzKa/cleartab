# Payer coverage with clustered CIs and the Mayo sensitivity check (meeting 2026-10-16)

**PROVISIONAL.** Uses the payer dictionary of 2026-10-13, not yet accepted (inter-rater round 2 pending).

Reproduce: `python -m research.h2.coverage_followup` (seed 20261016). Outputs:
data/processed/coverage_followup_hospitals.csv, coverage_followup_summary.csv, coverage_followup_strings.csv.
The script checks that its counts equal data/processed/f4_coverage.csv exactly.

**Definition** (proposal Table 9): coverage = share of priced negotiated rows (kept after the F4 outlier rules)
whose payer string maps to one of the 11 canonical insurers. Target: 60% or more, otherwise the product falls back
to cash and gross prices. 14 of the 19 hospitals publish negotiated rates; the other 5 have no rows to cover.

**Why clustered CIs.** One payer string covers thousands of rows (Mayo: 2,064 strings for 51.8 million rows), and
all rows of a string map the same way. Rows are not independent observations, so the CIs below come from a cluster
bootstrap that resamples **hospitals** (2,000 draws). Per-hospital intervals resample that hospital's **payer
strings** (descriptive).

## Main analysis (Mayo included) and sensitivity (Mayo excluded)
| | Main: 14 hospitals, Mayo included | Sensitivity: 13 hospitals, Mayo excluded |
|---|---|---|
| Overall, all rows pooled | **51.0%** (95% CI 48.8% - 73.5%) | **66.7%** (95% CI 55.3% - 76.5%) |
| Share of bootstrap draws with pooled >= 60% | 31.2% | 87.4% |
| Mean of per-hospital coverage | **70.7%** (95% CI 60.5% - 80.2%) | **72.4%** (95% CI 61.6% - 82.4%) |
| Share of draws with mean >= 60% | 98.0% | 99.0% |
| Hospitals below 60% | 5 of 14 | 4 of 13 |
| Phoenix: pooled / mean of hospitals | 50.1% (48.7% - 82.0%) / 78.7% (67.7% - 89.1%) | 74.4% (69.0% - 87.6%) / 82.6% (73.1% - 91.8%) |
| Tucson: pooled / mean of hospitals | 60.7% (42.2% - 74.9%) / 56.1% (43.7% - 69.3%) | unchanged (Mayo is in Phoenix) |

The pooled CI with Mayo is lopsided (48.8% - 73.5% around 51.0%) because Mayo holds 85% of all negotiated rows:
draws that happen to leave Mayo out jump to about 67%, draws that include it stay near 51%.

## Which conclusions change without Mayo
- **Pooled coverage changes verdict.** 51.0% with Mayo is below the 60% target; 66.7% without is above it. A
  pooled reading of Table 9 is therefore decided by one file.
- **Mean of hospitals does not change verdict.** 70.7% vs 72.4%, both above 60% with the lower CI bound above 60%
  in both cases. Hospital-weighted coverage is robust to Mayo.
- **Phoenix pooled changes** (50.1% to 74.4%); **Tucson is unaffected** (60.7% pooled, 56.1% mean), and Tucson's
  mean is below 60% either way, because of the three Northwest hospitals.
- The per-hospital picture does not change: the same 4 non-Mayo hospitals are below 60% either way.

## Per hospital
| Metro | Hospital | Coverage | Interval (payer strings resampled) | Payer strings | Negotiated rows | Below 60% |
|---|---|---|---|---|---|---|
| Phoenix | Arizona Spine and Joint Hospital | 100.0% | 100.0% - 100.0% | 5 | 6,081 | |
| Phoenix | HonorHealth Scottsdale Osborn Medical Center | 95.7% | 89.2% - 98.5% | 39 | 280,639 | |
| Phoenix | HonorHealth Deer Valley Medical Center | 95.1% | 88.1% - 98.2% | 41 | 282,784 | |
| Phoenix | Abrazo Central Campus | 90.6% | 81.8% - 96.4% | 56 | 319,839 | |
| Tucson | Tucson Medical Center | 81.5% | 62.1% - 100.0% | 16 | 1,969,041 | |
| Phoenix | Chandler Regional Medical Center | 78.8% | 61.1% - 94.6% | 29 | 379,003 | |
| Phoenix | Valleywise Health Medical Center | 68.2% | 54.8% - 81.0% | 100 | 1,700,730 | |
| Phoenix | St. Joseph's Hospital and Medical Center | 66.9% | 50.6% - 82.9% | 35 | 508,867 | |
| Phoenix | Banner Desert Medical Center | 65.2% | 50.8% - 80.1% | 56 | 477,050 | |
| Tucson | Banner - University Medical Center Tucson | 58.9% | 43.9% - 73.7% | 62 | 538,449 | yes |
| Tucson | Northwest Medical Center Sahuarita | 57.1% | 40.8% - 72.6% | 47 | 608,455 | yes |
| Phoenix | Mayo Clinic Hospital (Phoenix) | 48.3% | 45.5% - 51.1% | 2,064 | 51,819,013 | yes |
| Tucson | Northwest Medical Center | 44.9% | 30.1% - 60.0% | 62 | 1,001,428 | yes |
| Tucson | Oro Valley Hospital | 38.2% | 24.8% - 51.9% | 67 | 974,812 | yes |

The per-hospital intervals are wide for hospitals with few payer strings (TMC: 16 strings, 62% - 100%), so being
just under or over 60% is not a firm distinction for Banner UMC Tucson (58.9%) or Sahuarita (57.1%).

## What the team and Dr. Li need to decide
Table 9 says "60% or more of priced rows" without saying whether that is pooled or per hospital. Options:
1. **Per hospital** (recommended for the product): a hospital below 60% shows cash and gross only, and its
   negotiated rates appear as "plan not matched". Today that affects 5 of 14 hospitals.
2. **Mean of hospitals** for the study-level statement: 70.7% (60.5% - 80.2%), robust to Mayo.
3. **Pooled rows**: decided by Mayo (51.0% vs 66.7%); we suggest reporting it but not using it as the decision.

Caveat for all three: the 5 hospitals below 60% are mostly ones whose files list many employer plans,
administrators and Medicare Advantage contracts that correctly map to "other" (Northwest "NODE ..." plans, Mayo's
national administrators). Low coverage there reflects payer mix, not only dictionary gaps.
