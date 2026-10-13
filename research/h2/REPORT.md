# H2 - Prices vary enough to matter

## Feature 4 targets (copied from proposal Table 9 before any matching, 2026-10-12)
- Payer dictionary size: 150 or more raw strings, mapped to roughly 10 canonical Arizona insurers plus an
  "other" bucket.
- Row coverage by canonical insurers: 60% or more of priced rows. Measured, not assumed; below this the
  product falls back to cash and gross prices only.
- Inter rater agreement on mapping: 85% or higher. Two team members map the same strings independently
  before the dictionary is accepted.
- Outlier rules: drop rates under $1 and above the gross charge.
- Methodology labels: fixed dollar, percent of charges, per diem, algorithm. Rows that are not a fixed dollar
  amount are never shown as a headline price.
- Percent of charges and algorithm rows: shown as an allowed amount range, using the 2026 median and 10th to
  90th percentile allowed amounts, labelled as an allowed amount estimate rather than a negotiated price.
- Unmatched plans: shown as "plan not matched", never silently folded into another insurer.

## H2 decision rule (copied from proposal Table 13 before measuring)
> Proceed if the median highest-to-lowest ratio across the launch procedures is at least 2. If the spread is
> smaller than that, comparison is not the product's value proposition and the project reframes around
> interpretation and provenance: what a published price means, what it excludes, and which hospitals
> publish nothing.

Measurement: ratio of highest to lowest comparable rate per code per metro, and the share of the fifty
launch procedures where the cash price is below the median negotiated rate. Measured only on rows that
survive the normalization rules in Feature 4.

## Results (PROVISIONAL - the payer dictionary has not been accepted by two raters yet)

Run 2026-10-12 on the 12 usable H1 files (including Valleywise, which downloaded in the first ETL run). Reproduce: `python -m pipeline.payers`, `python -m pipeline.normalize`,
`PYTHONPATH=. python research/h2/h2_provisional.py`.

### Canonical insurers (pipeline/payers.py)
Aetna; Blue Cross Blue Shield of Arizona; Cigna; UnitedHealthcare; Humana; Banner Health plans; Mercy Care;
Health Choice Arizona; Centene (Arizona Complete Health, Ambetter, Health Net, Wellcare); Molina; Oscar; plus
"other". That is 11 named insurers, close to the "about 10" in Table 9. The AHCCCS plans come from the AHCCCS
report "Population by Health Care Contractor", September 2026
(https://www.azahcccs.gov/Resources/Downloads/PopulationStatistics/PopulationbyContractor09102026.pdf,
retrieved 2026-10-12): UnitedHealthcare Community Plan, Mercy Care, Banner-University Family Care, Arizona
Complete Health-Complete Care Plan, Health Choice Arizona, Molina Complete Care (plus DCS CHP and ALTCS, DDD
and tribal programs). Care 1st shows 0 members in every month of that report. The older AHCCCS Complete Care
page (https://www.azahcccs.gov/AHCCCS/Initiatives/AHCCCSCompleteCare/) still lists 7 plans from the 2018
award, including Care1st; the newer report was used.

### Dictionary and coverage
- data/processed/payer_aliases.csv: **327** raw payer + plan strings (target 150 or more), all mapped by
  deterministic rules: 304 high confidence, 23 medium (each has a note, for example "APIPA is the former name
  of UnitedHealthcare Community Plan in AHCCCS"). All rows are rater_status = provisional.
- Rental networks (MultiPlan, First Health, "Medical Rental"), workers compensation plans, government
  programs, IPAs, employers and small Medicare Advantage plans map to "other".
- Row coverage by canonical insurers (negotiated rows after outlier rules): **72.6% overall** (3,260,178 of
  4,493,442), target 60%. Per hospital: Arizona Spine and Joint 100%, HonorHealth Osborn 95.7%, HonorHealth
  Deer Valley 95.1%, Abrazo Central 90.6%, Chandler Regional 78.8%, Valleywise 68.2%, St. Joseph's Phoenix
  66.9%, Banner Desert 65.2%, **Banner UMC Tucson 58.9% (below 60%)**. Carondelet x2, East Valley and Exceptional publish no
  negotiated rows. Under the Table 9 rule, Banner UMC Tucson would fall back to cash and gross only unless
  the team decides the rule applies to the whole dataset rather than per hospital.

### Rows dropped or flagged (data/processed/f4_flag_log.csv)
| Reason | Rows | Action |
|---|---|---|
| above_gross (negotiated dollar above the gross charge) | 133,246 | dropped |
| under_1_dollar (dollar amount under $1) | 131,732 | dropped |
| unparseable | 0 | dropped |
| gross_from_code (item had no gross; compared with the highest gross for the same code) | 151,279 | kept, flagged |
| no_gross_to_check (no gross anywhere for the code) | 1,768,380 | kept, flagged |
| methodology: fixed dollar / percent of charges / algorithm / per diem (negotiated rows) | 2,969,929 / 853,520 / 921,278 / 9,950 | only fixed dollar can be a headline price |

Valleywise alone has 116,171 rows under $1 (114,474 negotiated dollar, 1,528 gross, 169 cash; values from
$0.01 to $0.99, median $0.43, labelled "fee schedule"; examples are professional-fee items such as
"PF I&D COMPLEX DRAINAGE WND" at $0.01) and 58,923 rows above gross. What these values mean is not known; they
are dropped as Table 9 requires.

Note: Banner files carry a dollar figure on rows whose methodology is "percent of total billed charges";
these are labelled percent of charges and are not headline prices, as Table 9 requires.

### Provisional H2 measures (data/processed/h2_provisional_by_procedure.csv)
Comparable rate = negotiated dollar, methodology fixed dollar, surviving the outlier rules, facility billing,
outpatient or both, canonical insurer. 12,436 comparable rows from 9 hospitals (8 Phoenix, 1 Tucson).
- **Median highest-to-lowest ratio across launch procedures: 2.81** (interquartile range 2.39 to 7.56), from
  50 procedure-metro pairs, all in Phoenix. 40 of 50 procedures have a ratio of 2 or more.
- Tucson: no ratio can be computed, because only Banner UMC Tucson publishes negotiated rates among the
  sampled Tucson hospitals (Carondelet publishes none; Northwest and TMC were not downloadable).
- Sensitivity, same insurer across hospitals: median 3.43. Row level (single highest / single lowest rate):
  median 2,596, driven by isolated very low rates (for example a $1.00 Aetna rate for a metabolic panel at
  Abrazo Central). The row-level figure is not a credible measure and is shown only to document why hospital
  medians are used.
- Cash below the median negotiated rate: **7 of 50 procedures (14%)** when the median hospital cash price is
  compared with the median comparable negotiated rate; 39 of 282 hospital-procedure pairs (14%) when each
  hospital's cash price is compared with its own median negotiated rate.
- Caution: the largest ratios are surgical (prostate biopsy 39.7, fluid drainage 23.8, shoulder arthroscopy
  15.0, gallbladder removal 10.1). A human should check a few of these rows in the source files before the
  result is used, because a low rate can be a component or add-on price rather than the whole procedure.

### Provisional verdict
On provisional data, the H2 decision rule is met (2.81 >= 2): **PROCEED**, for Phoenix only. This becomes
final only after (1) both raters label the 200 strings and agreement is 85% or higher, (2) disagreements are
resolved and the dictionary is marked accepted, and (3) the script is re-run. If the raters change mappings,
the ratio may change; the decision is not expected to flip unless it falls below 2.

## Inter-rater test (not run yet)
- Sample: research/h2/make_irr_sample.py, seed **20261012**: 100 strings drawn with probability
  proportional to row count, then 100 drawn uniformly from the rest, shuffled (200 of the 327 strings).
- Files: research/h2/irr_rater_A.csv and irr_rater_B.csv (identical, label columns empty),
  research/h2/labeling_guide.md, research/h2/irr_score.py (percent agreement, Cohen's kappa, disagreements).
- The rater files are empty; agreement has not been estimated.
