# ClearTab research: evidence and opportunities (US + Arizona)

Prepared 2026-11-04. Method: web search and page fetches. Every fact has a source URL. "Not found" means I searched and did not find a reliable source. Where a figure comes only from a secondary source (news, podcast transcript, competitor marketing), that is stated.

---

## 1. How often medical bills contain errors

### Best evidence (survey-based, nationally representative)

| Finding | Source and quality |
|---|---|
| 45% of insured working-age adults got a bill or copay in the past year for a service they thought should have been free or covered. Fewer than half challenged it; 54% of non-challengers were not sure they had the right to. 38% of those who disputed had the bill reduced or eliminated (61% for Medicare, 46% for Medicaid). 17% had a doctor-recommended service denied; 50% of those who challenged a denial got some or all of it approved. | Commonwealth Fund, "Unforeseen Health Care Bills and Coverage Denials by Health Insurers in the U.S.", Aug 2024, survey fielded Apr-Jul 2023. https://www.commonwealthfund.org/publications/issue-briefs/2024/aug/unforeseen-health-care-bills-coverage-denials-by-insurers and press release https://www.commonwealthfund.org/press-release/2024/new-research-insured-working-age-americans-face-widespread-medical-billing . Quality: good (probability sample). Caveat: measures *perceived* wrong bills, not audited errors. |
| About 1 in 5 adults recently got a bill they disagreed with or could not afford. 61.5% contacted the billing office; 86.1% of those who did not said it would not make a difference. 74% of those who called about an error said it was corrected; 76% who called about an unaffordable bill got some relief; 62% who negotiated got a lower price. Less likely to call: no college degree, lower financial literacy, uninsured. | Duffy, Trish et al., "Disparate Patient Advocacy When Facing Unaffordable and Problematic Medical Bills", JAMA Health Forum, 2024-08-30, DOI 10.1001/jamahealthforum.2024.2744. Summary: https://www.news-medical.net/news/20240830/Research-shows-many-miss-out-on-financial-relief-for-problematic-medical-bills.aspx . Quality: good (Understanding America Study, n=1,135, Aug-Oct 2023). Self-reported outcomes. |
| 58% of insured adults had at least one problem using insurance in the past year; 18% had a denied claim; 60% do not know they have a legal right to appeal; 16% had trouble paying medical bills. | KFF Survey of Consumer Experiences with Health Insurance, fielded Feb 21 - Mar 14 2023, n=3,605. https://www.kff.org/health-costs/press-release/kff-survey-shows-complexity-red-tape-denials-confusion-rivals-affordability-as-a-problem-for-insured-consumers-with-some-saying-it-caused-them-to-go-without-or-delay-care/ and denied-claims brief https://www.kff.org/affordable-care-act/issue-brief/consumer-survey-highlights-problems-with-denied-health-insurance-claims/ . Quality: good. |
| 32% of continuously privately insured working-age adults are paying off medical bills or debt over time; 15% owe more than $2,000; 36% could not pay an unexpected $1,000 bill in 30 days; 25% said their bills went to a credit bureau; hospital care was the most common source. | Commonwealth Fund, "How Medical Bills and Debt Impact Americans with Private Insurance", Sep 17 2026 (2025 Affordability Survey, n=4,121 privately insured). https://www.commonwealthfund.org/publications/surveys/2026/sep/how-medical-bills-debt-impact-americans-private-insurance (page returned 403 to my fetcher; numbers taken from coverage: https://www.marketplace.org/story/2026/09/18/1-in-3-adults-with-insurance-still-has-medical-debt-survey-finds , https://www.healthcarefinancenews.com/news/one-third-privately-insured-adults-carries-medical-debt ). Quality: good survey; verify numbers against the PDF https://www.commonwealthfund.org/sites/default/files/2026-09/PDF_Collins_how_medical_debt_impacts_americans_private_insurance.pdf |

### Weak or misleading figures (do not use as headline)

- **"80% of medical bills contain errors"**: traces to Medical Billing Advocates of America (MBAA), based on bills its own advocates reviewed (a self-selected sample of bills people already suspected). Not a random sample, no published method. https://www.beckershospitalreview.com/finance/medical-billing-errors-growing-says-medical-billing-advocates-of-america/ , https://consumerist.com/2009/05/14/80-of-medical-bills-have-errors/ . Many 2026 AI bill apps repeat it (e.g. https://www.producthunt.com/products/medical-bill-al-save-money/launches ).
- **"49% of Medicare claims have errors"** (NerdWallet, 2016): commercial analysis, method not peer reviewed. Cited at https://www.coronishealth.com/blog/new-study-suggests-mistakes-in-nearly-half-of-all-medicare-bills .
- **"AMA: 7.1% of claims had errors" (2013)**: secondhand only, original not found.
- "65% of adults have encountered billing errors", "$935 million lost weekly": aggregator sites with no traceable primary source (e.g. https://jobera.com/resources/?p=24553 ). Not usable.
- **Not found**: any recent (2023-2026) peer-reviewed *audit* of a random sample of consumer hospital bills measuring an error rate. This is a real evidence gap; ClearTab's R2 synthetic benchmark should say so honestly rather than claim a prevalence.

### Error types with evidence

- Billed for covered or free services (Commonwealth 45%, above).
- Claim denials, mostly administrative or "other" reasons (KFF marketplace data, section 3).
- Duplicates, unbundling, upcoding: commonly listed by advocates and apps; no recent primary prevalence data found.

**Implication for ClearTab:** the strongest honest message is not "most bills are wrong" but "many people get a bill they think is wrong, most never question it, and when they do, a large share win" (Commonwealth 38%, JAMA HF 74% of error calls corrected).

---

## 2. Charity care uptake, Arizona law, credit reporting

### Uptake gap

- Dollar For research (early 2024 reports, survey of 1,100+ people plus IRS filings): only **29%** of patients with hospital bills they cannot afford manage to learn about, apply for, and receive charity care; about two thirds did not know it exists; estimated gap about **$14 billion** (they call it conservative). Source is podcast coverage, original report not found: https://kffhealthnews.org/podcast/new-lessons-fight-charity-care-financial-assistance/ , https://armandalegshow.com/episode/new-lessons-charity-care
- A 2023 Dollar For survey: **51%** of potentially eligible respondents did not apply; more than half of those did not know programs existed. Cited by Cronkite News, Mar 2026: https://cronkitenews.azpbs.org/2026/03/18/hospital-financial-assistance-policies-help-arizona-patients/
- Eligibility rules vary wildly: among 2,989 US nonprofit hospitals, free-care income cutoffs ranged from 41% to 600% of the federal poverty guideline; many use asset tests, some residency requirements. Messac et al., Health Affairs 43(11):1569-1577, 2024. https://hbhi.jhu.edu/node/678 (median 200%/400% FPL figures seen only on a secondary site, not verified).
- Reporting of bad debt from charity-eligible patients is sporadic: in one sample of 111 nonprofit hospitals only 32 reported any; Texas analysis estimates 5.4%-14.7% of bad debt came from patients who should have qualified. https://www.bakerinstitute.org/research/nonprofit-hospitals-and-medical-debt-texas (secondary summary; check original).
- Enforcement example: Washington AG ordered PeaceHealth to refund more than 15,000 patients up to $13.4 million for billing without screening for charity care (2023). https://www.cbsnews.com/boston/tag/internal-revenue-service (secondary; Washington AG release not fetched).
- Lown Institute: only 20% of 2,425 nonprofit hospitals had a "fair share" surplus (2024-25 analysis). https://www.healthcaredive.com/news/nonprofit-hospitals-charity-care-deficit-lown-institute/711318/ . Arizona hospital-level fair share numbers: not found in this pass (check lownhospitalsindex.org).
- KFF, Health Affairs and JAMA 2023-2025 study counting eligible patients who were billed instead: **not found** as a national number. JAMA Internal Medicine viewpoint (Kona 2024) argues federal rules set no minimum eligibility thresholds (secondary mention).

### Arizona numbers

- Arizona has **no state charity care law**; nonprofit hospitals follow federal IRS 501(r). Arizona hospitals forgave over **$324 million** in charity care in 2024 (AHCCCS report); uncompensated care rose $213.2 million 2015-2024. Cronkite News (Sophia Braccio), Mar 18 2026: https://cronkitenews.azpbs.org/2026/03/18/hospital-financial-assistance-policies-help-arizona-patients/ (also on AZPM and KJZZ/HealthLeaders).
- Medical debt prevalence: about 8.2% of Arizonans (about 460,000) have medical debt (KFF-Peterson, via secondary source); Urban Institute Debt in America 2021: 16% of Arizonans with a credit file had medical debt in collections, median about $1,000. https://azpha.org/wp-content/uploads/2022/06/Predatory-Debt-Collection-Protection-Initiative_-Policy-Paper-1.pdf . Current 2025 Arizona Urban number: not found (Urban appendix: https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2025/11/19/Debt%20in%20America%20Technical%20Appendix%202025.pdf ).
- State medical debt relief (Gov. Hobbs + Undue Medical Debt, started 2024, $30M ARPA funds): more than **$1 billion** erased for nearly **671,000** Arizonans as of Aug 2026; no application, debt is bought automatically; targets income at or below 400% FPL or medical debt at least 5% of income. https://www.azmed.org/arizona-erases-1-billion-in-medical-debt-for-nearly-671-000-residents , https://ktar.com/arizona-health-news/1-billion-medical-debt-erased-arizonans , FAQ https://azgovernor.gov/node/6259

### Arizona law

- **Prop 209 (Predatory Debt Collection Protection Act, Nov 2022, passed 72-28)**: caps interest on medical debt (and medical financing and judgments on medical debt) at the lesser of 3% per year or the weekly average one-year Treasury yield; limits garnishment of unsecured debt to 10% of disposable earnings (from 25%); raises exemptions for home equity, vehicle, bank account and household goods, with inflation adjustment from 2024; does not apply to contracts made before its effective date. https://ballotpedia.org/Arizona_Proposition_209,_Healthcare_Debt_Interest_Rate_Limit_and_Debt_Collection_Exemptions_Initiative_(2022) , https://www.azcourts.gov/selfservicecenter/Garnishment/Proposition-209 , https://azpha.org/2025/12/29/how-arizonas-medical-debt-proposition-209-is-helping-families-health/ . Outcome of the creditors' bar legal challenge: not confirmed in this pass.
- **2026 bills**: SB 1607 (Kuby, Epstein, Miranda, Ortiz, Sundareshan; Rep. Garcia) would create a health care claims consumer assistance program in DIFI, help with appeals, civil penalties of at least $25,000 per violation for repeated wrongful denials, double damages, annual public denial report by insurer from May 1 2027, $250,000 appropriation. Text: https://www.azleg.gov/legtext/57leg/2R/bills/SB1607P.htm . Companion HB 2581 https://www.azleg.gov/legtext/57leg/2R/bills/HB2581P.htm and SB 1533. Final status (signed or not): **not confirmed** (trackers conflict; check azleg.gov).
- Older: HB 2679 (2023-24, medical debt grants) https://www.azleg.gov/legtext/56leg/1R/bills/HB2679P.htm , outcome not confirmed; SB 1796 (2021) died.
- Arizona Attorney General (Sep 2025): Arizona's 2023 in-network denial rate was **21%** vs 19% national; held listening sessions on denials; consumer complaints at azag.gov/complaints/consumer, (602) 542-5025. https://www.azag.gov/index%2Ephp/press-release/attorney-general-mayes-announces-town-halls-health-insurance-denials

### Credit reporting

- **CFPB medical debt rule** (finalized Jan 2025, would have removed about $49B from credit reports of 15 million people) was **vacated** on July 11 2025 by the US District Court for the Eastern District of Texas (Cornerstone Credit Union League v. CFPB), after CFPB itself agreed. Court also said FCRA preempts state laws banning reporting of coded medical debt. https://www.consumerfinance.gov/archive/newsroom/cfpb-finalizes-rule-to-remove-medical-bills-from-credit-reports/ , https://news.bgov.com/banking-law/cfpb-medical-debt-reporting-ban-vacated-by-texas-federal-judge , https://www.accountsrecovery.net/2025/07/13/judge-vacates-cfpb-medical-debt-credit-reporting-rule/
- **Bureaus' voluntary policies (still in effect as far as found)**: since July 1 2022, paid medical collections removed and unpaid ones wait 1 year before appearing; since April 2023, medical collections under $500 are not reported (removed about 70% of medical collection tradelines). https://www.techtarget.com/revcyclemanagement/news/366600479/Major-Credit-Bureaus-Remove-Medical-Debt-Collections-Under-500 , https://www.autoremarketing.com/subprime/equifax-experian-transunion-remove-medical-collections-debt-under-500-on-credit-reports . Any 2025-2026 reversal by the bureaus: not found.

---

## 3. Claim denials and appeals

- HealthCare.gov marketplace insurers, 2023: about **20%** of in-network claims denied (86M of 436M), 36% of out-of-network. **Under 1%** of in-network denials appealed (376,508 appeals); insurers upheld **56%** of internal appeals (so roughly 44% overturned or otherwise not upheld; KFF does not state an overturn rate directly). External appeals: at least 5,000. Reasons: other 34%, administrative 21%, excluded service 14%, no prior auth/referral 9%, medical necessity about 6%. Arizona insurer examples: BCBS of Arizona reported 97% of denial reasons as no prior auth/referral; Cigna HealthCare of Arizona 32% medical necessity. KFF, Jan 27 2025, updated Mar 24 2026. https://www.kff.org/private-insurance/claims-denials-and-appeals-in-aca-marketplace-plans-in-2023/
- Survey side: 18% of insured adults had a denied claim (KFF 2023); 17% denied a doctor-recommended service, 43% challenged, 50% of challengers won (Commonwealth 2024). Links in section 1.

### Arizona external review (DIFI)

- DIFI health care appeals page: https://difi.az.gov/health-care-appeals . Levels: Initial Appeal, optional Voluntary Internal Appeal, then External Independent Review.
- Consumer guide (2025): https://difi.az.gov/sites/default/files/Final%202025%20Consumer%20Brochure%20Rev.%2007.02.25.pdf ; insurer appeals packet (Jul 2025): https://difi.az.gov/sites/default/files/Final%20Health%20Care%20Appeal%20Packet_07.02.25.pdf
- Deadline: request external review within **4 months** after the insurer denies the final internal appeal. Medical necessity disputes go to a state-contracted Independent Review Organization (decision within 21 days per insurer packets); pure coverage questions are decided by DIFI. **No fee** to the patient for any level. Expedited track exists with provider certification.
- Contacts listed by DIFI: Consumer Services (602) 364-3100; health care appeals hca@difi.az.gov, (602) 364-2499, 100 N 15th Ave Suite 261, Phoenix AZ 85007 (from the packet).
- Caveat: applies to state-regulated plans; self-funded employer (ERISA) plans use the federal external review process. Students on the UA SHIP (UnitedHealthcare Student Resources, insured plan) should fall under DIFI, but confirm with DIFI.

---

## 4. Existing tools and competitors

| Tool | What it does | Price | Nonprofit | Gap ClearTab can fill |
|---|---|---|---|---|
| Dollar For (dollarfor.org) | Fills and submits hospital financial assistance applications, follows up; says 20,000+ applications | Free, donor funded | Yes (EIN 46-0889864) https://dollarfor.org | Does not check bill math, EOB match or denials; ClearTab can do the check first and hand off charity-eligible cases (partner page https://dollarfor.org/partner/ ) |
| Goodbill | Gets itemized hospital bill, finds coding/pricing errors, negotiates | 20% of savings, cap $1,000; hospital bills only, not in collections https://www.goodbill.com/faq | No | Paid, hospital-only, opaque; ClearTab is free, shows every rule and source |
| Resolve | Advocates negotiate bills and file assistance applications | 10% success fee, $499 deposit for bills over $15k (FAQ); partner pages show 8-25% https://www.resolvemedicalbills.com/faq | No | Targets large bills; ClearTab serves small bills nobody negotiates |
| Counterforce Health | AI drafts insurance appeal letters; voice AI "Maxwell" calls insurer | Free to patients https://www.axios.com/local/raleigh/2025/08/20/using-ai-to-fight-back-against-insurance-denials-counteforce | Yes (claims 20,000 helped, 70% reversal, self-reported) | Appeals only; no bill audit, no AZ-specific DIFI steps |
| Fight Health Insurance | Open-source AI appeal letter generator | Free; optional $5 fax https://bgr.com/tech/this-free-site-uses-ai-to-help-you-fight-health-insurance-claim-denials/ | Company (open source) | LLM-written letters; ClearTab's deterministic findings feed a letter |
| Claimable | AI appeals, mailed/faxed for you | $39.95 per appeal at launch (2024), about $50 in 2026 https://www.globenewswire.com/news-release/2024/10/02/2956879/0/en/Claimable-Launches-First-Ever-AI-Powered-Appeals-Platform-to-Fight-Unjust-Healthcare-Denials.html | No | Paid, appeals only |
| Sheer Health | App that tracks claims, handles disputes and appeals | Listed free on App Store; one user reported $40/month; unverified https://apps.apple.com/us/app/-/id6447633462 | No | Requires handing over insurer account; ClearTab works on paper you already have, stores nothing |
| CareRoute (Healtheja, Inc.) | Charity care rankings by city incl. Phoenix (Banner, HonorHealth, Valleywise), bill letters, paid "Bill Defense" | Rankings free; bill service fee capped $1,000 https://www.careroute.ai/charity-care | No | Direct competitor for F9; Tucson not mentioned; ClearTab can cover Tucson and link the exact policy PDF and date |
| FAIR Health Consumer | Cost lookup by procedure and ZIP, in/out of network estimates | Free https://www.fairhealth.org/article/fair-health-s-consumer-site-continues-to-expand-its-offerings | Yes (501(c)(3)) | Estimates, not checking your bill |
| Turquoise Health | Price transparency data company; had a free consumer search (2022) https://medcitynews.com/2022/05/turquoise-health-raises-20m-to-boost-price-transparency/ | Consumer search free (current status not verified) | No | Prices only |
| Unbill | **Not found** under this name | - | - | - |
| 2025-2026 AI bill apps: Billopsy, BillMD, Billscope, MyBill Decoder ($9.99/mo), Medical Bill Negotiator: IQ ($2.99/week to $59.99 lifetime), MedBillAI, BillShield, BillProof, FairMedBill | Photo of bill, LLM flags "possible" errors, writes dispute letter | Mostly freemium | No | Most repeat the "80%" claim; findings come from an LLM, not rules; no EOB reconciliation, no state law, no charity care. Listings: https://www.producthunt.com/products/billopsy/launches , https://apps.apple.com/us/app/-/id6761640558 , https://apps.apple.com/us/app/-/id6757212060 |

**ClearTab's defensible niche** (no tool found doing all of it): free + open source + deterministic rules with cited sources + bill-to-EOB reconciliation + Arizona-specific law (Prop 209, DIFI, ambulance rates) + local charity care policies + no data stored.

---

## 5. Partners and contacts (public listings only)

| Who | Why | Public contact |
|---|---|---|
| UA Campus Health Insurance Office (Ivan Acosta, Program Coordinator Senior) | SHIP questions, referral rules, student pilot | chs-insurance@distribution.arizona.edu (listed on UA exemption pages), Campus Health 520-621-9202, https://health.arizona.edu/people/insurance |
| UA Arizona Center for Rural Health (Director Daniel Derksen) | Runs Health Insurance 101 materials, AHCCCS/HR1 work, navigator ties | https://crh.arizona.edu/ |
| MEZCOPH faculty | Health policy faculty roster not found in this pass; Maia Ingram (Health Promotion Sciences, community health workers) is a possible lead | https://publichealth.arizona.edu/directory/maia-ingram |
| UA Basic Needs Center | Already lists Step Up to Justice for students | https://basicneeds.arizona.edu/step-justice |
| Step Up to Justice (Tucson) | Free civil legal help for low-income Pima County residents incl. consumer/debt | https://www.stepuptojustice.org/ , 520-276-3815 |
| Community Legal Services (Phoenix area), Southern Arizona Legal Aid, Arizona Center for Disability Law | Legal aid referral targets | Pages not fetched in this pass; statewide portal referenced by courts: https://azcourts.gov/selfservicecenter/Consumer-Debt |
| Arizona Alliance for Community Health Centers | Marketplace navigator grantee, primary care association | Current navigator contact not found; directory https://issuu.com/aachc/docs/2024_aachc_membership_directory_7.11 |
| Dollar For | Referral of charity-eligible users | https://dollarfor.org/partner/ , https://dollarfor.org/contact/ |
| AZ DIFI Consumer Services | Validate the appeal guide; SB 1607 program if funded | (602) 364-3100, hca@difi.az.gov |
| AZ Attorney General consumer unit | Denial complaints | https://www.azag.gov/complaints/consumer |
| Journalists | Sophia Braccio (Cronkite News, wrote the Mar 2026 AZ charity care story); Stephanie Innes (Arizona Republic health reporter, per speaker profile https://behavioralhealthtech.com/2024-speakers/stephanie-innes ); James Hodge (ASU law professor, quoted on charity care) as an expert source | Arizona Luminaria and KJZZ health reporter names: not found |

---

## 6. Students

- **UA SHIP 2026-27**: UnitedHealthcare Student Resources; plan year 8/16/26-8/15/27; annual premium **$2,956** (Fall $1,118, Spring+Summer $1,838). Platinum, actuarial value 91.83%. In-network deductible **$250**, out of network $1,000; out-of-pocket max **$2,500** in network, $5,000 out; coinsurance 80% in network, 50% out; physician visit $25, urgent care $25, emergency $200 (waived if admitted); Rx deductible $125, tiers $15/$40/$80. At Campus Health many services $0 or $15-25 copays; labs at Campus Health or sent to LabCorp/Sonora Quest at 100%. **Student Health Center referral requirement: benefits are reduced for outpatient care elsewhere without a Campus Health referral.** Flyer: https://www.uhcsr.com/uhcsrbrochures/public/benefitsummaryflyers/2026-738-1%20Summary%20Flyer.pdf ; plan page https://health.arizona.edu/student-health-insurance-plan-2026-2027
- **International students**: all on non-immigrant visas with at least one unit are automatically enrolled and must carry SHIP unless they get an exemption under Campus Health guidelines each semester; individual policies are not accepted; deadlines Fall 2026 Sep 8, Spring 2027 Jan 27; missing it means paying the premium. https://health.arizona.edu/international-students-exemptions
- Student surveys: no 2024-2026 survey of college students and medical bills found. Older: about half of 455 students at a public university were confused about choosing/using coverage, about a quarter delayed or skipped care (UVA, ACHA 2018-19) https://www.studenthealth.virginia.edu/sites/g/files/jsddwu891/files/ACHAPosterFinal.pdf . A fall 2025 Belmont student survey exists, numbers not available https://repository.belmont.edu/spark_presentations/1169 . **This is a gap ClearTab's R3 could fill with a small UA survey (IRB needed).**

---

## 7. Demo ideas for the Dec 10 showcase

What the evidence supports saying out loud: people get bills they think are wrong (Commonwealth 45%), most never question them (54% unsure they may; 86% think calling will not help), and those who do question often win (38% reduced; 74% of error calls corrected).

1. **"Spot the error" live challenge**: hand judges a realistic synthetic UA student bill + UHCSR-style EOB with one planted error (e.g. billed amount above "patient responsibility" on EOB, or a copay charged above the $25 SHIP copay). Give them 60 seconds, then scan it with ClearTab and show the rule, the number and the source line. Mirrors R3.
2. **Student scenario using real SHIP rules**: a student saw an outside specialist without a Campus Health referral, got reduced benefits; ClearTab explains why, what to ask Campus Health (retro referral), and the DIFI 4-month path. Every number from the public flyer.
3. **Arizona Tucson charity care in 30 seconds**: enter household size and income, show which Tucson/Phoenix hospitals' 501(r) policies cover you, link to the exact policy PDF and retrieval date. Contrast with "51% of eligible people never apply".
4. **Prop 209 check**: statement showing interest above 3% on a medical bill gets flagged with the statute. Simple, local, deterministic.
5. **"No AI made this number" panel**: show the rule trace and that the vision model only reads, the user confirms, and the rules decide. Judges in 2026 have seen many LLM bill apps; this is the differentiator.
6. **Honest scoreboard**: R2 results (rules vs LLM vs hybrid on the synthetic benchmark), number of AZ hospital policies collected, and, only if real and consented, one real outcome (dollars corrected). Do not quote "80% of bills".
7. **Cost comparison slide**: same case through ClearTab (free) vs Goodbill (20%, cap $1,000), Resolve (10% + deposit), Claimable ($40-50 per appeal).

---

## Top 5 actionable opportunities

1. **UA SHIP mode**: preload 2026-27 SHIP cost sharing (deductible $250, OOP max $2,500, copays, referral rule) as rules: flag copay overcharges, OOP max exceeded, missing-referral reductions. Email Campus Health Insurance Office for a review and a pilot.
2. **Arizona appeal kit (F8)**: DIFI steps, 4-month deadline, no fee, links to the official request form, AG complaint route; cite Arizona 21% denial rate. Watch SB 1607 / HB 2581 status for a DIFI consumer assistance program to refer to.
3. **Charity care finder with Tucson coverage (F9)**: competitors (CareRoute) cover Phoenix, not Tucson; add policy PDF link + retrieval date + FPL table, and a "send to Dollar For" handoff.
4. **Arizona debt protection rules**: Prop 209 interest cap check, garnishment 10% explainer, state Undue Medical Debt program (no application, 400% FPL or 5% of income), credit bureau rules (under $500 not reported, paid removed, 1-year wait) with the note that the CFPB rule was vacated in July 2025.
5. **"You are allowed to question this" nudge + measurement**: the biggest documented barrier is people not knowing they can dispute; put the phone script first and measure it in R3 (a UA student survey would also fill a real literature gap).
