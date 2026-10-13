# Payer labeling guide (inter-rater test)

Two team members label the same 200 strings **independently**: Rater A fills `irr_rater_A.csv`, Rater B fills
`irr_rater_B.csv`. Do not discuss strings, do not open the other file and do not look at
`data/processed/payer_aliases.csv` (the provisional rule-based mapping) until both files are saved.

For each row read `raw_payer` and `raw_plan` (and `hospital` for context) and fill in:
- `canonical_payer`: exactly one value from list 1, spelled as shown.
- `plan_type`: exactly one value from list 2.
- `notes`: optional; write why when you were unsure.

## 1. canonical_payer
| Value | Use when the insurer that issues the member's card is... | Example string |
|---|---|---|
| Aetna | Aetna or an Aetna-branded plan | `Aetna` / `Medicare Advantage` |
| Blue Cross Blue Shield of Arizona | BCBS of Arizona (AZ Blue) | `BCBS - AZ` / `Commercial|MaricopaFocus` |
| Cigna | Cigna | `Cigna Healthcare of Arizona, Inc.` / `LocalFlex` |
| UnitedHealthcare | UnitedHealthcare, incl. UHC Community Plan (AHCCCS) | `Unitedhealthcare` / `Exchange` |
| Humana | Humana | `HUMANA` / `HUMANA COMMERCIAL` |
| Banner Health plans | Banner University Family Care, Banner Medicare Advantage, Banner University Health Plans | `Banner University Health Plan` / `AZ Medicaid - AHCCCS` |
| Mercy Care | Mercy Care (AHCCCS or Mercy Care Advantage) | `Mercy Care` / `Mercy Care Advantage` |
| Health Choice Arizona | Health Choice Arizona | `Health Choice` / `Medicaid|All Plans` |
| Centene (Arizona Complete Health, Ambetter, Health Net, Wellcare) | Any Centene brand: Arizona Complete Health, Ambetter, Health Net, Wellcare, Allwell | `Ambetter` / `Az Complete Exchange` |
| Molina | Molina, incl. Molina Complete Care | `MOLINA` / `MOLINA COMPLETE CARE MEDICAID` |
| Oscar | Oscar Health | `Oscar Health Plan` / `Exchange` |
| other | Any other insurer, a provider network or IPA, a rental network, workers compensation, government programs, an employer, or you cannot tell | `MultiPlan` / `Commercial|All Plans` |

Rules: a rental or access network (MultiPlan, First Health, "Medical Rental") is **other** even when the payer
column names a big insurer. Workers compensation plans are **other**. Choose by the card issuer, not by the
company that owns a provider group.

## 2. plan_type
| Value | Meaning | Example plan string |
|---|---|---|
| commercial | employer or individual plan that is not marketplace | `Commercial|PPO` |
| medicare advantage | Medicare Advantage or a Medicare/Medicaid dual plan | `Medicare|All Plans` |
| medicare supplement | Medigap / Medicare supplement | `Medicare Supplemental Senior Preferred` |
| ahcccs | Arizona Medicaid (AHCCCS) incl. ALTCS / LTC | `Medicaid Managed Care Plan` |
| marketplace | ACA exchange / HIX / individual marketplace | `Connect (IFP) Exchange` |
| government | TRICARE, VA Community Care, federal prison | `VA Community Care Network` |
| workers comp | workers compensation | `BCBSAZ Workers Comp` |
| rental network | rental or access network | `Medical Rental` |
| unknown | cannot tell from the strings | `Plotkin Health` |

## Time
About 1 to 1.5 hours per rater for 200 rows (20 to 30 seconds per row). When both files are saved, run
`.venv/bin/python research/h2/irr_score.py`. Disagreements are then resolved together and the agreed values
are written into `data/processed/payer_aliases.csv` with rater_status = accepted.
