# Launch procedure list (Feature 1, 50 procedures)

Built 2026-10-12. Files: data/processed/code_frequency.csv (every code with the number of usable H1
hospitals publishing a priced row), data/processed/procedure_selection.csv (the 50 and why),
data/processed/procedure_text.csv (plain names, synonyms, descriptions; written by the team, CMS and AMA
short descriptors used only as facts), data/processed/procedures.csv (loaded into the procedures table).

Reproduce: `PYTHONPATH=. .venv/bin/python research/procedures/procedures_frequency.py`, then
`python -m pipeline.select_procedures` and `python -m pipeline.build_procedures`.

## Method
- Start list: the 70 CMS-specified shoppable services, Table 3 of 84 FR 65524 (pipeline/cms70.py, text
  retrieved from federalregister.gov), plus every code in the 17 usable H1 files.
- CPT and HCPCS labels are counted as one code system (CPT is HCPCS Level I; HonorHealth labels CPT codes as
  HCPCS). Original labels are kept in the data.
- Selection rules are in the docstring of pipeline/select_procedures.py: four categories from Table 6 with
  quotas imaging 15, laboratory 15, endoscopy 8, outpatient surgery 12; exclusions for E&M, psychotherapy,
  obstetric delivery, inpatient MS-DRGs, oncology, child-only procedures, unlisted codes and blood draws.

## Result
- 50 procedures: 45 CMS shoppable codes + 5 most-published codes (chest x-ray 1 and 2 views, flexible
  sigmoidoscopy with and without biopsy, ultrasound-guided joint injection).
- All 50 are published by at least 9 of the 17 usable hospitals, so the fallback thresholds (step C) were not
  needed.
- History (same rules each time, all reproducible): with 11 usable hospitals the list held 72114 and 10060;
  adding Valleywise brought in the CMS codes 77065 and 66984; adding Mayo brought in 66821 in place of 10140;
  adding TMC and the Northwest hospitals brought in 45331 in place of 31622 (bronchoscopy). At that step 51798
  (bladder volume by ultrasound) also became eligible as "outpatient surgery" because of its code range; it is
  a measurement, not surgery, and was added to the exclusions.
- CMS shoppable services not selected, and why:
  - 13 evaluation and management and psychotherapy codes (90832-90853, 99203-99205, 99243-99244, 99385-99386):
    not in the four categories.
  - 59400, 59510, 59610: obstetric delivery. 216, 460, 470, 473, 743: inpatient MS-DRGs (still searchable
    later, not in the launch list). 55866: cancer surgery (proposal 6.2 item 5). 42820: children under 12.
  - 93000, 93452, 95810, 97110: not in the four categories.
  - 80055, 81000: fewer than 8 hospitals.

## Launch procedures published per hospital
| CCN | Hospital | Of 50 |
|---|---|---|
| 030010 | St. Mary's Hospital | 30 |
| 030011 | St. Joseph's Hospital (Tucson) | 30 |
| 030006 | Tucson Medical Center | 50 |
| 030085 | Northwest Medical Center | 45 |
| 030114 | Oro Valley Hospital | 44 |
| 030148 | Northwest Medical Center Sahuarita | 44 |
| 030064 | Banner - University Medical Center Tucson | 46 |
| 030092 | HonorHealth Deer Valley Medical Center | 50 |
| 030038 | HonorHealth Scottsdale Osborn Medical Center | 50 |
| 030024 | St. Joseph's Hospital and Medical Center | 50 |
| 030036 | Chandler Regional Medical Center | 48 |
| 030030 | Abrazo Central Campus | 50 |
| 030022 | Valleywise Health Medical Center | 50 |
| 030103 | Mayo Clinic Hospital (Phoenix) | 50 |
| 030107 | Arizona Spine and Joint Hospital | 19 |
| 030065 | Banner Desert Medical Center | 44 |
| 030153 | East Valley ER & Hospital | 48 |
| 030152 | Exceptional Community Hospital - Maricopa | 0 |
| 030108 | The CORE Institute Specialty Hospital | 0 |

Carondelet (30 of 50) lacks most surgery and endoscopy codes; Arizona Spine and Joint (19) is a specialty
hospital. Exceptional publishes CPT codes labelled "CDM", so 0 match; CORE is non-standard. Human review: a clinician or the advisor should read the 50 plain names and descriptions
before launch. Reading level, measured with research/readability.py (Flesch-Kincaid with an approximate
syllable counter): descriptions average grade 4.7, highest 7.6, none above grade 8 (54 texts, incl. 4 no longer selected).
