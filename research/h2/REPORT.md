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

Run 2026-10-13 on the 17 usable H1 hospitals (14 of them publish negotiated rates). Reproduce:
`python -m pipeline.payers`, `python -m pipeline.normalize`, `PYTHONPATH=. python research/h2/h2_provisional.py`.

### Canonical insurers (pipeline/payers.py)
Aetna; Blue Cross Blue Shield of Arizona; Cigna; UnitedHealthcare; Humana; Banner Health plans; Mercy Care;
Health Choice Arizona; Centene (Arizona Complete Health, Ambetter, Health Net, Wellcare); Molina; Oscar; plus
"other". That is 11 named insurers, close to the "about 10" in Table 9. The AHCCCS plans come from the AHCCCS
report "Population by Health Care Contractor", September 2026
(https://www.azahcccs.gov/Resources/Downloads/PopulationStatistics/PopulationbyContractor09102026.pdf,
retrieved 2026-10-12): UnitedHealthcare Community Plan, Mercy Care, Banner-University Family Care, Arizona
Complete Health-Complete Care Plan, Health Choice Arizona, Molina Complete Care (plus DCS CHP and ALTCS, DDD and
tribal programs). Care 1st shows 0 members in every month of that report. The older AHCCCS Complete Care page
(https://www.azahcccs.gov/AHCCCS/Initiatives/AHCCCSCompleteCare/) still lists the 7 plans of the 2018 award;
the newer report was used.

### Dictionary and coverage
- data/processed/payer_aliases.csv: **2,502** raw payer + plan strings (target 150 or more; 2,064 from Mayo),
  all mapped by deterministic rules: 2,464 high confidence, 38 medium (each with a note, for example "no state
  given; read as BCBS of Arizona because the files are Arizona hospitals"). All rows are provisional.
- Rental networks (MultiPlan, First Health, "Medical Rental"), workers compensation plans, government
  programs, IPAs, employers and small Medicare Advantage plans map to "other".
- Row coverage by canonical insurers (negotiated rows after outlier rules), target 60%:
  - pooled, all 14 hospitals: **12.8%** (7,792,291 of 60,866,191);
  - pooled without Mayo: **66.0%** (5,967,200 of 9,047,178);
  - per hospital: Arizona Spine and Joint 100%, HonorHealth Osborn 95.7%, HonorHealth Deer Valley 95.1%,
    Abrazo Central 90.6%, TMC 81.5%, Chandler Regional 78.8%, Valleywise 68.2%, St. Joseph's Phoenix 66.9%,
    Banner Desert 65.2%, **Banner UMC Tucson 58.9%, Sahuarita 52.4%, Northwest 42.3%, Oro Valley 37.0%,
    Mayo 3.5%** (the last five are below 60%).
- Mayo has 51.8 million negotiated rows, more than five times all other hospitals together, and almost all
  of its payers are national third-party administrators and out-of-state plans. A pooled share is therefore
  decided by one file. The team should decide whether Table 9's 60% rule applies per hospital (then the five
  hospitals above fall back to cash and gross only) or to the pooled dataset.
- The Northwest files list many plans as "NODE ..." Medicare Advantage contracts, employer plans and
  administrators (for example CHS Group Health Plan BCBST, HealthSmart, Prime Health), which map to "other".

### Rows dropped or flagged (data/processed/f4_flag_log.csv)
| Reason | Rows | Action |
|---|---|---|
| above_gross (negotiated dollar above the gross charge) | 219,699 | dropped |
| under_1_dollar (dollar amount under $1) | 973,149 | dropped |
| unparseable | 0 | dropped |
| gross_from_code (item had no gross; compared with the highest gross for the same code) | 169,553 | kept, flagged |
| no_gross_to_check (no gross anywhere for the code) | 2,099,277 | kept, flagged |
| methodology: fixed dollar / percent of charges / algorithm / per diem (negotiated rows) | 3,919,371 / 54,123,794 / 3,899,344 / 61,597 | only fixed dollar can be a headline price |

Most rows under $1 are in the Northwest files (Northwest 285,978, Oro Valley 280,195, Sahuarita 199,186) and
Valleywise (116,171: values from $0.01 to $0.99, labelled "fee schedule", for example professional-fee items
such as "PF I&D COMPLEX DRAINAGE WND" at $0.01). What these values mean is not known; they are dropped as
Table 9 requires. Mayo labels 51.7 million negotiated rows "percent of total billed charges" while also giving
a dollar figure (for example 90% of the gross charge); like Banner's, these are percent of charges and never a
headline price.

### Provisional H2 measures (data/processed/h2_provisional_by_procedure.csv)
Comparable rate = negotiated dollar, methodology fixed dollar, surviving the outlier rules, facility billing,
outpatient or both, canonical insurer. 16,401 comparable rows from 14 hospitals (9 Phoenix, 5 Tucson); 99
procedure-metro pairs with at least 2 hospitals (50 Phoenix, 49 Tucson).

| Measure | Phoenix | Tucson | Both metros (rule) |
|---|---|---|---|
| Median highest-to-lowest ratio (hospital medians) | **2.81** (IQR 2.39-5.36) | **1.63** (IQR 1.30-1.98) | **1.99** |
| Procedures with ratio of 2 or more | 40 of 50 | 9 of 49 | 49 of 99 |
| Same insurer across hospitals (sensitivity) | 3.43 | 1.59 | 2.50 |

- Cash below the median negotiated rate: **1 of 50 procedures (2%)** when the median hospital cash price is
  compared with the median comparable negotiated rate; 42 of 451 hospital-procedure pairs (9%) when each
  hospital's cash price is compared with its own median negotiated rate.
- Row-level ratio (single highest / single lowest rate) median 55; not a credible measure because of isolated
  very low rates, shown only to document why hospital medians are used.
- The largest ratios are surgical (prostate biopsy 39.7 and shoulder arthroscopy 15.0 in Phoenix, shoulder
  arthroscopy 14.9 in Tucson). A human should check a few of these rows in the source files, because a low
  rate can be a component or add-on price rather than the whole procedure.
- Sensitivity to the dictionary: adding 16 aliases and 3 rules for spellings in the TMC and Northwest files moved the
  pooled median from 2.13 to 1.99. The verdict depends on the accepted dictionary.

### Provisional verdict
On provisional data the pooled median across launch procedures and metros is 1.99, just under the rule of 2,
while Phoenix alone (2.81) meets it and Tucson alone (1.63) does not. **H2 is not resolved yet:** the result is
within the range that the payer dictionary can move. It becomes final after (1) both raters label the 200
strings with 85% or higher agreement, (2) disagreements are resolved and the dictionary is marked accepted,
and (3) the script is re-run. The team should also confirm with Dr. Li that "the median across the launch
procedures" means pooling both metros, as computed here, rather than deciding per metro. If the final pooled
median stays under 2, Table 13 says the project reframes around interpretation and provenance.

## Inter-rater test (not run yet)
- Sample: research/h2/make_irr_sample.py, seed **20261012**: 100 strings drawn with probability proportional
  to row count, then 100 drawn uniformly from the rest, shuffled (200 of the 2,502 strings).
- Files: research/h2/irr_rater_A.xlsx and irr_rater_B.xlsx (drop-down lists; CSV copies alongside),
  research/h2/labeling_guide.md, research/h2/irr_score.py (percent agreement, Cohen's kappa, disagreements).
- The rater files are empty; agreement has not been estimated.
