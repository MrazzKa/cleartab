# Accuracy check against hospital phone quotes (proposal Section 4.2, Table 14: Nov 21)

Goal: for at least 10 procedure-hospital pairs, compare the figure ClearTab displays with the figure the hospital
gives when asked by phone. The ground truth is the hospital's own answer.

## Pairs (research/accuracy_check/phone_check.csv, chosen by make_pairs.py)
Rule: 10 commonly shopped launch procedures in a fixed order; each assigned to a different hospital that
publishes a cash price, balancing the two metros. All pairs use the **cash price** (self-pay), because a cash
quote does not require an insurance ID and can be asked without personal data.

| # | Metro | Hospital | Procedure (CPT) | Displayed cash price |
|---|---|---|---|---|
| 1 | Tucson | St. Mary's Hospital | knee MRI (73721) | $10,290.00 |
| 2 | Phoenix | Valleywise Health Medical Center | colonoscopy (45378) | $1,141.19 |
| 3 | Tucson | St. Joseph's Hospital (Tucson) | head CT scan (70450) | $4,495.50 |
| 4 | Phoenix | St. Joseph's Hospital and Medical Center | comprehensive metabolic panel (80053) | $131.41 |
| 5 | Phoenix | Chandler Regional Medical Center | screening mammogram (77067) | $182.24 |
| 6 | Tucson | Banner UMC Tucson | CT of belly and pelvis with contrast (74177) | $428.87 |
| 7 | Phoenix | HonorHealth Scottsdale Osborn | complete blood count with differential (85025) | $281.00 |
| 8 | Phoenix | Banner Desert Medical Center | abdominal ultrasound (76700) | $277.76 |
| 9 | Phoenix | East Valley ER & Hospital | gallbladder removal, laparoscopic (47562) | $1,022.22 |
| 10 | Phoenix | Arizona Spine and Joint Hospital | knee arthroscopy, meniscus (29881) | $3,207.64 |

Figures are the median of the hospital's published cash items for that code, as shown by the API on
2026-10-12. Re-run make_pairs.py right before calling so the CSV holds what the site shows that day.

## Call script (caller states they are a student; no personal or insurance details are given)
1. "Hello, I am a student at the University of Arizona working on a class project about hospital prices. I am
   not a patient and I will not give any personal information. Could I ask a pricing question, or which
   department handles self-pay estimates?"
2. "If someone paid cash with no insurance, what would the hospital charge for CPT code [code], [plain
   procedure name], as an outpatient?"
3. "Does that amount include the radiologist's or doctor's fee, or is that billed separately?"
4. "Does it include anything else, such as contrast, anesthesia, facility fee or supplies?"
5. "Is there a prompt-pay or self-pay discount on top of that?"
6. "Thank you. May I note your department's name? I will not record your personal name."
If the hospital will not quote without a patient account or a doctor's order, record "no quote" and the reason;
that is a result, not a failure.

## Recording (columns in phone_check.csv)
hospital, ccn, phone, metro, code, procedure, displayed_price, displayed_type, **quoted_price**,
**what_was_included**, **date**, **notes**, source_url, retrieved_at. Do not record the name of the person spoken
to. Two team members review each row.

## Analysis
Per pair: quoted minus displayed, in dollars and percent; flag whether the quote includes the physician fee.
Report: number of pairs with a quote, median absolute percent difference, share within 10% and within 25%, and
every "no quote" with the reason. No pair is dropped from the report.

## Timing
About 15-20 minutes per call including hold time; 10 calls about 3-4 hours, spread over two weekdays
during business hours. Owner suggestion: Artyom (data) calls, Timur reviews.
