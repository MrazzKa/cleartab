# Launch procedure list (Feature 1, 50 procedures)

Built 2026-10-12. Files: data/processed/code_frequency.csv (every code with the number of usable H1
hospitals publishing a priced row), data/processed/procedure_selection.csv (the 50 and why),
data/processed/procedure_text.csv (plain names, synonyms, descriptions; written by the team, CMS and AMA
short descriptors used only as facts), data/processed/procedures.csv (loaded into the procedures table).

Reproduce: `PYTHONPATH=. .venv/bin/python research/procedures/procedures_frequency.py`, then
`python -m pipeline.select_procedures` and `python -m pipeline.build_procedures`.

## Method
- Start list: the 70 CMS-specified shoppable services, Table 3 of 84 FR 65524 (pipeline/cms70.py, text
  retrieved from federalregister.gov), plus every code in the 11 usable H1 files.
- CPT and HCPCS labels are counted as one code system (CPT is HCPCS Level I; HonorHealth labels CPT codes as
  HCPCS). Original labels are kept in the data.
- Selection rules are in the docstring of pipeline/select_procedures.py: four categories from Table 6 with
  quotas imaging 15, laboratory 15, endoscopy 8, outpatient surgery 12; exclusions for E&M, psychotherapy,
  obstetric delivery, inpatient MS-DRGs, oncology, child-only procedures, unlisted codes and blood draws.

## Result
- 50 procedures: 42 CMS shoppable codes + 8 most-published codes. 47 are published by at least 8 of the
  11 usable hospitals; 3 endoscopies (45391, 45330, 31622) by 7, because no other endoscopy reaches 8.
- Excluded CMS shoppable services and why: 13 E&M and psychotherapy codes (not in the four categories);
  59400, 59510, 59610 (obstetric delivery); 5 MS-DRGs 216, 460, 470, 473, 743 (inpatient); 55866 (cancer
  surgery, proposal 6.2 item 5); 42820 (children under 12); 93000, 93452, 95810, 97110 (not in the four
  categories); 77065, 80055, 81000, 66984, 66821 (fewer than 8 hospitals, and other codes filled the quota).

## Launch procedures published per hospital
| CCN | Hospital | Of 50 |
|---|---|---|
| 030010 | St. Mary's Hospital | 30 |
| 030011 | St. Joseph's Hospital (Tucson) | 30 |
| 030092 | HonorHealth Deer Valley Medical Center | 50 |
| 030038 | HonorHealth Scottsdale Osborn Medical Center | 50 |
| 030024 | St. Joseph's Hospital and Medical Center | 50 |
| 030036 | Chandler Regional Medical Center | 49 |
| 030030 | Abrazo Central Campus | 50 |
| 030022 | Valleywise Health Medical Center | 0 |
| 030103 | Mayo Clinic Hospital (Phoenix) | 0 |
| 030107 | Arizona Spine and Joint Hospital | 22 |
| 030064 | Banner - University Medical Center Tucson | 48 |
| 030065 | Banner Desert Medical Center | 47 |
| 030152 | Exceptional Community Hospital - Maricopa | 0 |
| 030153 | East Valley ER & Hospital | 48 |
| 030108 | The CORE Institute Specialty Hospital | 0 |

Carondelet (30 of 50) lacks most surgery and endoscopy codes; Arizona Spine and Joint (22) is a specialty
hospital. Exceptional publishes CPT codes labelled "CDM", so 0 match. Human review: a clinician or the
advisor should read the 50 plain names and descriptions before launch; the reading level was written to
8th grade but not measured with a tool.
