# H1 - Published data is usable

## Decision rule (copied from proposal Table 13 before any file was downloaded, 2026-10-12)

> Proceed if at least 8 of 12 hospitals yield usable coded rows. If fewer than 8 do, the consumer
> comparison is reduced to the systems that publish usable files and the compliance scoreboard in Table 12
> is promoted into core scope, because the finding is then about non publication rather than about price.

Measurement (Table 13): the Feature 5 completeness score computed across at least 12 hospitals in at least
4 health systems, reported as the share of hospitals reaching each score band and the share missing each
named 2026 element.

Hypothesis text: a majority of the machine readable files published by hospitals in the Tucson and Phoenix
metropolitan areas can be parsed into comparable, code level price rows, and a substantial share still omit
at least one element required by the CY 2026 rule.

## Results

Run on 2026-10-12. All numbers below come from `research/h1/summarize.py` and `research/h1/median_gap.py`
over data/processed/h1_file_profile.csv, h1_required_elements.csv and h1_validator.csv.

### Sample
Default sample from the master prompt with logged replacements (pipeline/h1_download.py):
- Northwest Medical Center and Oro Valley Hospital: robots.txt disallows their files (Phase 1). Replaced by
  Exceptional Community Hospital - Maricopa and East Valley ER & Hospital (two non-Banner systems).
- Valleywise Health Medical Center: the download portal closed the connection on the first two GET attempts,
  so The CORE Institute Specialty Hospital was added as a replacement. On the third attempt (the first ETL
  run, Phase 5) the file downloaded normally, so Valleywise is included and CORE stays in the sample too.
- Mayo Clinic Hospital (Phoenix): the file is 21.5 GB. The first transfer broke at 560 MB and was resumed
  (HTTP Range with If-Range on the ETag, so the same file version). Validation and parsing took several hours;
  the profile was added to the H1 tables from the ETL cache (research/h1/backfill_from_cache.py).
- Tucson Medical Center: not added; no file in data/raw/manual/ yet.

15 hospitals attempted across 11 health system labels, 15 files downloaded, 14 in the CMS template
(6 CMS JSON, 8 CMS CSV tall, 0 CMS CSV wide), 1 non-standard (CORE: its own column layout, not the CMS
template). All 14 template files declare version 3.0.0 and all 14 pass the official CMS validator
(hpt-validator-cli 1.10.8, validator 2.6.0, data dictionary 3.0.0) with 0 errors.

### Definition of "usable coded rows"
A hospital yields usable coded rows when its file parses as a CMS template and has priced rows for at least
100 distinct CPT, HCPCS or MS-DRG codes. (Threshold set for this analysis; the decision does not depend on it:
every hospital that passes has over 1,000 such codes, and every one that fails has 0.)

### Per hospital
| Hospital | System | Format | File date | Rows | Priced CPT/HCPCS/DRG codes | Negotiated $ / % / algorithm | Score |
|---|---|---|---|---|---|---|---|
| St. Mary's Hospital | Carondelet (Tenet) | CMS JSON | 2026-04-06 | 20,614 | 2,031 | no negotiated rates | 98.7 |
| St. Joseph's Hospital (Tucson) | Carondelet (Tenet) | CMS JSON | 2026-04-06 | 20,802 | 2,088 | no negotiated rates | 98.7 |
| HonorHealth Deer Valley | HonorHealth | CMS CSV tall | 2026-04-01 | 370,076 | 19,081 | 85.8% / 0.8% / 13.4% | 96.0 |
| HonorHealth Scottsdale Osborn | HonorHealth | CMS CSV tall | 2026-04-01 | 366,368 | 19,079 | 86.3% / 0.8% / 13.0% | 96.1 |
| St. Joseph's Hospital and Medical Center (Phoenix) | Dignity Health | CMS JSON | 2026-02-28 | 778,589 | 9,169 | 87.2% / 12.8% / 0% | 96.9 |
| Chandler Regional Medical Center | Dignity Health | CMS JSON | 2026-02-28 | 590,510 | 8,569 | 92.4% / 7.6% / 0% | 97.8 |
| Abrazo Central Campus | Abrazo (Tenet) | CMS JSON | 2026-07-23 | 400,026 | 16,193 | 82.2% / 17.8% / 0% | 96.2 |
| Valleywise Health Medical Center | Valleywise Health | CMS CSV tall | 2026-06-28 | 2,530,959 | 24,093 | 76.0% / 0.1% / 24.0% | 88.1 |
| Arizona Spine and Joint Hospital | USPI | CMS JSON | 2026-04-14 | 7,929 | 1,223 | 100% / 0% / 0% | 98.3 |
| Banner UMC Tucson | Banner Health | CMS CSV tall | 2026-09-25 | 611,483 | 5,337 | 99.1% / 0% / 0.9% | 98.4 |
| Banner Desert Medical Center | Banner Health | CMS CSV tall | 2026-09-23 | 554,123 | 5,007 | 99.2% / 0% / 0.8% | 98.3 |
| East Valley ER & Hospital | Nutex | CMS CSV tall | 4/1/2026 | 7,954 | 2,361 | no negotiated rates | 100.0 |
| Exceptional Community Hospital - Maricopa | Exceptional Healthcare | CMS CSV tall | 2/1/2026 | 4,790 | 0 (see note) | no negotiated rates | 80.0 |
| The CORE Institute Specialty Hospital | Independent | non-standard | - | 0 | 0 | - | 0 |
| Mayo Clinic Hospital (Phoenix) | Mayo Clinic | CMS CSV tall | 08/14/2026 | 57,479,558 | 7,490 | 99.97% / 0.03% / 0% | 94.8 |

Shares of negotiated records: a record is counted as dollar when it has a dollar amount, else percent, else
algorithm. Note on Exceptional: 2,176 of its 4,790 rows carry a 5-character value that looks like a CPT
code, but every code is labelled type "CDM". The parser does not relabel codes (hard rule 7), so the file
has no usable code. This is reported to the team, not fixed. Valleywise scores 88.1 mainly because only 63%
of its rows carry a CPT, HCPCS or MS-DRG code (C3 = 12.7); Mayo scores 94.8 for the same reason (74%, C3 = 14.8).

### CY 2026 elements
- Organizational NPI (type_2_npi), attester name and attestation statement: present in 14 of 14 template files.
- Median, 10th percentile, 90th percentile and count: present in all 9 files that have percent or algorithm
  rates; not applicable in the 5 files that have none (St. Mary's, St. Joseph's Tucson, Arizona Spine and
  Joint, East Valley, Exceptional).
- Files missing or empty on at least one applicable 2026 element (as a column or key): 0 of 14 (0%).
- At record level, most percent or algorithm records carry no median: St. Joseph's Phoenix 163,731 of
  180,400, Chandler Regional 108,189 of 124,863, Abrazo Central 57,730 of 57,732, Valleywise 554,394 of
  557,162, HonorHealth Osborn 33,711 of 39,596, HonorHealth Deer Valley 35,301 of 41,120, Banner UMC Tucson
  8,705 of 9,116, Banner Desert 9,033 of 9,244. In all of these the file reports an allowed count of 0 (no paid claims in the look-back period),
  so the median is legitimately absent rather than omitted. **Exception: Mayo**, 71,229 of 78,026 records
  without a median; 59,343 report a count of 0, but **11,886 carry neither a median nor a count**. Those
  records omit an applicable CY 2026 element even though the columns exist; the CMS validator does not flag
  them. (Here a record counts if it has any percent or algorithm rate, even when a dollar figure is also
  given, so the totals differ from pct_algo_records in the profile.)

### Completeness score (Feature 5)
Formula (equal weights; the proposal gives none, so the team can change them in pipeline/h1_profile.py):
`score = C1 + C2 + C3 + C4 + C5`, where C1 = 20 if a CMS-template file was found and parsed; C2 = 20 if the
CMS validator reports 0 errors; C3 = 20 x share of normalized rows with a CPT, HCPCS or MS-DRG code;
C4 = 20 x (gross + cash records + negotiated records with a dollar amount + percent or algorithm records
with a median) / (gross + cash + all negotiated records); C5 = 20 x (applicable 2026 elements present) /
(applicable 2026 elements). Labels: complete 80-100, partial 1-79, not published 0.

Bands: 12 hospitals at 90 or above, 2 at 80-89 (Valleywise 88.1, Exceptional 80.0), 0 at 1-79, 1 at 0 (CORE
non-standard).

Limitation the team should decide on: the five components in proposal Table 10 do not reward publishing
payer-specific negotiated rates. The two Carondelet hospitals publish only gross and cash prices and still
score 98.7, and Exceptional, which has no usable code at all, still reaches 80.0 (complete) because
every other component is full. Options: keep the formula (it measures what Table 10 names), or count
"negotiated rates present" inside C4. Changing it is a scope decision for the PM and Dr. Li.

## Verdict
**H1 decision rule: PROCEED.** 13 of the 15 hospitals attempted yield usable coded rows, across 9 health
system labels (Carondelet, HonorHealth, Dignity Health, Abrazo, Valleywise, Mayo Clinic, USPI, Banner Health,
Nutex), which meets "at least 8 of 12". 11 of these 13 are non-Banner.

Sensitivity: if the two robots.txt-blocked Northwest hospitals are counted as failures instead of being
replaced, the count of usable hospitals is still 13 (of 17 attempted), above the absolute threshold of 8.

Second half of the hypothesis ("a substantial share still omit at least one CY 2026 element"): **not
supported at file level, partly at record level.** 0 of 14 template files lack an applicable 2026 element as
a column, and in 8 of 9 files every missing median is explained by an allowed count of 0. Only Mayo has
records (11,886, 15% of its percent or algorithm records) that carry neither. One file in 14 is not a
"substantial share". Problems that do exist are about access and usefulness rather than missing elements:
2 of 15 attempted hospitals gave no usable file (non-standard layout, mislabelled codes), 4 of 14 template
files contain no negotiated rates at all, and 6 of the 46 registry
hospitals block or refuse automated access (Phase 1). This should be reported as found, and it is worth
discussing with Dr. Li which hypothesis carries the paper.

Consequence for H2 and F4: comparisons of negotiated rates can draw on 10 hospitals in 7 systems (HonorHealth
x2, Dignity x2, Abrazo, Valleywise, Mayo, USPI, Banner x2), of which only Banner UMC Tucson is in Tucson; cash
and gross comparisons can draw on all 13.
