# ClearTab v2 plan (2026-11-02)

## Why the direction changed
- H1 met (17 of 19 hospitals usable). H2 not met: median highest-to-lowest ratio 1.92, goal 2 (Phoenix 2.81,
  Tucson 1.39). Under the proposal's own decision rule, comparison is not the value proposition, and the project
  reframes around interpretation of published prices.
- Interview with the UA Campus Health insurance office (2026-10-26): the main problem is after care. People cannot
  read the explanation of benefits (EOB), cannot tell whether a bill is right, and do not know whom to call. The
  student plan covers imaging and labs at 100%, so comparing prices before care has little money at stake for
  students.
- KFF Health Care Debt Survey (Feb-Mar 2022, 2,375 adults): 41% of US adults have debt from medical or dental
  bills; 44% of adults with such debt did not pay a bill in full because they were not sure it was accurate.
- Our data: only 2 of 19 hospitals publish physician fees for the launch procedures, so a patient receives bills
  the hospital files do not show.
- The instructor agreed the direction may change within the same topic (2026-10-27); the team decides.

## Product: from bill to resolution
Tagline: check a medical bill against what the hospital published and what your insurer said, then get help
paying it.

| ID | Feature | Status for the Nov 9 prototype |
|---|---|---|
| F7 | **Bill check.** The user enters (or uploads) the EOB lines and the bill. A deterministic rule engine checks EOB arithmetic, bill vs EOB, duplicates, units above the CMS medically unlikely edit, code pairs that CMS says should not be billed together, the allowed amount against the hospital's published rate for that insurer, a self-pay charge against the published cash price, and No Surprises Act protections. Each finding has a plain explanation, the evidence and its source, and what to do. | Core |
| F8 | **Dispute kit.** A letter and a phone script built from the findings, using the vocabulary billing offices ask for (facility or provider charge, itemized bill with codes, claim number). Template based, no free text generation. | Core |
| F9 | **Financial assistance finder.** Each nonprofit hospital must publish a financial assistance policy (IRS 501(r)). ClearTab extracts the income thresholds, discounts and how to apply for Arizona hospitals; the user enters household size and income in the browser and sees what they may qualify for. | Core (19 hospitals), statewide later |
| F10 | **Read my documents (optional).** A photo or PDF of an EOB or bill is turned into editable lines by an open-weights vision model, only with consent; the user checks every number before the rule engine runs; nothing is stored. | Prototype |
| F11 | **What bills to expect.** For common procedures, the separate bills a patient may receive (facility, physician, anesthesia, pathology), with published prices where they exist and "not published" where they do not. | After Nov 9 |
| F1-F6 | Price search, comparison, completeness and provenance from v1 stay as the reference layer behind F7 and F11. | Kept |

Design rules carried over from v1: every number traceable to a source; no accounts; no personal data stored or
logged; bill and income data stay in the browser or in the request only; a language model never produces a
price or a finding, it only reads a document into fields the user confirms.

## Research
- **R1 Statewide and multi-state.** Extend the hospital registry to all Arizona hospitals; collect financial
  assistance policies (eligibility thresholds, discounts) and compare generosity across hospitals and systems,
  and for multi-state systems across states. Addresses the advisor's sample-size concern.
- **R2 Can AI check a bill?** A benchmark of synthetic EOB and bill pairs with planted errors (known answers, no
  personal data). Compare the rule engine, open-weights language models alone, and the hybrid. Fits the
  advisor's lab.
- **R3 Usability (replaces H3).** Between subjects, with and without ClearTab: can a participant find the amount
  they owe and spot a planted error? Scored against a right answer. IRB position to be confirmed in writing.
- H1 and H2 results from v1 are reported as they are, including the cash vs per-insurer analysis
  (research/discovery/cash_vs_insurance.md).

## Data sources
| Source | Use | Access |
|---|---|---|
| Hospital machine-readable files (v1 pipeline) | published rates, cash prices, gross charges | already loaded (19 hospitals) |
| CMS NCCI medically unlikely edits (MUE), quarterly | units check | direct download from cms.gov |
| CMS NCCI procedure-to-procedure (PTP) edits, quarterly | code pair check | AMA CPT license click-through: downloaded by a team member (MANUAL_DOWNLOADS.md) |
| HHS poverty guidelines 2026 | financial assistance eligibility | aspe.hhs.gov |
| Hospital financial assistance policies and plain language summaries | F9, R1 | hospital websites, polite fetch |
| CFPB consumer complaint database | evidence of pain (medical debt complaints) | public API |
| KFF surveys | national context | cited, not redistributed |

CPT descriptors are AMA copyrighted: NCCI and MUE tables stay in data/raw (gitignored) and are rebuilt locally;
the repository holds the code that reads them, not the tables.

## Schedule
| Date | Milestone |
|---|---|
| Nov 2 | Plan, data sourcing, rule engine skeleton |
| Nov 3 | Rule engine with tests, POST /bill/check |
| Nov 4 | Financial assistance data for the 19 sampled hospitals, GET /assistance |
| Nov 5 | Web: bill check flow and results |
| Nov 6 | Web: dispute kit, assistance finder, price lookup; synthetic demo cases |
| Nov 7 | Document reading (F10); test deployment |
| Nov 8 | Demo script and slides |
| Nov 9 | Mid-semester evaluation: working prototype |
| Nov 10-22 | R2 benchmark, R1 statewide, R3 usability study, proposal revision signed |
| Dec 1 | Feature freeze |
| Dec 5 / 7 / 10 | Manuscript outline / final submission / iShowcase |

## Team (owners)
- Timur: product and research lead, rule definitions, R2, proposal revision, interviews.
- Nikita: web flows (bill check, results, dispute kit, assistance finder), R3 usability study.
- Danil: API, database, deployment, document reading endpoint.
- Artyom: data (MUE, PTP, poverty guidelines, financial assistance policies), R1 statewide registry, QA.
