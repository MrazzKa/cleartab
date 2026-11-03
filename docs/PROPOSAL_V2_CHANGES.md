# Proposal revision 2.0: what changes (draft for the team, 2026-11-02)

The signed proposal (v1.0, 2026-09-25) stays the record of the original plan. Revision 2.0 is re-signed by the
team, Dr. Li and the instructor. This file lists, section by section, what the revision changes and why, so each
section author can rewrite their part.

## Title and executive summary (Timur)
- New title: "ClearTab: checking hospital bills against published prices and federal billing rules in Arizona".
- One-paragraph reason for the change: H2 not met (median ratio 1.92, 95% CI 1.82-2.39); Campus Health insurance
  office interview (2026-10-26) and KFF Health Care Debt Survey (2022: 41% of adults have medical or dental debt;
  44% of them did not pay a bill in full because they were not sure it was correct) point to the problem after
  care. Instructor approval of a change of direction within the topic: 2026-10-27.

## Section 2 User and market research (Timur, Nikita)
- Add the Campus Health interview (role only, permission to quote by role).
- Add KFF evidence (cite the survey pages; verify each figure against the KFF page before submission).
- Competitors to add: insurer member portals with cost estimators (UnitedHealthcare), careroute.ai (hospital
  financial assistance guides), Dollar For (nonprofit charity care help), bill negotiation services. Position:
  open, free, every finding traceable to a published rule or price, nothing stored.

## Section 3 Features (each owner rewrites their feature)
| v2 | Feature | Owner | Replaces / keeps |
|---|---|---|---|
| F7 | Bill check (rule engine) | Timur (rules), Danil (API) | new core |
| F8 | Dispute kit (letter, phone script) | Nikita | evolves v1 F6 call summary |
| F9 | Financial assistance finder | Artyom (data), Nikita (UI) | new core |
| F10 | Read my documents (optional, consent) | Danil | new |
| F1-F5 | Price search, comparison, pipeline, normalization, completeness | as v1 | kept as reference layer |
Parameter tables for F7-F10 come from docs/PLAN_V2.md and the code (billcheck/).

## Section 4 Hypotheses and evaluation (Timur)
- H1 and H2 are reported as tested (H1 met; H2 not met, reported with intervals per Dr. Li).
- New, with decision rules fixed before the confirmatory tests:
  - **H4 (R2) AI alone is not enough.** On a confirmatory set of synthetic EOB-bill pairs (new seed, written before
    any result on it is seen), the best open-weights model reading the documents alone detects planted errors
    with lower sensitivity than the rule engine with model reading (hybrid). Decision rule: if the best model
    alone is within 5 percentage points of the hybrid on sensitivity and specificity, the product may use the
    model as the checker with the rules as a verifier; otherwise the rules stay the only source of findings.
    The pilot run of 2026-11-02 (seed 20261102) was seen before this rule was written and is reported as
    exploratory only.
  - **H5 (R3) the tool helps people act.** Between subjects, synthetic bill with one planted error. Primary:
    correct amount owed identified. Secondary: error spotted, next action named. Decision rule: ship the guided
    flow as default if the tool arm beats the control arm on the primary measure; sample size fixed with Dr. Li.
  - **H6 (R1) assistance policies differ in ways that matter.** Statewide collection of financial assistance
    policies; reported descriptively (free-care threshold, discount tiers, insured eligibility, application
    window, published or not). No yes/no rule; this is a census.
- Accuracy check (section 4.2) becomes: findings on 10 real, consenting users' bills, with names removed, reviewed
  by the Campus Health insurance office or a billing professional.

## Section 5 Timeline (Danil)
Nov 9 mid-semester (working prototype) / Nov 14 second-reader check of assistance policies done / Nov 16 R2
confirmatory run / Nov 18 poster draft / Nov 21 usability study done / Dec 1 feature freeze / Dec 5 manuscript
outline / Dec 7 final / Dec 10 iShowcase.

## Section 6 Ethics (Timur)
- New data: bill and EOB numbers, household income. Never stored or logged; letter details filled in the browser.
- Photos (F10) go to a third-party model API only with explicit consent, are not stored by ClearTab, and the
  screen asks users to cover names and member IDs. The model never produces a finding.
- Not legal advice: each finding says "ask about this", cites its rule, and links to official help (No Surprises
  Help Desk 1-800-985-3059).
- Harm if wrong: a false "error" could lead someone to withhold payment. The letter asks to put the account on
  hold during review rather than refusing to pay; amounts in question are capped at the bill balance.
- Assistance policies: a wrong threshold could mislead; two-reader check before display, source link on every
  card, "the hospital decides" note.

## Section 7 AI usage (Artyom)
Add: open-weights models on Groq (qwen/qwen3.8-27b for document reading; gpt-oss-120b, gpt-oss-20b and qwen as
benchmark subjects in R2). The v1 commitment stays: no model computes, adjusts or invents a price or a finding.

## Section 11.2 ground rules (Danil)
Item 16.5 ("participant notes are never entered into an AI tool") and the "notes only, no audio" rule: rewrite to
cover professional stakeholder interviews recorded with consent and transcribed with a tool, with names removed
and transcripts kept out of the repository.
