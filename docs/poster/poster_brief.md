# ClearTab poster brief (iShowcase, Dec 9, 2026)

Poster: 24 x 36 in, portrait, white background, must explain itself without a walkthrough (UA Capstone Poster
Design Guide, software style: problem and solution, UI screenshots, tech stack, features).

Checked against the code on branch `feature/denials` (commit 0fe5513) on 2026-11-17. Where an older document
disagrees with the code or data, the code wins and the conflict is noted. Every number below says where it comes from
and whether it was re-checked for this brief.

---

## 1. One-liner and pitch

**ClearTab is a free web app that helps people in Arizona check a medical bill and find out what they really owe.**

Medical bills and insurance statements are hard to read, and they are sometimes wrong. Many people pay anyway, or
give up, because they cannot tell. With ClearTab you take a photo of your bill or insurance statement, and in about a
minute you see what you owe, what to question and what help you can get, with a letter and a phone script ready to
use. Every finding comes from official rules and the hospital's own published prices, not from AI guesses, and your
documents are read on our own server and not kept.

---

## 2. Features

Status words: **working** = in the app and tested; **beta** = works, built recently or tested on few real
documents; **planned** = not built.

All of the work below is on branch `feature/denials` (PR #27, stacked on PRs #24 to #26). None of it is merged into
`main` yet, and none of it is online yet (see section 8).

| Feature | Status | What it does for the user | Where it lives |
|---|---|---|---|
| Home with the doors | working | One question, "What do you need?", with six choices. | `#/`, `web/src/pages/Home.tsx` |
| 1. "I think it's wrong" (bill check) | working | Compares the bill with the insurance statement (EOB) and the hospital's published prices, names each problem, says what to do, and gives a letter and a phone script. | `#/bill`, `BillCheck.tsx`, `Results.tsx`, `DetailedCheck.tsx`; API `POST /bill/check`; rules `billcheck/rules.py`, kit `billcheck/kit.py` |
| 2. "I can't afford it" (financial assistance) | working | Tells you, from the hospital's own policy, whether your income may qualify for free or discounted care, and gives the form, the documents to gather, where to send it and a cover letter. 8 Arizona health systems. | `#/help`, `Assistance.tsx`; API `POST /assistance`; `billcheck/assistance.py`, `data/processed/assistance_policies.json` |
| 3. "My insurer said no" (denial) | beta (built Nov 16) | Explains the denial reason in plain words, says whether a phone call usually fixes it, gives the appeal deadlines for your plan type with dates, a call script and an appeal letter. Shows the Arizona denial numbers from R4. | `#/denied`, `Denied.tsx`; API `POST /denial`, `GET /denial/reasons`; `billcheck/denial.py` |
| 4. "A collector is after me" (debt collector) | beta (built Nov 16) | Checks a collection letter against the federal dispute window, Arizona's 3% interest cap on medical debt, credit report rules and the hospital assistance window; points court papers to free legal aid; gives a dispute letter. | `#/collections`, `Collections.tsx`; API `POST /collections`; `billcheck/collection_letter.py` |
| 5. "A pile of bills from one visit" (My visits) | working | Keeps every bill, EOB and receipt from one visit in one place and says per provider: pay, wait or question. Shows deductible and out-of-pocket progress, reminders (.ics), sharing, a collector letter. | `#/visits`, `Visits.tsx`; stored only in the browser (localStorage) |
| Photo and PDF reading (OCR) | beta | Reads the numbers from a phone photo or a PDF on our own server (PDF text layer or text recognition), then fixed rules place each amount. You confirm every line before the check. | API `POST /bill/read`; `billcheck/local_reader.py` (production mode `READ_MODE=local`) |
| Example visit | working | "Try it with an example": a made-up ER visit (EOB PDF + bill photo) that the app reads and checks; finds a $1,818.00 overcharge. | `billcheck/examples/` (synthetic, marked SAMPLE); API `POST /bill/read/example/{name}` |
| Spanish | working (not reviewed by a native speaker) | Whole interface and every finding in Spanish (486 interface strings); letters stay in English because they go to US offices. | `web/src/i18n.tsx`, `web/src/es.ts`, `billcheck/es.py` |
| Price lookup | working (reference) | Published hospital prices for 50 common procedures at 17 Tucson and Phoenix hospitals. | `#/prices`, `Prices.tsx`; API `GET /search` |
| Mobile app in stores | planned (after Dec 9) | | not built |

**Ranked for a live demo (most impressive first)**
1. **Bill check with the example visit.** Tap "Read the example", the app reads two documents, and the result says
   "We found 1 likely error worth up to $1,818.00", with the reason, the source and a ready letter. It is a complete
   story in under a minute and uses no real data.
2. **"My insurer said no".** Paste "CO-197 precertification absent", pick a plan, and get a plain explanation, a dated
   deadline and an appeal letter. The Arizona numbers on the page (1 in 6 claims denied, 40% of appeals won) start
   conversations.
3. **"I can't afford it".** Choose Banner - University Medical Center Tucson, household of 3, income $42,000: "You may
   qualify for free care". Very visual and surprising to most visitors.
4. **Spanish switch.** One tap turns the whole result into Spanish. Quick and memorable.
5. **"A collector is after me".** Strong content (Arizona 3% cap), but the story needs more explaining.
6. **My visits** and **Price lookup.** Useful, but less of a "wow" in 30 seconds.

---

## 3. Key numbers

"Re-checked now" means the number was recomputed or re-read from its source on 2026-11-17 for this brief.

### Insurer denials in Arizona (R4, CMS data)
| Number | Meaning | Source | Re-checked now |
|---|---|---|---|
| **16.1%** (1,449,189 of 8,988,391) | Share of in-network claims denied by Arizona HealthCare.gov insurers in 2025 ("1 in 6"). | CMS Transparency in Coverage PUF, PY2027 file (2025 claims); `python -m pipeline.tc_puf`, `data/processed/r4_az_marketplace_denials.csv`, `research/r4/REPORT.md` | yes |
| **0.77 per 100 denials** (11,145 internal appeals) | People appealed fewer than 1 in 100 denials. Uses only insurers that reported both counts (Imperial's are suppressed). | same | yes |
| **40.2%** (4,477 of 11,145) | Share of internal appeals that won (the denial was overturned) in 2025. | same | yes |
| 20.1%, 0.78, 30.4% | The same three numbers for 2024 claims. | CMS PUF PY2026 file; same script | yes |
| 9.6% to 50.1% | Range of denial rates between the six Arizona insurers in 2025. | same | yes |
| 18.73% | National in-network denial rate, 2024 claims, all HealthCare.gov insurers; matches KFF's "about 19%", which validates our processing. | `data/processed/r4_us_marketplace_totals.csv` | yes |

### Medical debt (KFF)
| Number | Meaning | Source | Re-checked now |
|---|---|---|---|
| **41%** | of US adults "currently have some debt caused by medical or dental bills." | KFF Health Care Debt Survey, published June 16, 2022 (survey Feb 25 to Mar 20, 2022, 2,375 adults), https://www.kff.org/health-costs/kff-health-care-debt-survey/ | yes, against the KFF page |
| **44%** | of adults with health care debt "did not pay a bill in full in the past five years because they weren't sure the bill was accurate." | same | yes. The app's home page paraphrases it as "not sure it was correct"; on the poster use KFF's wording. |

### Hospital price files (the data layer)
| Number | Meaning | Source | Re-checked now |
|---|---|---|---|
| 46 | Phoenix and Tucson hospitals in our registry (38 Phoenix, 8 Tucson). | database table `hospitals`; `research/registry/` | yes (database) |
| 19 / **17** | Hospitals whose price files we processed / that gave usable coded prices (11 health systems). | `research/h1/REPORT.md`; database (17 hospitals with prices) | yes |
| **174,071** | Prices loaded, for 50 common procedures. | database table `prices` | yes |
| 2 of 19 | Processed hospitals whose file was not usable (non-standard layout, mislabelled codes). | `research/h1/REPORT.md` | yes (report) |
| 6 of 46 | Registry hospitals that block or refuse automated download (4 then downloaded by hand). | `research/h1/REPORT.md` | yes (report) |
| 2 of 19 | Hospitals that publish physician (doctor) fees for our 50 procedures (Valleywise, Mayo). | Manual check by the team, Oct 2026 (weekly update week 10, `docs/PLAN_V2.md`) | **no: there is no committed script; cannot be reproduced. Say "in our check" or leave it off.** |
| 1.92 (95% CI 1.82 to 2.39) | Median highest-to-lowest price ratio for the same procedure; pre-registered goal was 2, so H2 was not met. Phoenix 2.81, Tucson 1.39. | `data/processed/li2_h2_intervals.csv`, `research/h2/REPORT.md` | yes (file) |
| 2,696 rates, 17 hospitals | Published ER visit rates (levels 1 to 5) by insurer and plan, used by the ER check. | `data/processed/er_rates.csv` (`pipeline/er_rates.py`) | yes |
| 7,862 codes (9,526 rows) | Arizona 2026 Medicare physician fee amounts used for "N x Medicare". | `data/processed/medicare_pfs_az_2026.csv` | yes. **Conflict:** `docs/PROGRESS.md` and the week 12 update say "9,526 codes"; 9,526 is rows (code plus modifier), distinct codes are 7,862. |
| 103 | Arizona ground ambulance services with state-approved rates (ADHS). | `data/processed/az_ground_ambulance_rates.csv` | yes |

### AI benchmark (R2)
Error kinds planted (one per bill, 10 bills each, plus 20 clean bills): payment not subtracted, balance billing,
duplicate charge, charge not on the EOB, units above the CMS limit (MUE), code pair billed separately (NCCI), EOB
arithmetic error, allowed amount above the hospital's published rate.

How a checker is scored (`research/r2/run.py`, function `score`), for each of the 100 synthetic bills:
- **error caught**: on a bill with a planted error, the checker says there is an error;
- **false alarm**: on a clean bill, the checker says there is an error;
- **kind named**: it names the planted kind (or none on a clean bill);
- **amount due right**: its "amount the patient should pay" is within $1 of the true amount.
"Missed errors", "false alarms" and "wrong amount due" below are counts out of 80, 20 and 100.

Confirmatory run (100 new bills, seed 20261111, decision rule committed before the bills were generated; Jetstream2):

| Checker | Missed errors (of 80) | False alarms (of 20) | Wrong amount due (of 100) |
|---|---|---|---|
| ClearTab rules | 0 | 0 | 0 |
| AI reads the images, rules check (gemma-4-31b-it) | 0 | 0 | 0 |
| Our text recognition, rules check (no AI) | 0 | 0 | 0 |
| qwen-3.8-27b alone | 0 | 0 | 12 |
| gemma-4-31b-it alone | 6 | 6 | 6 |
| gpt-oss-120b alone | 14 | 2 | 24 |

Source: `research/r2/data_confirm/results.json`, `research/r2/REPORT.md`. Re-checked now: yes, recounted from the
results file. **Caveat:** the `research/r2/data*` folders (cases, model answers, results) are not committed to git;
they are reproducible with the scripts, but not visible in the public repo yet.
- Models tested: Groq pilot (Nov 2): openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.8-27b. Jetstream2 (Nov 11):
  gpt-oss-120b, gemma-4-31b-it, qwen-3.8-27b (muse-glimmer tried for photo reading only).
- Pilot on the free Groq tier for comparison: gpt-oss-120b missed 13, 1 false alarm, 29 wrong amounts; gpt-oss-20b
  30, 3, 31; qwen3.8-27b 46, 0, 42 (with reasoning turned off to fit the free tier).
- 800 model requests on Jetstream2 so far (counted from the cache files; usage is now logged).

### Other numbers
| Number | Meaning | Source | Re-checked now |
|---|---|---|---|
| 8 | Arizona health systems whose financial assistance policies are in the app (Banner, HonorHealth, Dignity/CommonSpirit, TMC, Mayo, Valleywise, Tenet/Abrazo and Carondelet, Northwest). | `data/processed/assistance_policies.json` | yes |
| 87.0% (114 of 131) | Agreement of two independent readers on those policies. | same file, `research/assistance/` | yes (file text) |
| 83 / 44 / 41 | Arizona acute and critical access hospitals / nonprofit (must have an assistance policy) / hospitals whose policy we collected (16 nonprofit still to collect). | `data/processed/r1_az_hospitals.csv` | yes |
| **57** | Automated tests (pytest), all passing; web: TypeScript and ESLint clean. There are no web unit tests. | `python -m pytest -q` run on 2026-11-17 | yes (run now) |
| 19 of 19 lines, 4 of 4 totals | Our on-server reader on 4 real, anonymized insurer EOBs. | team test, documents kept outside the repo for privacy; `docs/PROGRESS.md` | **no: cannot be reproduced by others (the documents are private). Say "in our test on 4 real, anonymized EOBs".** |
| 15,303 US / 385 AZ | CFPB medical debt complaints since 2025. | `docs/PROGRESS.md` only | **no: no committed script or download. Re-pull from the CFPB database before using.** |
| Usability study (R3) | Not started. Survey: 0 responses as of Nov 16; paused until the university IRB office (HSPP) answers. | | yes |

---

## 4. Research block

**H1. Is the hospital price data usable?** Federal law requires hospitals to publish machine-readable price files. We
found 46 Phoenix and Tucson hospitals, processed 19 files and checked them against the CMS format. 17 of 19 gave usable
coded prices (174,071 prices for 50 procedures), which passed our rule of at least 8. Access is the real problem: some
sites block downloads, some files have no negotiated rates, and only 2 of 19 list doctor fees (our manual check).

**H2. Do prices vary enough to matter?** For each procedure we compared the highest and lowest published price. The
median ratio was 1.92 (95% CI 1.82 to 2.39), just under our pre-registered goal of 2 (Phoenix 2.81, Tucson 1.39).
Because comparing prices before care helps less than we expected, and interviews showed the pain comes after care,
we turned ClearTab into a bill checker.

**R1. Can people get financial help from the hospital?** We read the financial assistance policies of 8 Arizona health
systems and turned them into income bands, documents and where to send them. A second reader checked every value
independently: 87.0% agreement, and every disagreement was settled against the document. Statewide, 44 of 83 Arizona
hospitals are nonprofit and must offer such a policy.

**R2. Can AI check a medical bill on its own?** We made 100 synthetic bill and EOB pairs with one planted error each
(and 20 clean ones) and compared our rules with open AI models. On a new confirmatory set, with the decision rule
written first, the rules and the "AI reads, rules check" setup made no mistakes. The best model alone found every
error too, but got the amount the patient should pay wrong on 12 of 100 bills; other models missed errors or raised
false alarms. ClearTab therefore keeps fixed rules for findings and amounts.

**R4. How often do Arizona insurers say no, and do people fight back?** We processed the public CMS file in which
every HealthCare.gov insurer reports claims, denials and appeals. In 2025, Arizona insurers denied 1 in 6 in-network
claims, fewer than 1 in 100 denials were appealed, and 40% of appeals won. This is why ClearTab now has a "My insurer
said no" page.

**R3. Does ClearTab help people? (planned)** A short usability study (find the amount owed, spot a planted error, with
and without ClearTab) waits for the IRB office's answer.

Chart-ready data (also saved as CSV in `docs/poster/data/`):

`r2_confirmatory.csv`: AI benchmark, one bar group per checker
```
checker,errors_missed_of_80,false_alarms_of_20,wrong_amount_due_of_100
ClearTab rules,0,0,0
AI reads + rules (gemma-4-31b-it),0,0,0
Text recognition + rules (no AI),0,0,0
qwen-3.8-27b alone,0,0,12
gemma-4-31b-it alone,6,6,6
gpt-oss-120b alone,14,2,24
```
Suggested chart: horizontal bars of "wrong amount due (of 100)" per checker; the rules sit at zero.

`r4_az_summary.csv`: Arizona denials (one simple funnel or three big numbers)
```
data_year,in_network_claims,denied,denial_rate_pct,internal_appeals,appeals_per_100_denials,appeals_won_pct
2025,8988391,1449189,16.12,11145,0.77,40.2
2024,7874919,1581162,20.08,12351,0.78,30.4
```
Also `r4_az_2025_by_insurer.csv` (denial rate per insurer, a bar chart) and `h2_price_ratio.csv`.

---

## 5. Tech stack

| Layer | What we use | Production or research |
|---|---|---|
| Languages | Python 3.12, TypeScript 5.8, SQL | production |
| Web app | React 19, Vite 6, plain CSS (system fonts), installable from the browser (web manifest), English and Spanish | production |
| API and rules | FastAPI with uvicorn; rule engine in `billcheck/` (Pydantic models) | production |
| Database | PostgreSQL 16 with full-text search and pg_trgm | production |
| Document reading | pdfplumber (PDF text layer), pypdfium2 (render scanned PDFs), Pillow, RapidOCR (PP-OCRv4 mobile detection, PP-OCRv6 recognition) on ONNX Runtime, CPU only, on our server | production |
| Data pipeline | pandas, polars, ijson (streams files up to 2 GB), pyarrow, openpyxl; CMS hospital price files, CMS NCCI/MUE, CMS physician fee schedule, CMS Transparency in Coverage, ADHS ambulance rates | production data, built offline |
| Hosting | Docker Compose: Postgres, API, Caddy 2 (HTTPS and static files); no access logs | ready, not deployed (section 8) |
| Quality | pytest (57 tests), ruff, ESLint, TypeScript strict; GitHub | development |
| AI models | Jetstream2 Inference (Indiana University, ACCESS allocation through Prof. Greg Chism): gpt-oss-120b, gemma-4-31b-it, qwen-3.8-27b; Groq free tier for the pilot (openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.8-27b) | **research and synthetic examples only.** Production runs `READ_MODE=local`: no document goes to any AI service. |

Note: `deploy/compose.yml` still passes the AI keys and `READER_PROVIDERS` to the API, but they are unused while
`READ_MODE=local` (the default in `deploy/compose.yml` and `deploy/.env.example`).

---

## 6. Visual identity

From `web/src/index.css` (light theme; the app also has a dark theme):

| Token | Hex | Use |
|---|---|---|
| accent (primary) | `#0f6b74` | brand teal: buttons, links, "Tab" in the wordmark, icon background |
| accent-soft | `#e2f0f1` | light teal fills, selected tab |
| icon fold | `#d9eef0` | folded corner in the icon |
| paper (page background) | `#f7f9fa` | app background (use white `#ffffff` on the poster) |
| card | `#ffffff` | cards |
| ink (text) | `#15232b` | main text, "Clear" in the wordmark |
| muted (secondary text) | `#56666f` | captions |
| rule (lines) | `#d4dde2` | borders |
| ok (success) | `#1d6b3a` on `#e6f4ea` | "Checked" |
| warning | `#8a5300` on `#fdf1df` | "Ask about this" |
| error | `#b42318` on `#fdecea` | "Likely error" |
| info | `#255f9e` on `#e7f0fa` | "Good to know" |
| focus | `#f0a500` | keyboard focus ring |

- Fonts: system UI stack (`system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial`); numbers and letters in
  a monospace stack (`ui-monospace, "SF Mono", Menlo, Consolas`). For the poster, Inter or Segoe UI matches the look.
- Border radius: 14px for cards and main buttons (`--radius`), 12px for small icon tiles, fully round (999px) for
  the language switch and top navigation; the app icon uses 96 on a 512 square (about 19%).
- Assets: `web/public/icon.svg` (app icon: white bill with a folded corner and a teal check mark on a teal rounded
  square; also the favicon and the installed-app icon), `web/public/manifest.webmanifest` (theme `#0f6b74`).
- Logo: the app had an icon but no full logo. `docs/poster/logo.svg` is a horizontal lockup made from the existing
  icon plus the "ClearTab" wordmark in the app's two colors (vector, any size).
- Other logo ideas if the team wants a change: (a) a receipt with a torn zig-zag bottom edge and a check mark;
  (b) a magnifying glass over a bill line with a dollar sign; (c) a "tab" shape (folder tab) with a check, playing on
  the name. The current icon already reads well at small sizes, so we suggest keeping it.

---

## 7. Screenshots

Captured with Playwright from the local app (API in `READ_MODE=local`, synthetic sample documents only, no real
patient data). Mobile: 390 x 844 at 3x (1170 x 2532 px). Desktop: 1440 x 900 at 2x (2880 x 1800 px). "Full" files are
the whole scrolling page with the sticky bars un-stuck.

| File | Caption |
|---|---|
| `screens/01_home_mobile.png` | Home: "Got a hospital bill?", scan or ask for help, no account, English and Spanish. |
| `screens/01b_home_mobile_full.png` | Home, full page: all six doors and "Why this matters" (KFF numbers). |
| `screens/02_bill_upload_mobile.png` | Scan a bill: take a photo or upload a PDF; read on our own server, not sent to any AI service. |
| `screens/03_bill_read_lines_mobile.png` | The lines read from the sample EOB, to confirm before the check. |
| `screens/04_bill_results_mobile.png` | Result: "We found 1 likely error worth up to $1,818.00." |
| `screens/04b_bill_results_mobile_full.png` | Result, full page: why, what to do, sources, checks that passed (ER rate matches the hospital's published rate). |
| `screens/05a_bill_letter_mobile.png` | The dispute letter, filled in on the page. |
| `screens/05b_bill_phone_script_mobile.png` | The phone script with the exact amounts to quote. |
| `screens/05_bill_dispute_kit_mobile_full.png` | The whole dispute kit, full page. |
| `screens/06_denial_result_mobile.png` | "My insurer said no": what the denial means, with Arizona's denial numbers. |
| `screens/06b_denial_result_mobile_full.png` | Denial, full page: first step, deadlines with dates, call script. |
| `screens/07_assistance_result_mobile.png` | "I can't afford it": "You may qualify for free care" at Banner - UMC Tucson, and how to apply. |
| `screens/07b_assistance_result_mobile_full.png` | Financial assistance, full page. |
| `screens/08_collector_result_mobile.png` | "A collector is after me": dispute deadline and Arizona's 3% interest cap. |
| `screens/09_home_spanish_mobile.png` | The home page in Spanish. |
| `screens/10_denial_spanish_mobile.png` | A denial result in Spanish. |
| `screens/11_home_desktop.png` | Desktop home page with all six doors. |

Sample inputs used: the built-in example visit (synthetic ER EOB and bill); denial text "CO-197: Precertification/
authorization absent", job-based plan, notice Nov 2, 2026, emergency; assistance: Banner - University Medical Center
Tucson, household of 3, $42,000 a year, insured; collector: agency letter received Nov 5, 2026, care on Mar 10, 2025,
$420 at 8% interest.

---

## 8. Public beta

**There is no public URL yet.** What is left:
1. A server. The Oracle Cloud Always Free sign-up failed with a generic error (Nov 16); options are to fix it (existing
   account, VPN, card address) or use Azure for Students ($100 credit, UA email).
2. Copy the database and reference data to the server and start `deploy/compose.yml` (about an hour once the server
   exists).
3. A domain. `cleartab.app` is taken; `mycleartab.com` was available on Nov 10 (not bought). Until then the site can
   run at `https://<server IP>.sslip.io`, which changes if the server changes.
4. Merge the PRs into `main` (they need a teammate's approval).

For the QR code: wait for the final domain. If the poster must be printed first, point the QR code at a short link you
control (for example a GitHub Pages redirect) and update the target later. GitHub repository (already public):
https://github.com/MrazzKa/cleartab

---

## 9. Team and credits

Team Trace (ISTA 498 Capstone, Fall 2026, Group 2), as listed in the project plan and the weekly updates:
- Timur Kamarayev, Project Manager
- Nikita Balashov, Frontend and UX
- Danil Chaikin, Backend
- Artyom Prudelyuk, Data and ETL (pipeline, QA)

Faculty advisor: Dr. Lingyao Li. Instructor: Michael McKisson. With thanks to Prof. Greg Chism (Jetstream2 access)
and the UA Campus Health insurance office (interview). No role conflict was found.

---

## 10. Do not claim

Must not say, or must say carefully:
- **"Not legal or medical advice."** The app says it in the footer and on every letter page; the poster should too.
  Letters are sent by the person, not by ClearTab.
- **"Nothing is stored."** True for the server as written in the code: the API logs only method, path and status
  (`api/main.py`), uvicorn runs with `--no-access-log`, Caddy has no access log, uploaded documents are processed in
  memory and not written to disk (`billcheck/local_reader.py`, `billcheck/reader.py`). Careful: (a) the rate limiter
  keeps visitor addresses in memory for up to 24 hours (never written or logged, `api/limits.py`); (b) "My visits" is
  saved in the visitor's own browser; (c) this holds only in `READ_MODE=local`. Say "read on our server and not kept",
  not "nothing ever leaves your phone".
- **"No AI reads your documents."** True only in production mode `READ_MODE=local`. The code can also send documents
  to AI services in other modes (used for research and the synthetic examples). Do not say "ClearTab uses no AI at
  all": AI models are part of the research.
- **"AI can't check bills."** Not supported: the best model alone found every planted error in our test; the
  difference was the amount owed (12 of 100 wrong) and other models' mistakes. All test bills were synthetic, from one
  template, one hospital and one insurer, with one error each, and the prompt listed the error kinds.
- **Accuracy on real bills.** Not measured beyond our test on 4 real, anonymized EOBs. Phone photos (angle, light,
  folds) are not systematically tested. Say "tested on sample documents and a few real statements".
- **Rules engine limits.** It checks only what it has rules for: EOB math, bill vs EOB, duplicates, CMS unit limits and
  code pairs, No Surprises Act, published hospital and ER rates, Medicare yardstick, global surgery period, Arizona
  ambulance rates, plan balances. It cannot judge medical necessity or coding quality, and it does not know a
  person's plan documents. Hospital prices cover 17 hospitals and 50 procedures in Tucson and Phoenix only.
- **Coverage.** Financial assistance: 8 health systems, not all Arizona hospitals. Denial data: HealthCare.gov plans
  only, not job-based plans, AHCCCS or Medicare.
- **Users and impact.** No real users yet, no usability results, survey 0 responses, no real case outcomes. Do not
  claim people helped or money saved.
- **Not online yet.** Do not print "available now" unless the beta is live by Dec 9.
- **Spanish** has not been reviewed by a native speaker.
- **Numbers to avoid or re-check:** "2 of 19 hospitals publish physician fees" (not reproducible), CFPB 15,303 / 385
  (not reproducible), "9,526 codes" (it is 7,862 codes), the KFF 44% (use KFF's exact wording).
- **Self-reported data.** The CMS denial numbers are reported by insurers and not audited; CMS warns that denial rates
  do not measure plan quality. One insurer reported zero appeals for 518,619 denials, which looks like a reporting gap.
- **Names and logos** of hospitals and insurers appear only as data sources; do not imply partnership or endorsement.
