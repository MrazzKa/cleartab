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

Run 2026-10-13 on the 17 usable H1 hospitals (14 of them publish negotiated rates); updated the same day after
inter-rater round 1. Reproduce: `python -m pipeline.payers`, `python -m pipeline.normalize`,
`python -m research.h2.h2_provisional` (add `--payer-rule` for the sensitivity run below).

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
  all mapped by deterministic rules: 1,856 high confidence, 646 medium (each with a note, for example "no state
  given; read as BCBS of Arizona because the files are Arizona hospitals"). All rows are provisional.
- Changes after inter-rater round 1 (2026-10-13):
  - Brand words "UHC" and "BCBS AZ" / "BCBSAZ" in the payer column now match their insurer. This fixed 11
    strings the rules had missed, for example "UHC Navigate", "UHC Health Exchange", "NODE BCBS AZ MCR ADV" in
    the Northwest files and "BCBS AZ NETWORK" in Mayo.
  - New "network contract" rule (608 strings, all Mayo, medium confidence): when the payer is an employer
    plan, fund, administrator or an insurer that is not on the list, and the plan column names a listed
    insurer's contract ("AZ CIGNA [39]", "AZ AETNA ASA [1119]", "AZ BCBS [124]", "AZ UHC OPTUM [72]"), the row
    counts under that insurer. Evidence: in the Mayo file the plan column is the contract that sets the price;
    for MRI brain (70553) all 136 payer names under "AZ CIGNA [39]" carry the same rate ($2,341.86) and all 49
    under "AZ BCBS [124]" carry $2,545.50. The round 1 raters split on exactly this case (see below).
- Rental networks (MultiPlan, First Health, "Medical Rental"), workers compensation plans, government
  programs, IPAs, employers and small Medicare Advantage plans map to "other".
- Row coverage by canonical insurers (negotiated rows after outlier rules), target 60%
  (data/processed/f4_coverage.csv):
  - pooled, all 14 hospitals: **51.0%** (31,041,715 of 60,866,191; 12.8% before the round 1 changes);
  - pooled without Mayo: **66.7%** (6,033,682 of 9,047,178; was 66.0%);
  - per hospital: Arizona Spine and Joint 100%, HonorHealth Osborn 95.7%, HonorHealth Deer Valley 95.1%,
    Abrazo Central 90.6%, TMC 81.5%, Chandler Regional 78.8%, Valleywise 68.2%, St. Joseph's Phoenix 66.9%,
    Banner Desert 65.2%, **Banner UMC Tucson 58.9%, Sahuarita 57.1%, Mayo 48.3%, Northwest 44.9%, Oro Valley
    38.2%** (the last five are below 60%; Mayo was 3.5% before the network contract rule).
- Mayo has 51.8 million negotiated rows, more than five times all other hospitals together, and almost all
  of its payers are national third-party administrators and out-of-state plans. A pooled share is therefore
  decided by one file (51.0% with it, 66.7% without). The team should decide whether Table 9's 60% rule applies per hospital (then the five
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
outpatient or both, canonical insurer. 16,820 comparable rows from 14 hospitals (9 Phoenix, 5 Tucson); 99
procedure-metro pairs with at least 2 hospitals (50 Phoenix, 49 Tucson).

| Measure | Phoenix | Tucson | Both metros (rule) |
|---|---|---|---|
| Median highest-to-lowest ratio (hospital medians) | **2.81** (IQR 2.35-5.71) | **1.39** (IQR 1.25-1.86) | **1.92** (IQR 1.42-2.81) |
| Procedures with ratio of 2 or more | 40 of 50 | 6 of 49 | 46 of 99 |
| Same insurer across hospitals (sensitivity) | 3.43 | 1.57 | 2.50 |

- Cash below the median negotiated rate: **1 of 50 procedures (2%)** when the median hospital cash price is
  compared with the median comparable negotiated rate; 41 of 451 hospital-procedure pairs (9%) when each
  hospital's cash price is compared with its own median negotiated rate.
- Row-level ratio (single highest / single lowest rate) median 55; not a credible measure because of isolated
  very low rates, shown only to document why hospital medians are used.
- The largest ratios are surgical (prostate biopsy 39.7 and shoulder arthroscopy 15.0 in Phoenix, shoulder
  arthroscopy 14.9 in Tucson). A human should check a few of these rows in the source files, because a low
  rate can be a component or add-on price rather than the whole procedure.
- Sensitivity to the dictionary: adding 16 aliases and 3 rules for spellings in the TMC and Northwest files moved the
  pooled median from 2.13 to 1.99; the 11 brand-word fixes after round 1 (Northwest UHC and BCBS strings) moved
  it to 1.92, with Tucson falling from 1.63 to 1.39 as more Northwest rates became comparable.
- Sensitivity to the round 1 disagreement: with the network contract rule switched off
  (`--payer-rule`, data/processed/h2_payer_rule_by_procedure.csv) every H2 figure is identical (1.92 pooled,
  2.81 Phoenix, 1.39 Tucson, 1 of 50 cash). The rule only touches Mayo, and Mayo's rows for these contracts are
  labelled percent of charges, so none of them is a comparable fixed dollar rate. The rule decides coverage
  and what the product shows for Mayo, not the H2 verdict.

### Provisional verdict
On provisional data the pooled median across launch procedures and metros is 1.92, under the rule of 2, while
Phoenix alone (2.81) meets it and Tucson alone (1.39) does not. **H2 is not resolved yet:** the proposal does
not accept the dictionary below 85% inter-rater agreement, and round 1 reached 68%. It becomes final after
(1) round 2 reaches 85% or higher, (2) disagreements are resolved and the dictionary is marked accepted, and
(3) the script is re-run. Both readings of the rule that split the round 1 raters give the same H2 figures, so
the direction of the result (pooled under 2, Phoenix over 2, Tucson under 2) is not expected to change. The team should also confirm with Dr. Li that "the median across the launch
procedures" means pooling both metros, as computed here, rather than deciding per metro. If the final pooled
median stays under 2, Table 13 says the project reframes around interpretation and provenance.

## Inter-rater test
### Round 1 (2026-10-13): 68%, below the 85% target
- Sample: research/h2/make_irr_sample.py round 1, seed **20261012**: 100 strings drawn with probability
  proportional to row count, then 100 drawn uniformly from the rest, shuffled (200 of the 2,502 strings; 164 of
  the 200 come from the Mayo file).
- Two team members labelled the strings independently. Labels: research/h2/irr_round1_rater_A.csv and
  irr_round1_rater_B.csv; output: research/h2/irr_round1_score.txt.
- Rater B's file had 8 `raw_plan` cells changed by a find-and-replace ("Commercial" to "unknown"); the labels
  were not affected. Rows were matched by position and the original strings restored from the sample.
- **canonical_payer: 136 of 200 = 68.0%, Cohen's kappa 0.289.** plan_type: 197 of 200 = 98.5%, kappa 0.941.
  Mayo strings 111 of 164 (67.7%), other hospitals 25 of 36 (69.4%).
- The 64 canonical_payer disagreements by type (irr_score.py):
  - 50 "plan names insurer": the payer is an employer, fund or administrator and the plan column names a
    listed insurer (for example BOILERMAKERS NATIONAL FUND / AZ CIGNA [39]); rater A chose "other" (by the card
    issuer, as the round 1 guide said), rater B chose the insurer in the plan column. The guide did not
    address this case directly.
  - 5 "hospital name used as payer": rows from Banner - University Medical Center Tucson labelled Banner
    Health plans although neither string names Banner (for example Aetna / Broad Network).
  - 9 other: 6 rows where one rater chose "other" although the payer column names a listed insurer (for example
    CIGNA / ALL PRODUCTS, HUMANA BH / MEDICARE ADVANTAGE - MID-LEVEL), plus single cases (Oscar PPO / AZ CIGNA,
    a BCBS string without state, a BCBS contract labelled UnitedHealthcare).
- Diagnostic only, not a test result: with the first type removed, agreement on the other 150 strings is 136
  of 150 (90.7%). Against the current dictionary, rater A matches 137 of 200 and rater B 174 of 200.
- Decision: the dictionary is **not accepted** (proposal Table 9 and section 6.4, item 5: not accepted below 85%). The guide was
  rewritten with explicit rules for each disagreement type (research/h2/labeling_guide.md), the dictionary
  adopted the network contract rule on the evidence above, and a fresh sample is labelled in round 2.

### Round 2 (files ready, not labelled yet)
- Sample: make_irr_sample.py round 2, seed **20261013**, same method, drawn from the 2,302 strings not used in
  round 1. Files: research/h2/irr_round2_rater_A.xlsx and irr_round2_rater_B.xlsx (CSV copies alongside).
- Score with `python -m research.h2.irr_score` once both files are saved.
