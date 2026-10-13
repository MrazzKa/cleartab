# H3 usability study - draft plan (for Dr. Li)

Status: DRAFT for discussion. Data collected for publication only after IRB approval with Dr. Li as PI
(proposal 4.3). Until then sessions are coursework and are reported as such.

## Hypothesis and design
H3 (proposal Table 13): users shown the three price types with a plain-language explainer identify the price
that applies to them more often than users shown the same figures without it, and can name a next action.
**Between-subjects**, two arms, random assignment by a pre-generated list (block size 4):
- Arm A, explainer: the results screen as specified in docs/results_screen_spec.md.
- Arm B, no explainer: the same screen with the explainer box and the in-row methodology hints removed.
Everything else (data, order, layout, wording of tasks) is identical. Sessions are 20-25 minutes, one at a time,
in person or by video, on the participant's own phone where possible (360 px target).

## Tasks (same 5 for both arms, fixed scenarios, real data from the local database)
1. "You have no insurance and need a knee MRI. Your ZIP is 85006. Which number on the screen is the price you
   would most likely pay at the first hospital?" (correct answer: the cash price)
2. "You have UnitedHealthcare through work. For the same scan, which number is the rate your plan agreed with
   [hospital]?" (correct: the negotiated rate, not the list price)
3. "At [hospital], your plan shows 'percent of charges, not a dollar amount'. What does that mean for you?"
   (correct: no dollar figure is published for this plan; ask the hospital)
4. "Does this price include the doctor's fee?" (correct: no, facility charge only)
5. "Which hospital would you call first, and what would you ask?" (open; scores the secondary measure)

## Measures
- **Primary:** correct identification of the applicable price, scored against the database (tasks 1-4,
  each correct / incorrect by a fixed key written before the study; per-participant share correct, and task 1
  alone as the pre-specified primary binary outcome).
- **Secondary:** names a specific hospital they would call (task 5, yes / no), scored by two team members
  independently.
- Time on task (seconds, from task read to answer) and errors (wrong taps, back-tracks) per task.
- System Usability Scale (10 items, standard wording).
- Perceived usefulness and trust: 4-6 items adapted from ResQue (Pu, Chen and Hu, 2011), for example
  "The prices shown were useful to me", "I trust the prices shown", 5-point agreement scale.
- Decision confidence: "How confident are you that you know what you would pay?" (5-point).
- Distress check (proposal 6.2 item 6): "Compared with before this session, how do you feel about getting
  this care?" (less likely / same / more likely). Any "less likely" is logged as a blocking defect.

## Participants and recruitment (proposal 2.3)
Three channels in parallel: University of Arizona students and staff who have paid out of pocket for care
(dental, urgent care, imaging); community clinics serving uninsured patients in Tucson; one hospital patient
financial counselor reached through a billing department. If the third channel gives no participant by the
Table 14 date, the study runs on the first two and says so. **No payment or other incentive.** Inclusion: 18 or
older, has paid or expects to pay for care out of pocket. No clinicians are required.

## Data handling
Only participant codes (P01, P02, ...) are stored, with arm, answers, times, scores and questionnaire values.
No names, contact details, insurance IDs or health details. Notes are written, not audio-recorded (6.5).
Participant notes are never entered into an AI tool (11.2 item 16.5).

## Sample size
**To be fixed with Dr. Li.** Power note for the primary binary outcome (two-sided alpha 0.05, power 0.80,
two-proportion z-test, equal arms; effect sizes below are assumptions for planning, not data): 39 per arm to
detect 50% vs 80% correct; 58 per arm for 50% vs 75%; 82 per arm for 60% vs 80%; 32 per arm for 60% vs 90%.
The empathy study's 1 in 9 failure is too small to estimate the baseline. A realistic semester sample (5-15
per arm by the Nov 7 milestone) can only detect very large differences, so the course report should present
H3 as a pilot with effect sizes and confidence intervals; a powered study would continue after December.

## Decision rule (Table 13, unchanged)
Ship the explainer as a blocking requirement if it improves correct identification. If neither arm reaches an
acceptable rate (threshold to be agreed with Dr. Li before the first session), redesign before any public beta
and promote the natural-language layer (Table 12 priority 4).
