# ClearTab plan to iShowcase (2026-11-04 to 2026-12-10)

Builds on docs/PLAN_V2.md. Evidence: research/landscape/US_ARIZONA.md and research/landscape/WORLD.md.

## 1. What we are trying to achieve
One sentence: **a person with a medical bill learns in a few minutes whether to pay it, wait, or question it,
and leaves with the exact next step (letter, call script, appeal, or financial assistance application).**

Why this is worth doing (sourced in research/landscape/US_ARIZONA.md):
- 45% of insured working-age adults got a bill for care they thought was covered; 54% of those who did not
  challenge it were not sure they were allowed to; 38% of those who disputed got it reduced or removed
  (Commonwealth Fund 2024).
- 74% of people who called a billing office about an error got it fixed; 86% of those who never called thought
  it would not help (JAMA Health Forum 2024).
- 51% of potentially eligible patients never applied for charity care (Dollar For). Arizona has no state charity
  care law, only IRS 501(r).
- Marketplace insurers denied about 20% of in-network claims in 2023 and fewer than 1% of denials were appealed
  (KFF); Arizona's rate was 21% (Arizona Attorney General).
- Abroad, a bill is checked or priced from one public schedule before the patient sees it (Japan, Germany,
  France, Canada, Maryland). In Arizona the patient is the last auditor. ClearTab gives the patient the public
  schedules and the standard checks.

The main barrier is not math, it is **not knowing you may question a bill and what to say**. ClearTab's job is
to give permission and a script, backed by rules and sources.

Gap: no free, open-source tool combines rule-based bill and EOB checks, Arizona law, and Arizona charity care
(paid services take 10-20% of savings; free AI tools write appeal letters but do not audit bills).

## 2. Who
1. UA students, including international students (UA student plan 2026-27: UnitedHealthcare Student
   Resources, $250 deductible, $2,500 out-of-pocket maximum, $200 ER copay, referral rules).
2. Ordinary Arizonans with low or middle income, insured or not (charity care, collections, Spanish).

## 3. Success at iShowcase (targets, to confirm with Dr. Li)
- Public web app with a stable URL and a QR code; works on any phone; no account.
- At least 100 survey responses; at least 10 usability sessions (R3); at least 5 real bills walked through
  with consent; at least 1 documented real outcome (bill corrected, reduced, or assistance approved) with the
  person's written permission to share. If no outcome is final by Dec 10, we report honestly what is pending.
- Every finding on screen traceable to a rule and an official source; a language model never produces a number.
- Native app stores: decision on Nov 20 (web first).

## 4. Product work, in priority order
| # | Item | Why | Owner | Due |
|---|---|---|---|---|
| P0 | Review and merge PRs #15-#23 (non-author approval), deploy public beta (API + web + Postgres on free tiers, HTTPS, custom domain optional) | Nothing else works without a URL | Danil, all review | Nov 12 |
| P1 | "You can question this" first: itemized-bill request letter and phone script as the first step on every non-"pay" result | Best-documented barrier | Nikita, Timur | Nov 14 |
| P2 | UA student plan mode: 2026-27 plan rules (copays, deductible, out-of-pocket max reached, referral reduction) checked against the EOB; Campus Health reviews the rules | Our first users; concrete wins | Artyom, Timur | Nov 18 |
| P3 | Medicare yardstick per line: Arizona Medicare rate (PFS 2026, locality 03102-00; OPPS/ASC where facility) shown as "N x Medicare", with the CMS file named | Fair-price anchor that works for any bill; public data | Artyom, Danil | Nov 21 |
| P4 | Arizona appeal kit for denials: internal appeal letter, DIFI external review steps (4-month deadline, free), AG complaint route | 20% denied, under 1% appealed | Timur | Nov 21 |
| P5 | Arizona debt protections: Prop 209 3% interest cap check, 10% garnishment, credit bureau rules (under $500 not reported, paid removed, 1-year wait), state Undue Medical Debt relief note, collector validation letter (exists) | People in collections | Timur, Artyom | Nov 25 |
| P6 | Charity care statewide: collect the 16 missing nonprofit policies; Dollar For handoff for eligible users (partner page) | Largest dollar wins | Artyom | Nov 25 |
| P7 | International student mode: glossary (EOB, allowed, coinsurance), SHIP example visit, interface in more languages (human-checked strings) | Our own experience; Liu et al. 2023: about 22% could compute their costs | Nikita | Nov 28 |
| P8 | Outcome tracker in My visits: user marks "called / letter sent / reduced / approved" and the amount saved, stored on the device only; optional anonymous count sent with consent | Lets us report outcomes without storing bills | Danil | Nov 28 |
| P9 | Demo polish: example bills with planted errors, offline backup video, poster QR | Showcase | Nikita | Dec 5 |
| Later | Capacitor wrap for Google Play / App Store (Apple account $99/yr) | Decision Nov 20 | Danil | after Dec 1 if yes |

Feature freeze Dec 1: after that only fixes, data refresh and demo material.

## 5. Real cases and outreach (the "real person" part)
- Survey (anonymous) + separate sign-up form: research/r3/survey/create_forms.gs. Do not distribute until Dr. Li
  answers the IRB question.
- Channels: Michael's groups, Campus Health insurance office (Ivan Acosta), UA Basic Needs Center, international
  student office, team's own networks. The classmate's brother whose EOB we tested: ask if he wants us to finish
  his case (itemized bill, check, call).
- Case protocol (to write before the first case, short): written consent, we look at papers together, no copies,
  no data in git, the person makes the calls or sends the letter themselves (we are not lawyers or advocates),
  we record only outcome type and amount with permission.
- Partners to email: Campus Health, Dollar For (partner/referral), Step Up to Justice (legal referral for debt and
  collections), AZ DIFI consumer services (review our appeal guide), later local press after the beta is live.

## 6. Research
- R1 statewide assistance policies: finish the 16 policies; generosity comparison; second reader.
- R2 can AI check a bill: finish condition C (photo + rules), confirmatory run; this is the paper with Dr. Li.
- R3 usability: find amount owed and spot a planted error, with vs without ClearTab; plus "would you call" intent.
- S1 survey: bill experience of UA students and Arizonans (fills a literature gap; IRB first).
- Outcomes log: count of cases and outcomes, with consent; numbers only.

## 7. iShowcase demo (3 minutes)
1. Hook: one real story (with consent) or, if none, a realistic UA student ER visit with planted errors.
2. A judge scans the bill and EOB with their own phone via the poster QR.
3. Findings appear with the rule and the official source; the Medicare yardstick shows "4 x Medicare" style anchor.
4. One tap: letter or call script; charity care check says "you may qualify for free care at this hospital".
5. Numbers slide: survey results, usability results, outcomes so far, R2 (rules vs language models).
6. Close: "in Japan or Germany this check happens before the bill reaches you; here it is free in your pocket".
Backup: recorded video and offline build in case of network failure.

## 8. Week by week
| Week | Focus |
|---|---|
| Nov 4-9 | Mid-semester demo; forms built; emails to Michael, Dr. Li, Campus Health, Dollar For, Step Up; PR review starts |
| Nov 10-16 | Merge and deploy beta; P1; survey live (if IRB ok); first 2 real cases; Campus Health review of P2 |
| Nov 17-23 | P2, P3, P4; usability round 1 (R3); App store decision Nov 20; R2 condition C finished |
| Nov 24-30 | P5-P8; usability round 2; accuracy check; 16 policies |
| Dec 1-7 | Feature freeze Dec 1; poster, demo video, final report, manuscript outline Dec 5; submission Dec 7 |
| Dec 8-10 | Rehearsal, iShowcase Dec 10 |

## 9. Risks
- IRB scope unclear: no survey or usability data used for publication before Dr. Li confirms.
- Personal health data: never stored; consent and case protocol first.
- CPT descriptors are AMA copyright: show code numbers and our own plain labels only; NCCI/MUE tables stay out
  of git; check whether the deployed server may use the NCCI tables under the click-through license.
- Groq free tier daily cap: limit reading per user; ask UA for API credits (via Michael).
- Not legal advice: every letter says the user sends it themselves; legal questions go to Step Up to Justice.
- Numbers still to verify before the poster: Arizona RAND price ratio, Dollar For 29% (original report), status
  of SB 1607 / HB 2581, Prop 209 court challenge.
