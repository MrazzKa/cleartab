# R2 pilot: can a language model check a medical bill? (2026-11-02, exploratory)

**Status: pilot, exploratory.** The results below were seen before a decision rule was written. The confirmatory
run (new seed, rule fixed in advance in docs/PROPOSAL_V2_CHANGES.md, H4) follows.

## Design
- **Cases** (`python -m research.r2.cases`, seed 20261102): 100 synthetic pairs of an explanation of benefits (EOB)
  and a hospital statement for an in-network outpatient visit at Banner - University Medical Center Tucson with
  Blue Cross Blue Shield of Arizona. Allowed amounts are drawn inside the rates the hospital published for that
  insurer. 20 cases are clean; 80 carry one planted error, 10 of each kind: payment not subtracted, balance
  billing, duplicate charge, charge not on the EOB, units above the CMS medically unlikely edit (73721, limit 3),
  NCCI code pair (45380 with 45378, modifier indicator 0), EOB arithmetic error, allowed amount above the published
  rate. Every statement adds up (charges - insurance - contractual adjustment - patient payments = amount due), as
  real statements do. No real patient data.
- **Conditions** (`python -m research.r2.run`):
  - A: the ClearTab rule engine on the exact structured case, with the published prices from the database.
  - B: a language model reads both documents as text and answers in JSON (error or not, which kinds, the correct
    amount due). The prompt gives the published rates for the four services and the MUE limit, so the models have
    the same reference facts as the rules (they are not told the NCCI pair). Models: `openai/gpt-oss-120b`,
    `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` (open weights, Groq, temperature 0; qwen with reasoning off and 600
    output tokens because of the free tier's output limit).
  - C: `qwen/qwen3.8-27b` reads rendered images of the two documents (`node research/r2/render.cjs`) into fields
    with the ClearTab reader (billcheck/reader.py), then the rule engine checks them. 40 cases (4 per error kind,
    8 clean) because of the free tier's limits.
- **Scores**: errors caught (sensitivity), clean bills passed (specificity), the main error kind named, and the
  correct amount due within $1.

## Results
| Condition | Errors caught | Clean passed | Kind named | Amount due right |
|---|---|---|---|---|
| A ClearTab rules | 100% (80/80) | 100% (20/20) | 100% | 100% |
| B gpt-oss-120b | 84% | 95% | 83% | 71% |
| B gpt-oss-20b | 63% | 85% | 64% | 69% |
| B qwen3.8-27b | 43% | 100% | 54% | 58% |
| C qwen3.8-27b reads images + rules, **12 of 40 so far** | 10 of 10 | 2 of 2 | 10 of 12 | 12 of 12 |

By error kind (caught and named; of 10, clean of 20):

| Error | gpt-oss-120b | gpt-oss-20b | qwen3.8-27b |
|---|---|---|---|
| Payment not subtracted | 1 | 0 | 0 |
| Balance billing | 9 | 8 | 7 |
| Duplicate charge | 10 | 9 | 10 |
| Charge not on the EOB | 9 | 8 | 6 |
| Units above MUE | 10 | 9 | 6 |
| NCCI code pair | 7 | 0 | 0 |
| EOB arithmetic | 8 | 4 | 0 |
| Allowed above published rate | 10 | 9 | 5 |
| Clean (no false alarm) | 19 of 20 | 17 of 20 | 20 of 20 |

Condition C stopped at 12 of 40 cases on 2026-11-02: the free tier allows 200,000 qwen tokens per day and each
image pair uses about 3,500. Rerun `python -m research.r2.run --conditions A,C` the next day to complete it (cached
reads are kept). In the 12 cases read so far the totals on both documents were read exactly in all 12; both missed
kinds are NCCI pairs, where a misread line changed which codes the rules saw.

## Reading the results
- The rule engine was built for these eight kinds of error, so its 100% is an upper bound on these cases, not an
  accuracy claim for real bills.
- The models catch errors that show on the page (duplicates, a units number, a price above a given range) and miss
  errors that need a relation between the two documents. A payment that was not subtracted, the problem the Campus
  Health insurance office described first, was caught once in 30 model answers: the statement adds up, the amount
  due equals the EOB's "what you owe", and the models conclude it is correct without subtracting the copay already
  paid.
- The amount the patient should pay was right in 58-71% of model answers; the rules give it in every case.
- Implication for the product, pending the confirmatory run: models are useful for reading documents; findings and
  amounts stay with the rules.

## Limits
Synthetic cases from one hospital and one insurer; one error per case; text versions are cleaner than real bills;
free-tier settings (qwen without reasoning) may understate qwen; a single prompt; no human baseline yet (R3 adds
one).
