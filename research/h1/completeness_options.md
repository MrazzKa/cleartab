# Completeness score (F5): options for the team and Dr. Li (meeting 2026-10-16)

The proposal (Table 10) names the five components but gives no weights. The current default is 20 points each
(research/h1/REPORT.md). Dr. Li doubts equal weights and asked to see the data first. **This file does not pick an
option.** Reproduce: `python -m research.h1.completeness_options` (data/processed/completeness_options.csv).

## The five components (current, 20 points each)
- C1 file found and parsed as a CMS template; C2 CMS validator reports 0 errors; C3 share of rows with a CPT,
  HCPCS or MS-DRG code; C4 share of price records with a dollar amount (or, for percent and algorithm rates, a
  2026 median allowed amount); C5 share of applicable 2026 elements present.
- In this sample C1, C2 and C5 are 20 for every hospital except CORE (non-standard file, 0 on all). **Only C3 and
  C4 separate hospitals**, so the current score mostly measures coding and dollar expression.

## Three options
- **A. Equal weights (current):** C1 + C2 + C3 + C4 + C5.
- **B. Negotiated rates required:** as A, but a hospital whose file has no payer-specific negotiated rate cannot
  score above 50. Targets the known gap: Carondelet (St. Mary's, St. Joseph's Tucson) and East Valley publish
  only gross and cash and score 98.7-100 under A.
- **C. Patient-weighted:** P = share of the 50 launch procedures with a usable dollar price (a cash price or a
  fixed dollar negotiated rate surviving the F4 rules, facility, outpatient). Score = 50 x P + 10 x (each of
  C1-C5 rescaled to 10). The 50/10 split only illustrates "P counts most"; other splits are possible.

## Components and the three scores
| Hospital | Metro | C1 | C2 | C3 | C4 | C5 | Negotiated rates | Launch procs with usable price | A | Rank A | B | Rank B | C | Rank C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| East Valley ER & Hospital | Phoenix | 20 | 20 | 20.0 | 20.0 | 20 | no | 48 | 100.0 | 1 | 50.0 | 15 | 98.0 | 3 |
| St. Joseph's Hospital (Tucson) | Tucson | 20 | 20 | 18.7 | 20.0 | 20 | no | 30 | 98.7 | 2 | 50.0 | 15 | 79.3 | 15 |
| St. Mary's Hospital | Tucson | 20 | 20 | 18.7 | 20.0 | 20 | no | 30 | 98.7 | 2 | 50.0 | 15 | 79.3 | 15 |
| Banner - University Medical Center Tucson | Tucson | 20 | 20 | 18.6 | 19.8 | 20 | yes | 46 | 98.4 | 4 | 98.4 | 1 | 95.2 | 7 |
| Arizona Spine and Joint Hospital | Phoenix | 20 | 20 | 18.3 | 20.0 | 20 | yes | 19 | 98.3 | 5 | 98.3 | 2 | 68.2 | 17 |
| Banner Desert Medical Center | Phoenix | 20 | 20 | 18.5 | 19.8 | 20 | yes | 44 | 98.3 | 5 | 98.3 | 2 | 93.2 | 9 |
| Chandler Regional Medical Center | Phoenix | 20 | 20 | 19.2 | 18.6 | 20 | yes | 48 | 97.8 | 7 | 97.8 | 4 | 96.9 | 6 |
| St. Joseph's Hospital and Medical Center | Phoenix | 20 | 20 | 19.3 | 17.6 | 20 | yes | 50 | 96.9 | 8 | 96.9 | 5 | 98.5 | 1 |
| Abrazo Central Campus | Phoenix | 20 | 20 | 19.6 | 16.6 | 20 | yes | 50 | 96.2 | 9 | 96.2 | 6 | 98.1 | 2 |
| HonorHealth Scottsdale Osborn Medical Center | Phoenix | 20 | 20 | 18.3 | 17.8 | 20 | yes | 50 | 96.1 | 10 | 96.1 | 7 | 98.0 | 3 |
| HonorHealth Deer Valley Medical Center | Phoenix | 20 | 20 | 18.3 | 17.7 | 20 | yes | 50 | 96.0 | 11 | 96.0 | 8 | 98.0 | 3 |
| Mayo Clinic Hospital (Phoenix) | Phoenix | 20 | 20 | 14.8 | 20.0 | 20 | yes | 43 | 94.8 | 12 | 94.8 | 9 | 90.4 | 11 |
| Northwest Medical Center Sahuarita | Tucson | 20 | 20 | 11.5 | 20.0 | 20 | yes | 44 | 91.5 | 13 | 91.5 | 10 | 89.8 | 13 |
| Northwest Medical Center | Tucson | 20 | 20 | 11.3 | 19.9 | 20 | yes | 45 | 91.2 | 14 | 91.2 | 11 | 90.6 | 10 |
| Oro Valley Hospital | Tucson | 20 | 20 | 11.2 | 19.8 | 20 | yes | 44 | 91.0 | 15 | 91.0 | 12 | 89.5 | 14 |
| Valleywise Health Medical Center | Phoenix | 20 | 20 | 12.7 | 15.4 | 20 | yes | 50 | 88.1 | 16 | 88.1 | 13 | 94.0 | 8 |
| Tucson Medical Center | Tucson | 20 | 20 | 14.4 | 6.0 | 20 | yes | 50 | 80.4 | 17 | 80.4 | 14 | 90.2 | 12 |
| Exceptional Community Hospital - Maricopa | Phoenix | 20 | 20 | 0.0 | 20.0 | 20 | no | 0 | 80.0 | 18 | 50.0 | 15 | 40.0 | 18 |
| The CORE Institute Specialty Hospital | Phoenix | 0 | 0 | 0.0 | 0.0 | 0 | no | 0 | 0.0 | 19 | 0.0 | 19 | 0.0 | 19 |

Bands (90+ / 80-89 / 50-79 / 1-49 / 0): A 15 / 3 / 0 / 0 / 1; B 12 / 2 / 4 / 0 / 1; C 12 / 2 / 3 / 1 / 1.

## How the ranking changes
- **A to B:** the 4 hospitals without negotiated rates (East Valley, both Carondelet hospitals, Exceptional) drop
  to 50 and share rank 15. Everyone else keeps their order. B fixes the known gap and changes nothing else.
- **A to C:** C rewards hospitals that price most of the 50 procedures, even with modest C3/C4. Valleywise (16 to
  8) and TMC (17 to 12) rise because they price all 50; TMC's low C4 (83% of its negotiated rates are algorithms)
  matters less. The two Carondelet hospitals fall to 15 (30 of 50 procedures). Arizona Spine and Joint falls from
  5 to 17 because it is a specialty hospital and does not offer most launch procedures (labs, mammograms), which
  says nothing about the quality of its file. East Valley stays near the top (98.0) because its cash prices count
  as usable for uninsured patients, although it publishes no negotiated rates.
- Exceptional and CORE stay at the bottom under every option.

## Points to settle on Friday
1. Should the score measure **compliance with the file rules** (A or B: what Table 10 names) or **usefulness to a
   patient** (C)? They answer different questions; the product could show one and the paper report both.
2. If C: how to treat specialty hospitals (denominator = launch procedures the hospital offers, or all 50?), and
   whether cash-only hospitals should be able to score at the top.
3. If B: is 50 the right cap, and does "negotiated rates" mean any rate or at least one fixed dollar rate?
4. Any choice must be fixed in writing before the score is shown publicly (F5: "never edited by hand"), and the
   weights reported in the paper.
