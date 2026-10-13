# Payer labeling guide (inter-rater test, round 2)

Two team members label the same 200 strings **independently**: Rater A fills `irr_round2_rater_A.xlsx`, Rater B
fills `irr_round2_rater_B.xlsx` (open in Excel or Google Sheets; the yellow columns have drop-down lists). The CSV
copies hold the same rows for anyone without Excel. Do not discuss strings, do not open the other file and do not
look at `data/processed/payer_aliases.csv` (the provisional rule-based mapping) until both files are saved.
Do not edit the `raw_payer`, `raw_plan` or `hospital` cells (no find-and-replace on the sheet).

For each row read `raw_payer` and `raw_plan` (and `hospital` for context only) and fill in:
- `canonical_payer`: exactly one value from list 1, spelled as shown.
- `plan_type`: exactly one value from list 2.
- `notes`: optional; a few words when you were unsure.

Round 1 (2026-10-13) reached 68% agreement. Most disagreements came from one rule that the round 1 guide left
open (rule 3 below), so the rules are now written out in full.

## Rules for canonical_payer, applied in this order
1. **Rental or access networks and workers compensation are always other.** MultiPlan, PHCS (Private
   Healthcare Systems), First Health, "Medical Rental", Plotkin, NHSI, and any "Work Comp" plan: choose
   `other`, even when a listed insurer appears in the string.
2. **The payer column names a listed insurer:** choose that insurer, whatever the plan column says. Brand names
   that count are in the table below (for example UHC, UnitedHealthcare Community Plan and APIPA are
   UnitedHealthcare; Blue Cross Blue Shield or BCBS with no other state named is Blue Cross Blue Shield of
   Arizona).
3. **The payer column is an employer, union fund, trust, school district, state plan, administrator (TPA) or an
   insurer that is not on the list, and the plan column names a listed insurer** (for example
   `BOILERMAKERS NATIONAL FUND` / `AZ CIGNA [39]`, `MERITAIN HEALTH` / `AZ AETNA ASA [162]`,
   `ROCHESTER PUBLIC SCHOOLS` / `AZ BCBS BLUE CARD [1018]`): choose **the insurer named in the plan column**.
   Reason: in these files the plan column is the hospital's contract, and the contract sets the price. In the
   Mayo file all 136 payers under `AZ CIGNA [39]` have exactly the same rate for each procedure.
4. **Neither column names a listed insurer:** choose `other`. Do not use knowledge of who owns whom: UMR,
   Optum, Surest, All Savers, Oxford, Sierra Health and Life, Health Plan of Nevada, Meritain, Anthem and
   Wellpoint are `other` unless rule 2 or 3 applies.
5. **Never use the hospital column to choose the payer.** A row from a Banner hospital is not Banner Health
   plans unless the payer or plan column says Banner.
6. Ignore numbers in square brackets such as `[91160093]`.
7. If you still cannot decide, choose `other` and write a note.

## 1. canonical_payer values
| Value | Brand names that count | Example string |
|---|---|---|
| Aetna | Aetna, Aetna Medicare | `Aetna` / `Medicare Advantage` |
| Blue Cross Blue Shield of Arizona | BCBS AZ, AZ Blue, Blue Cross Blue Shield, BCBS (no other state), Blue Card | `BCBS - AZ` / `Commercial|MaricopaFocus` |
| Cigna | Cigna, Cigna LocalFlex, Cigna LifeSource | `Cigna Healthcare of Arizona, Inc.` / `LocalFlex` |
| UnitedHealthcare | UnitedHealthcare, United Healthcare, UHC, UHC Community Plan, APIPA | `Unitedhealthcare` / `Exchange` |
| Humana | Humana | `HUMANA` / `HUMANA COMMERCIAL` |
| Banner Health plans | Banner University Family Care, Banner Medicare Advantage, Banner University Health Plans | `Banner University Health Plan` / `AZ Medicaid - AHCCCS` |
| Mercy Care | Mercy Care, Mercy Care Advantage | `Mercy Care` / `Mercy Care Advantage` |
| Health Choice Arizona | Health Choice | `Health Choice` / `Medicaid|All Plans` |
| Centene (Arizona Complete Health, Ambetter, Health Net, Wellcare) | Arizona Complete Health, Ambetter, Health Net, Wellcare, Allwell, Care1st | `Ambetter` / `Az Complete Exchange` |
| Molina | Molina, Molina Complete Care, Magellan Complete Care (Medicaid) | `MOLINA` / `MOLINA COMPLETE CARE MEDICAID` |
| Oscar | Oscar Health | `Oscar Health Plan` / `Exchange` |
| other | everything else (rules 1, 4 and 7) | `MultiPlan` / `Commercial|All Plans` |

## 2. plan_type values
Use the first line that matches the words in either column.
| Value | Choose when the strings say | Example plan string |
|---|---|---|
| rental network | a rental or access network (rule 1) | `Medical Rental` |
| workers comp | workers compensation | `BCBSAZ Workers Comp` |
| medicare supplement | Medigap, Medicare supplement | `Medicare Supplemental Senior Preferred` |
| ahcccs | AHCCCS, Medicaid, ALTCS, LTC | `Medicaid Managed Care Plan` |
| medicare advantage | Medicare, Medicare Advantage, MA, MCR ADV, dual, federal retiree plans that say Medicare | `Medicare|All Plans` |
| marketplace | Exchange, HIX, Marketplace, IFP, QHP | `Connect (IFP) Exchange` |
| government | TRICARE, VA, Veterans, federal prison | `VA Community Care Network` |
| commercial | an employer, union fund, trust, administrator or insurer plan with none of the words above | `Commercial|PPO` |
| unknown | self pay, or the strings do not say what kind of payer it is | `Plotkin Health` |

## Time
About 1 hour per rater for 200 rows (20 to 30 seconds per row). When both files are saved, run
`.venv/bin/python -m research.h2.irr_score` (reads the two round 2 .xlsx files). Disagreements are then
resolved together and the agreed values are written into `data/processed/payer_aliases.csv` with
rater_status = accepted.
