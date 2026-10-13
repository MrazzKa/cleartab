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

Run 2026-10-12 and 2026-10-13. All numbers below come from `research/h1/summarize.py` and
`research/h1/median_gap.py` over data/processed/h1_file_profile.csv, h1_required_elements.csv and
h1_validator.csv.

### Sample
Default sample from the master prompt, with logged changes (pipeline/h1_download.py):
- Northwest Medical Center and Oro Valley Hospital: robots.txt disallows their files, so Exceptional
  Community Hospital - Maricopa and East Valley ER & Hospital were added as replacements. On 2026-10-12 a team
  member downloaded the three Northwest Healthcare files by hand (data/raw/manual/); Northwest, Oro Valley and
  Sahuarita are now in the sample as well.
- Tucson Medical Center: robots.txt disallows the whole site; a team member downloaded the file by hand and,
  as the master prompt requires, it was added.
- Valleywise: the portal refused the first two GET requests, so The CORE Institute Specialty Hospital was
  added; the third attempt succeeded and both stay in the sample.
- Mayo Clinic: 21.5 GB; the transfer was resumed with HTTP Range on the same ETag. Its profile was taken from
  the ETL cache (research/h1/backfill_from_cache.py) instead of parsing the file a second time.
- Not in the sample: City of Hope Phoenix (the file a team member found is for the Duarte, California
  hospital), Arizona Orthopedic and Surgical (azosh.com now shows an unrelated vendor page).

19 hospitals attempted across 13 health system labels, 19 files, 18 in the CMS template (6 CMS JSON, 9 CMS CSV
tall, 3 CMS CSV wide), 1 non-standard (CORE: its own column layout). All 18 template files declare version
3.0.0 and all 18 pass the official CMS validator (hpt-validator-cli 1.10.8, validator 2.6.0, data dictionary
3.0.0) with 0 errors.

### Definition of "usable coded rows"
A hospital yields usable coded rows when its file parses as a CMS template and has priced rows for at least
100 distinct CPT, HCPCS or MS-DRG codes. (Threshold set for this analysis; the decision does not depend on it:
every hospital that passes has over 1,000 such codes, and every one that fails has 0.)

### Per hospital
| Hospital | System | Metro | Format | File date | Rows | Priced CPT/HCPCS/DRG codes | Negotiated $ / % / algorithm | Score |
|---|---|---|---|---|---|---|---|---|
| St. Mary's Hospital | Carondelet (Tenet) | Tucson | CMS JSON | 2026-04-06 | 20,614 | 2,031 | no negotiated rates | 98.7 |
| St. Joseph's Hospital (Tucson) | Carondelet (Tenet) | Tucson | CMS JSON | 2026-04-06 | 20,802 | 2,088 | no negotiated rates | 98.7 |
| Tucson Medical Center | TMC Health | Tucson | CMS CSV tall | 2026-04-30 | 4,216,318 | 17,162 | 17.2% / 0% / 82.8% | 80.4 |
| Northwest Medical Center | Northwest Healthcare | Tucson | CMS CSV wide | 2026-04-01 | 1,672,110 | 4,069 | 99.4% / 0.6% / 0% | 91.2 |
| Oro Valley Hospital | Northwest Healthcare | Tucson | CMS CSV wide | 2026-04-01 | 1,588,490 | 3,621 | 99.2% / 0.8% / 0% | 91.0 |
| Northwest Medical Center Sahuarita | Northwest Healthcare | Tucson | CMS CSV wide | 2026-04-01 | 1,069,137 | 3,250 | 99.8% / 0.2% / 0% | 91.5 |
| Banner UMC Tucson | Banner Health | Tucson | CMS CSV tall | 2026-09-25 | 611,483 | 5,337 | 99.1% / 0% / 0.9% | 98.4 |
| HonorHealth Deer Valley | HonorHealth | Phoenix | CMS CSV tall | 2026-04-01 | 370,076 | 19,081 | 85.8% / 0.8% / 13.4% | 96.0 |
| HonorHealth Scottsdale Osborn | HonorHealth | Phoenix | CMS CSV tall | 2026-04-01 | 366,368 | 19,079 | 86.2% / 0.8% / 13.0% | 96.1 |
| St. Joseph's Hospital and Medical Center | Dignity Health | Phoenix | CMS JSON | 2026-02-28 | 778,589 | 9,169 | 87.2% / 12.8% / 0% | 96.9 |
| Chandler Regional Medical Center | Dignity Health | Phoenix | CMS JSON | 2026-02-28 | 590,510 | 8,569 | 92.4% / 7.6% / 0% | 97.8 |
| Abrazo Central Campus | Abrazo (Tenet) | Phoenix | CMS JSON | 2026-07-23 | 400,026 | 16,193 | 82.2% / 17.8% / 0% | 96.2 |
| Valleywise Health Medical Center | Valleywise Health | Phoenix | CMS CSV tall | 2026-06-28 | 2,530,959 | 24,093 | 76.0% / 0.1% / 24.0% | 88.1 |
| Mayo Clinic Hospital (Phoenix) | Mayo Clinic | Phoenix | CMS CSV tall | 2026-08-14 | 57,479,558 | 7,490 | 99.97% / 0.03% / 0% | 94.8 |
| Arizona Spine and Joint Hospital | USPI | Phoenix | CMS JSON | 2026-04-14 | 7,929 | 1,223 | 100% / 0% / 0% | 98.3 |
| Banner Desert Medical Center | Banner Health | Phoenix | CMS CSV tall | 2026-09-23 | 554,123 | 5,007 | 99.2% / 0% / 0.9% | 98.3 |
| East Valley ER & Hospital | Nutex | Phoenix | CMS CSV tall | 2026-04-01 | 7,954 | 2,361 | no negotiated rates | 100.0 |
| Exceptional Community Hospital - Maricopa | Exceptional Healthcare | Phoenix | CMS CSV tall | 2026-02-01 | 4,790 | 0 (see note) | no negotiated rates | 80.0 |
| The CORE Institute Specialty Hospital | Independent | Phoenix | non-standard | - | 0 | 0 | - | 0 |

Shares of negotiated records: a record is counted as dollar when it has a dollar amount, else percent, else
algorithm. Note on Exceptional: 2,176 of its 4,790 rows carry a 5-character value that looks like a CPT code,
but every code is labelled type "CDM"; codes are not relabelled (bad data is never fixed silently), so the
file has no usable code. Lower scores: TMC (C4 = 6.0: 83% of its negotiated records are algorithms and only
5.6% of percent or algorithm records carry a median), Valleywise and the Northwest files (only 56-74% of rows
carry a CPT, HCPCS or MS-DRG code).

### CY 2026 elements
- Organizational NPI (type_2_npi), attester name and attestation statement: present in 18 of 18 template files.
- Median, 10th percentile, 90th percentile and count: present as columns or keys in all 13 files that have
  percent or algorithm rates; not applicable in the 5 files that have none.
- Files lacking an applicable 2026 element as a column or key: 0 of 18.
- At record level, most percent or algorithm records carry no median, for example TMC 1,526,368 of 1,641,140
  and Valleywise 554,394 of 557,162. In 12 of the 13 files every such record reports an allowed count of 0 (no
  paid claims in the look-back period), so the median is legitimately absent. **Exception: Mayo**, where
  11,886 of 78,026 percent or algorithm records carry neither a median nor a count. The CMS validator does not
  flag them. (Here a record counts if it has any percent or algorithm rate, even when a dollar figure is also
  given, so totals differ from pct_algo_records in the profile.)

### Completeness score (Feature 5)
Formula (equal weights; the proposal gives none, so the team can change them in pipeline/h1_profile.py):
`score = C1 + C2 + C3 + C4 + C5`, where C1 = 20 if a CMS-template file was found and parsed; C2 = 20 if the
CMS validator reports 0 errors; C3 = 20 x share of normalized rows with a CPT, HCPCS or MS-DRG code;
C4 = 20 x (gross + cash records + negotiated records with a dollar amount + percent or algorithm records
with a median) / (gross + cash + all negotiated records); C5 = 20 x (applicable 2026 elements present) /
(applicable 2026 elements). Labels: complete 80-100, partial 1-79, not published 0.

Bands: 15 hospitals at 90 or above, 3 at 80-89 (Valleywise 88.1, TMC 80.4, Exceptional 80.0), 0 at 1-79, 1 at
0 (CORE, non-standard).

Limitation for the team: the five components in proposal Table 10 do not reward publishing payer-specific
negotiated rates. The two Carondelet hospitals publish only gross and cash prices and still score 98.7, and
Exceptional, which has no usable code at all, still reaches 80.0 because every other component is full.
Options: keep the formula (it measures what Table 10 names), or count "negotiated rates present" inside C4.
This is a scope decision for the PM and Dr. Li.

## Verdict
**H1 decision rule: PROCEED.** 17 of the 19 hospitals attempted yield usable coded rows, across 11 health
system labels, which meets "at least 8 of 12". 15 of the 17 are non-Banner, and 7 of them are in Tucson.

Second half of the hypothesis ("a substantial share still omit at least one CY 2026 element"): **not
supported at file level, and only marginally at record level.** No template file lacks an applicable element
as a column; only Mayo (1 of 18 files) has records that omit both median and count. The problems that do
exist concern access and usefulness: 6 of the 46 registry hospitals block or refuse automated download (4 of
them were then downloaded by hand), 2 of 19 attempted hospitals gave no usable file (non-standard layout,
mislabelled codes), 4 of 18 template files contain no negotiated rates, and TMC expresses 83% of its
negotiated rates as algorithms rather than dollars. This should be reported as found; which hypothesis
carries the paper is a question for Dr. Li.

Consequence for H2 and F4: negotiated-rate comparisons can draw on 14 hospitals (9 Phoenix, 5 Tucson); cash and
gross comparisons on all 17 usable hospitals.
