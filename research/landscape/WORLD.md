# ClearTab - what the world does about fair prices and bill checking

Research date: 2026-11-04. Every fact has a source URL. "Not found" means I looked and could not confirm it. Numbers marked "computed" were calculated by me from the official CMS file named next to them, not copied from a published table. Several sources were search-result summaries of pages I could not open in full; those are marked "(secondary)" or "(verify)". Before anything goes on the poster, re-check the primary source.

---

## 1. Public US yardsticks a consumer app can use for free

### 1.1 What exists

| Yardstick | What it prices | 2026 key parameter | Where |
|---|---|---|---|
| Medicare Physician Fee Schedule (MPFS) | Professional (physician) services by CPT/HCPCS | Conversion factor (CF) $33.4009 non-QP; $33.57 (about 33.5675) QP. Final rule released 2025-10-31 | Final-rule summaries: https://www.acc.org/latest-in-cardiology/articles/2025/10/31/21/33/cms-releases-2026 , https://www.sirweb.org/publications/news/medicare-physician-fee-schedule-final-rule-for-2026-conversion-factor/ ; CF 33.4009 appears in the CMS file RVU26A (PPRRVU2026_Jan_nonQPP.csv, column CONV FACTOR) https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26a |
| OPPS / APC (hospital outpatient facility fee) | Facility part of outpatient hospital visits, imaging, surgery | OPPS CF $91.415 for CY 2026 (+2.6%); final rule 2025-11-21 | CMS fact sheet https://www.cms.gov/newsroom/fact-sheets/calendar-year-2026-hospital-outpatient-prospective-payment-system-opps-ambulatory-surgical-center ; ACR summary (secondary) https://edge.sitecorecloud.io/americancoldf5f-acrorgf92a-productioncb02-3650/media/ACR/Files/Medicare-Medicaid/HOPPS/CY2026-HOPPS-Final-Rule-ACR-Detailed-Summary.pdf |
| ASC payment system | Ambulatory surgery center facility fee | ASC CF $56.322 (quality reporters), $55.224 otherwise | ASCRS (secondary) https://www.ascrs.org/news/ascrs-news/2026-asc-final-rule-released |
| IPPS MS-DRG | Inpatient hospital stay per DRG | FY 2026 final rule CMS-1833-F; weights in Table 5; standardized amounts in Tables 1A-1E. Final standardized amount: not found in my searches (proposed-rule figures exist but must not be used) | https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps/fy-2026-ipps-final-rule-home-page |
| Clinical Laboratory Fee Schedule (CLFS) | Lab tests (e.g., 80053) - not in MPFS (status X in RVU file) | PAMA cuts delayed through 2026-12-31 by the Consolidated Appropriations Act, 2026 (secondary); CMS transmittal says MACs retrieve the CY 2026 CLFS on or after 2026-04-01 | https://www.cms.gov/medicare/medicare-fee-for-service-payment/clinicallabfeesched ; https://www.cms.gov/files/document/r13639cp.pdf ; https://www.pgmbilling.com/blog/labs-got-a-reprieve-on-pama-cuts-for-2026-but-2027-is-a-different-story/ |
| Ambulance Fee Schedule | Ground and air ambulance | CY 2026 ambulance inflation factor 2.0% | https://www.cms.gov/medicare/payment/fee-schedules/ambulance/afs-regulations-and-notices |
| MPFS Look-up Tool | Web lookup by code, national or MAC locality | Shows locality pricing via GPCIs; has a CPT click-through license | https://www.cms.gov/medicare/physician-fee-schedule/search/overview ; license page https://cms.gov/apps/physician-fee-schedule/search/search-criteria.aspx |

Note: ClearTab already has a local ground ambulance rate schedule PDF in data/raw/reference/ambulance (origin not checked in this research).

### 1.2 Arizona-local Medicare rate for a CPT code (MPFS)

Arizona is one statewide Medicare locality: MAC 03102 (Noridian JF), locality 00 "ARIZONA, STATEWIDE, ALL COUNTIES" (CMS file 26LOCCO.csv inside RVU26A).

2026 Arizona GPCIs (CMS file GPCI2026.csv, "Addendum E. Final CY 2026 GPCIs", inside https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip):
- Work GPCI 0.991 without the 1.0 floor, 1.000 with the floor
- Practice expense (PE) GPCI 0.969
- Malpractice (MP) GPCI 0.856

Formula (CMS PFS documentation https://www.cms.gov/apps/physician-fee-schedule/documentation.aspx):

`Payment = [ (work RVU x work GPCI) + (PE RVU x PE GPCI) + (MP RVU x MP GPCI) ] x CF`

Use the non-facility PE RVU when the service is in an office, and the facility PE RVU when it is in a hospital or ASC (then the hospital or ASC also bills its own facility fee under OPPS or ASC rates).

Worked examples (computed by me from PPRRVU2026_Jan_nonQPP.csv, CF 33.4009, work GPCI 1.000; verify against the Look-up Tool before publishing):

| Code | Non-facility (office) | Facility (physician part only) |
|---|---|---|
| 99213 | $93.25 | $56.67 |
| 99214 | $132.86 | $83.34 |
| 45378 | $368.12 | $161.31 |

Caveats:
- Whether the 1.0 work GPCI floor applies for a given 2026 date of service: not confirmed in my searches. With the 0.991 value results drop slightly. Check the Noridian JF fee files https://med.noridianmedicare.com/web/jfb/fees-news/fee-schedules/contractor-status-codes-c-status/2026-mpfs-contractor-code-status-c-fees
- The Medicare amount is the total allowed amount; the Medicare patient normally pays 20% of it. For a yardstick, show the allowed amount.
- Modifiers (26, TC, 50, 51), global surgery days and multiple-procedure rules change the number. The RVU file has the indicators; the rule engine must apply them or show "estimate".
- Hospital outpatient prices need OPPS (APC rate times the Arizona wage index adjustment for the labor share); that is a second calculation, not done here.

### 1.3 Licensing limits

- Medicare payment amounts, RVUs, GPCIs and CFs are US government data. A Florida AHCA license text says fee schedules, RVUs and conversion factors "are not assigned by the AMA, are not part of CPT" (secondary, via search result).
- CPT codes and descriptors are AMA copyright. The RVU file itself states "CPT codes and descriptions only are copyright 2026 American Medical Association". The CMS CPT click-through license limits use and sends other uses to the AMA (https://cms.gov/apps/physician-fee-schedule/search/search-criteria.aspx).
- AMA position: any organization that "uses, references or displays CPT content" is expected to get a license; CPT "must be licensed to be used in electronic products" (https://ama-assn.org/practice-management/cpt/licensing-cpt-ai-faqs). A Senate HELP letter reports a 2025 distribution rate of $18.50 per user plus a $1,050 annual fee (https://www.help.senate.gov/imo/media/doc/cassidy_letter_to_ama_on_cpt_monopoly.pdf, secondary). A patient group has sued the AMA over CPT copyright (https://www.patientrightsadvocate.org/blog/patientrightsadvocateorg-sues-american-medical-association-to-make-medical-billing-codes-freely-available-to-the-public).
- Whether a free, open-source consumer app that only shows code numbers (no AMA descriptors) next to a Medicare dollar amount needs a license: not found. Safe practice for ClearTab: keep the CMS RVU file in data/raw (like the NCCI/MUE tables), never commit descriptors, show the code number the user already has on their own bill plus team-written plain-English labels, and ask the AMA licensing team in writing before public launch. HCPCS Level II codes (letters A-V) are CMS-maintained and not AMA-owned.

### 1.4 Commercial prices as a multiple of Medicare

- RAND Round 5.1 (2020-2022 data, republished December 2024): employer plans paid hospitals 253% of Medicare in 2022 (state-level median); 254% in 2018 (Round 3), 246% in 2020 (Round 4). Inpatient facility about 255%; outpatient facility higher; professional services lower than facility. Covers more than 4,000 hospitals in 49 states and DC. Sources: https://www.rand.org/pubs/research_reports/RRA1144-2-v2.html (page returned 403 to my fetcher; figures from search summaries and the RAND FAQ https://www.rand.org/health/projects/hospital-pricing/round5/faq.html and news coverage https://www.news-medical.net/news/20240513/RAND-report-Hospital-prices-surge-above-Medicare-rates-in-2022.aspx).
- Arizona: Becker's tables list Arizona at 292% (overall) and 290% (inpatient), but the page does not say which RAND round, and I could not open it (403). Status: not verified. Get the number from the RAND supplementary state spreadsheet (employerPTP.org) before using it. URLs: https://beckershospitalreview.com/finance/medical-bills-paid-by-private-insurance-vs-medicare-comparison-by-state.html , https://beckershospitalreview.com/finance/inpatient-medical-bills-paid-by-private-insurance-vs-medicare-comparison-by-state.html
- Policy anchors that use Medicare as a yardstick: Oregon caps state employee plan hospital payments at 200% of Medicare in network and 185% out of network (2017 law) (https://milbank.org/publications/how-payment-caps-can-reduce-hospital-prices-and-spending-lessons-from-the-oregon-state-employee-plan). Montana's state plan moved to reference-based pricing in 2016, about 234% of Medicare on average; an independent study estimated $47.8 million saved FY2017-2019 (https://nashp.org/independent-analysis-estimating-the-impact-of-reference-based-hospital-pricing-on-the-montana-state-employee-plan/).

---

## 2. How other systems set prices and prevent surprise or wrong bills

| System | Who sets prices | Does the patient see an itemized bill? | Main protections |
|---|---|---|---|
| Germany (statutory, GKV) | EBM point values set by the Bewertungsausschuss (KBV + GKV-Spitzenverband). 2026 Orientierungswert 12.7404 cents per point (+2.8%), decided 2025-09-17 | Normally no; billing goes doctor -> KV -> fund. On request, a Patientenquittung from the doctor (free) or a cost statement from the fund (section 305 SGB V); hospitals must give it within 4 weeks on request | Sachleistung (benefits in kind); patient pays only legal co-payments |
| Germany (private, GOÄ) | Federal ordinance GOÄ (very old). BÄK and PKV agreed a new draft in 2025; updated 1,049-page draft sent to the Health Ministry 2026-07-31; still not law | Yes, private patients get a full itemized bill (GOÄ numbers and multipliers) | Fixed fee list with capped multipliers |
| France | Tarifs conventionnels negotiated between Assurance Maladie and doctors' unions. GP consultation EUR 30 since December 2024 (secondary sources) | Patient sees the base de remboursement and the reimbursement in the ameli account ("Mes paiements", about 27 months of history per ameli forum answers) | Secteur 1 doctors cannot charge above the tariff; tiers payant (no upfront payment) is mandatory in pharmacies but only "generalisable" for doctors since 2017 |
| Japan | National fee schedule (points; 1 point = 10 yen for insured care) revised every 2 years by Chuikyo/MHLW. FY2026 revision recommended 2026-02-13, start June 2026; base portion +3.09% | Yes. Hospitals issue a free itemized statement (meisaisho) with every receipt; may decline only with a filed "valid reason" | Monthly out-of-pocket cap (kogaku ryoyohi); raised from 2026-08-01, plus a new annual cap of about JPY 530,000 (secondary). Uninsured foreign patients: one hospital moves from 10 to 30 yen per point from 2026-09-01 |
| Canada | Provincial fee schedules negotiated with medical associations (Ontario: OHIP Schedule of Benefits, several 2026 editions) | Patients generally do not get bills for insured services | Canada Health Act bans extra-billing and user charges; federal transfer deducted dollar for dollar for violations |
| UK (NHS England) | NHS Payment Scheme unit and guide prices (2026/27 published March 2026, pay-award update August 2026). Prices are paid between NHS bodies | Residents: no bill. Overseas visitors: billed at 150% of tariff (non-EEA) | Free at point of use for residents; international students pay the Immigration Health Surcharge up front (student rate GBP 776 per year, secondary) |
| Switzerland | Since 2026-01-01 TARDOC (about 1,400 items) and Ambulante Pauschalen replaced TARMED; annual updates from 2027 | Yes. Under tiers garant the patient pays and is reimbursed; under tiers payant the patient must receive a copy of the bill (KVG art. 42 para 3) | Bills must be detailed and understandable; many insured do not know they have a right to the copy |
| Australia | Medicare Benefits Schedule (MBS) fee per item; doctors may charge more | Yes, patient pays the "gap" above the MBS rebate | Informed financial consent (written estimate before treatment); government Medical Costs Finder shows typical fees for over 1,300 services, but specialist participation was voluntary and very low (about 100 doctors) |
| Netherlands | NZa sets maximum tariffs in the regulated segment; hospital care in the free segment is negotiated by insurers | Insurer claim overviews (details: not found) | Compulsory deductible (eigen risico) EUR 385 in 2026, voluntary up to EUR 885 total |
| Maryland, US | HSCRC sets hospital rates; all payers including Medicare pay the same hospital rate; uncompensated care built into rates. AHEAD model runs 2026-2034 | Yes (US-style bills) | No price discrimination by payer; charity care and bad debt funded through rates. Federal review of Maryland's Medicare authority was reported; outcome not found |

Sources, in table order:
- Germany EBM: https://www.kbv.de/documents/infothek/rechtsquellen/bewertungsausschuss/gesamtverguetung/2026/ba-803-ow_2026.pdf ; Patientenquittung: https://www.gesetze-im-internet.de/sgb_5/__305.html , https://www.bundesgesundheitsministerium.de/themen/praevention/patientenrechte/patientenquittung.html ; GOÄ: https://www.bundesaerztekammer.de/neue-goae , https://www.pkv.de/verband/presse/pressemitteilungen/goae-entwurf-erfolgreiche-aktualisierung-als-basis-fuer-ein-zuegiges-verordnungsverfahren/
- France: https://www.allodocteurs.fr/pourquoi-une-consultation-chez-votre-generaliste-vous-coutera-bientot-30-euros-37267.html (secondary) ; tiers payant status https://www.groupama.fr/mutuelle-sante/conseils/tiers-payant/ , https://france-assos-sante.org/wp-content/uploads/2016/01/Fiche-C.8_Tiers-payant_2021.pdf ; ameli "Mes paiements" https://forum-assures.ameli.fr/questions/3257864-impossible-trouver-historique-remboursements/answers/8461196 ; base vs depassement example https://www.ag2rlamondiale.fr/faq/question?id=145
- Japan: fee revision https://www.nippon.com/en/news/yjj2026021300452 , https://english.adnkronos.com/2025/12/19/japan-to-raise-main-portion-of-medical-service-fees-by-3-09-pct ; meisaisho https://kouseikyoku.mhlw.go.jp/tokaihokuriku/shinsei/shido_kansa/shitei_kijun/h26/meisaisyo.html , https://www.dokkyomed.ac.jp/files/nmc/visit/statement_issuance.pdf ; caps https://www.city.minato.tokyo.jp/kuse/koho/minatomonthly/260801/changes-high-cost-medeical-expense-benefit-system.html , https://english.adnkronos.com/2026/07/18/japan-to-raise-caps-on-out-of-pocket-medical-expenses/ ; uninsured foreigners https://www.maebashi.jrc.or.jp/release/pdf/Important_Notice_English.pdf
- Canada: https://www.ontario.ca/page/ohip-schedule-benefits-and-fees ; CHA extra-billing summary (weak source, verify against the Act) https://metafilter.com/82905/Threatening-the-mercs-way-of-life ; Ontario law https://www.ontario.ca/laws/statute/04c05/v18
- UK: https://www.england.nhs.uk/publication/2026-27-nhs-payment-scheme/ ; 150% rule https://legislation.gov.uk/uksi/2015/238/regulation/7/2017-08-21 ; IHS (secondary) https://www.uni2study.com/articles/uk-student-visa-health-surcharge-fee-increase-2026
- Switzerland: https://www.bag.admin.ch/de/tardoc-und-ambulante-pauschalen ; bill copy https://www.bag.admin.ch/de/krankenversicherung-leistungen-und-tarife , https://www.parlament.ch/centers/eparl/curia/2019/20190046/Schlussabstimmungstext%202%20NS%20D.pdf
- Australia: https://www.health.gov.au/resources/apps-and-tools/medical-costs-finder ; IFC guide https://www.ama.com.au/sites/default/files/2024-10/AMA-Informed-Financial-Consent-Guide-October-2024.pdf ; low participation https://www.medicalrepublic.com.au/medical-costs-finder-to-automatically-display-fees/115249
- Netherlands: https://www.consumentenbond.nl/zorgverzekering/verplicht-eigen-risico ; NZa segments https://zoek.officielebekendmakingen.nl/stcrt-2019-27899.pdf
- Maryland: https://hscrc.maryland.gov:443/Pages/ahead-model.aspx ; same rate for all payers and UCC in rates https://hscrc.maryland.gov:443/Documents/pdr/ar/HSCRC-Disclosure-Report-FY-2016.pdf ; federal review https://www.yahoo.com/news/bumps-ahead-trump-administration-evaluating-123524818.html

### 2.1 International price comparison

iFHP 2024 International Healthcare Cost Comparison Report (with HCCI; published 2025-01-14; 2022 median claims data; 9 countries: Australia, Austria, Germany, Greece, New Zealand, South Africa, Spain, UK, USA for inpatient; outpatient adds Dominican Republic). Sources: https://healthcostinstitute.org/all-hcci-reports/international-comparisons-of-health-care-prices-from-the-2024-ifhp-study/ ; PDF https://healthcostinstitute.org/wp-content/uploads/images/pdfs/iFHP%20Cost%20Comparison%20Report%20final%20160125.pdf

US value vs range of the other countries shown in each chart (read from the PDF text; per-country labels could not be matched reliably from the extracted text, so only the US value and the min-max of the others are given):

| Inpatient procedure (2022, USD) | USA | Other countries, range |
|---|---|---|
| Coronary bypass | $89,094 | $10,734 - $36,352 |
| Spinal fusion | $59,582 | $7,334 - $32,756 |
| Coronary angioplasty (PCI) | $34,504 | $3,347 - $14,709 |
| Total hip replacement | $29,006 | $6,780 - $17,263 |
| Total knee replacement | $26,340 | $6,600 - $18,230 |
| Cholecystectomy | $17,817 | $3,198 - $9,295 |
| C-section | $13,601 | $2,419 - $8,910 |
| Appendectomy | $13,560 | $2,622 - $7,595 |

Outpatient charts (colonoscopy, MRI, CT 74160, endoscopy, cataract) are in the PDF (pages 13-15); I could not attribute the values to countries from the text, so they are left out. The US is not always highest there. Caveats from the report: figures are medians from member insurers and agencies, sources differ by country, they may not represent other plans in the same market.

Peterson-KFF Health System Tracker: higher prices, not higher use, explain high US spending; "services in the U.S. are consistently more expensive than in countries of similar size and wealth." https://www.kff.org/health-costs/how-do-healthcare-prices-and-use-in-the-u-s-compare-to-other-countries/ . Current figures from the tracker: not extracted.

---

## 3. Patient-side tools abroad worth borrowing

| Tool | What it does | Idea for ClearTab |
|---|---|---|
| Germany Patientenquittung (section 305 SGB V) | Plain list of services and costs, on request | One-tap "ask for itemized bill" letter, with a checklist of what must be on it |
| France ameli "Mes paiements" | Each visit shows amount paid, base de remboursement, amount reimbursed, and the gap above base | Show each bill line as three numbers: charged, a public yardstick (Medicare), what the plan allowed |
| Japan meisaisho and receipts | Free itemized statement with points per item; one national price list | "Points view": every line converted to a multiple of Medicare, so lines can be compared |
| Switzerland tiers payant copy | Patient gets a copy of what the insurer was billed | Match bill to EOB (ClearTab F7 already does this); tell the user they have a right to the itemized copy |
| Australia Medical Costs Finder and informed financial consent | Typical fees and gaps per MBS item; written estimate before care | ClearTab F11 "what bills to expect" plus a pre-care estimate request script. Lesson: voluntary provider reporting failed (about 100 doctors), mandatory data works better - ClearTab uses mandatory MRF data |
| Maryland HSCRC | Same hospital price for every payer | Poster contrast: in Arizona the same code has many prices at the same hospital |

Sources as in section 2.

---

## 4. International students in the US

- Liu et al. 2023, International Journal of Public Health (143 international students, one Midwest university, early 2022): only 21.68% and 22.38% could correctly compute their own costs in two scenarios (surgery, office visit); more than half could not define coinsurance, HMO, out-of-pocket maximum, copay and network; 57.34% often feel confused about their insurance; 28.67% said lack of understanding stopped or delayed care (15.38% "maybe"). Knowledge was linked to continent of origin (North America higher) and 5+ years in the US. Limitations: about 20% response rate, one campus, convenience sample (a reviewer flagged over-generalization). https://doi.org/10.3389/ijph.2023.1605788 , https://pmc.ncbi.nlm.nih.gov/articles/PMC10588627/
- Common confusions (from the study and system contrasts above): students from Canada, UK, Japan, Germany or France come from systems where the patient never sees, or rarely checks, an itemized bill, and where price is fixed nationally. US concepts with no home equivalent: deductible, coinsurance, network, balance billing, EOB "not a bill", facility fee separate from physician fee.
- University of Arizona: international students on non-immigrant visas with at least one unit must carry the Student Health Insurance Plan unless exempted; auto-enrolled and billed each semester; Fall 2026 coverage 2026-08-16 to 2026-12-31; spring 2027 premium shown as $1,838 on an early-arrival form. https://health.arizona.edu/international-students-exemptions , https://news.arizona.edu/uannounce/fall-2026-open-enrollment-student-healthcare-options , https://health.arizona.edu/sites/default/files/2026-05/Spring_EarlyArrival_Application_2271.pdf . SHIP benefit details (deductible, coinsurance) for 2026-27: not found.
- J-1 visitors: 22 CFR 62.14 minimums widely cited as $100,000 per accident or illness, deductible at most $500, evacuation $50,000, repatriation $25,000 (university summaries, e.g. https://isss.umbc.edu/j-1-visa-status-and-mandatory-health-insurance ; check current eCFR text).
- Newer (2024-2026) research specifically on international students and US medical bills: not found.

---

## 5. Product features ClearTab could add

1. Medicare yardstick per bill line (highest value, feasible before Dec 1)
   - For each line with a CPT/HCPCS code: Arizona Medicare allowed amount (MPFS locality 00, facility or non-facility by place of service), and "your plan allowed = N x Medicare". Labs from CLFS, ambulance from AFS, hospital outpatient facility lines from OPPS (second step).
   - Data: CMS RVU26A/B/C/D, GPCI2026, CLFS, AFS, OPPS Addendum B. Public data; keep files in data/raw, do not commit CPT descriptors.
   - Rule, not an LLM: deterministic formula, provenance (file name, release date) on screen. Use RAND 253% only as context text, never as a finding.
   - Risk: modifiers and bundling; show "estimate" when an indicator is not handled.

2. Fair price band for Arizona (combines yardstick and existing data)
   - Band = Medicare amount (floor), in-state negotiated p10-p90 from the 19 hospital MRFs for the same code, and the hospital's own cash price. Flag a line as "worth asking about" when allowed or self-pay amount is above the band, never as "error".
   - Feasibility: data already loaded; needs code-level join and the F4 rules (drop non-dollar rows).

3. Itemized bill and copy right letter (borrowed from Germany, Japan, Switzerland)
   - Add to F8 dispute kit: request for an itemized statement with codes, units, dates, and the EOB match. Arizona or federal legal right to an itemized bill: not found in this research - word it as a request, not a legal demand, until a law is confirmed.

4. "What this costs elsewhere" card (poster and education only)
   - For the 8 inpatient procedures in the iFHP 2024 report, show US 2022 median vs the range in 8 other countries, next to Arizona MRF prices. Big caveats: 2022 data, different sources per country, facility definitions differ, not a price the user can get. Not shown on individual bill checks.

5. International student mode
   - Glossary mapped to home-system concepts ("in Japan the receipt shows points; here the EOB shows allowed amount"), a worked SHIP example, and the "what you owe" calculator. Fits R3 usability: recruit international students as a subgroup (IRB needed). Evidence: 78% could not compute their own cost (Liu 2023).

## 6. Framing for poster and paper

- "Everywhere else, the bill is checked before it reaches the patient." Germany, Canada, UK residents rarely see a bill; Japan, France and Switzerland give the patient a standard, readable statement priced from one national list; Maryland gives one hospital price for all payers. In Arizona the patient is the last auditor of a bill priced from many private contracts.
- ClearTab moves two of those safeguards into software: a public price list as the yardstick (Medicare, like EBM/MBS/Japanese points) and a standard itemized check (like meisaisho/Patientenquittung).
- Research angle: share of bill lines and MRF negotiated rates above 2x, 3x, 4x the Arizona Medicare amount; compare with RAND state figure once verified. Reproducible from committed code, since CMS inputs are public.
