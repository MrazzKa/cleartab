# Cash or insurance (discovery, 2026-10-22)

Script: `python -m research.discovery.cash_vs_insurance` (seed 20261022, 2,000 cluster bootstrap draws over
hospitals). Outputs: `data/processed/cash_vs_insurance_triples.csv`, `cash_vs_insurance_summary.csv`.
Payer dictionary accepted 2026-10-16. Exploratory: no decision rule was fixed before this analysis.

## Question
H2 compared each procedure's median cash price with the median negotiated rate across all insurers and found
cash lower for 1 of 50 procedures. A patient below their deductible pays their own insurer's rate, not the
median, so this analysis compares the hospital's cash price with each named insurer's rate at the same
hospital. Prompted by the UA Campus Health insurance office (written answer, 2026-10-21): students are "in
disbelief that services often cost more with insurance than without".

## Method
- Same row filters as H2: launch procedures (CPT and HCPCS), facility or blank billing class, outpatient or
  both, rows dropped by F4 rules excluded, fixed dollar negotiated rates of the 11 named insurers.
- Main population: commercial and marketplace plans (patients with a deductible who could pay cash instead).
  AHCCCS, Medicare Advantage and other government plans are shown for reference only.
- Pair = hospital x procedure with a cash price and at least one main-population rate (437 pairs).
  Triple = pair x insurer x plan type, rate = median of that insurer's fixed dollar rates (2,867 triples).
- Cash = median of the hospital's cash rows for the procedure; 115 pairs have more than one cash value.
  Sensitivity: the highest cash row.
- 12 of 19 hospitals qualify. Not included: Mayo, St. Mary's, St. Joseph's Tucson and East Valley (no fixed
  dollar rate from a named insurer under these filters), Abrazo Central and Exceptional (no cash price), CORE
  (no usable codes).

## Results
| Measure | Value | 95% CI |
|---|---|---|
| Pairs where at least one insurer pays more than cash | 50.6% (221 of 437) | 29.7% - 73.2% |
| Insurer rates above the hospital's cash price | 22.9% of 2,867 | 11.1% - 36.7% |
| Median amount above cash, when above | $56.31 (47% of cash) | |
| Sensitivity, highest cash row | 48.7% of pairs, 21.0% of rates | 27.9% - 70.2% |
| Reference: AHCCCS, Medicare Advantage, government | 15.9% of pairs, 9.7% of rates | |

- By plan type: commercial 47.8% of pairs (median excess $96.40), marketplace 23.5% ($19.37).
- By metro: Phoenix 61.2% of pairs, Tucson 37.4%.
- By system (pairs with at least one insurer above cash): Valleywise 93.8%, Banner 83.9%, Dignity 83.1%,
  TMC 38.7%, Northwest 26.3%, HonorHealth 0.0%. The pattern follows the health system, as in the H2 follow-up.
- By insurer (share of rates above cash): BCBS of Arizona 31.6%, Oscar 27.3%, Cigna 25.1%, Centene 24.5%,
  Aetna 19.2%, UnitedHealthcare 16.6%, Humana 0.0%.
- 19 of 33 procedures with at least 8 pairs have an insurer above cash in half or more of hospitals. Highest:
  lumbar epidural injection 62323 (8 of 10 hospitals, median excess $431), chest x-ray 71045 and 71046
  (9 of 12), mammograms 77065-77067 (6 of 9 or 5 of 8), brain MRI 70553 (6 of 11, median excess $410).

## Limits
- 12 hospitals in 6 systems; the wide CI reflects how much the result depends on the system.
- Published rates, not claims: the rate an insurer actually allows can differ.
- Whether an insured patient may pay the cash price, and whether that payment counts toward the deductible,
  depends on hospital and plan policy and is not in the files. It must be asked (Feature 6 question 3).
- An earlier quick check in a scratch file (all settings and billing classes, all plan types) gave 47.9% of
  pairs and different insurer shares (for example Oscar 62.8%); the figures above use the H2 filters and replace
  it.
