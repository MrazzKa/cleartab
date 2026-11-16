# R4: claim denials and appeals of Arizona Marketplace insurers (2026-11-16)

**Question.** How often do Arizona's HealthCare.gov insurers deny in-network claims, how often do people appeal,
and how often do appeals win? This is the evidence behind ClearTab's "My insurer said no" page.

**Data.** CMS Transparency in Coverage public use file, PY2027 file (2025 claims) and PY2026 file (2024 claims),
https://www.cms.gov/marketplace/resources/data/public-use-files . Issuer-level counts, self-reported by insurers to
CMS, for individual plans sold on HealthCare.gov (Arizona uses it). Not included: job-based plans, AHCCCS,
Medicare. Cells CMS suppressed for small counts ("**") are left empty. `python -m pipeline.tc_puf --download`
rebuilds everything from the raw files:
- data/processed/r4_az_marketplace_denials.csv (one row per Arizona insurer and year)
- data/processed/r4_az_denial_reasons.csv (2025, in-network denials by reason, summed over each insurer's plans)
- data/processed/r4_us_marketplace_totals.csv (all HealthCare.gov insurers with reported counts)

Check against published work: our national in-network denial rate for 2024 is 18.73% (158 insurers); KFF and a
MoneyGeek analysis of the same file report about 19%.

## Arizona, all insurers with reported counts
| Data year | Insurers | In-network claims | Denied | Denial rate | Internal appeals | Appeals per 100 denials | Appeals won |
|---|---|---|---|---|---|---|---|
| 2025 | 6 | 8,988,391 | 1,449,189 | 16.1% | 11,145 | 0.77 | 4,477 (40.2%) |
| 2024 | 6 | 7,874,919 | 1,581,162 | 20.1% | 12,351 | 0.78 | 3,753 (30.4%) |

National (all HealthCare.gov insurers with reported counts): 15.71% denied in 2025, 18.73% in 2024.
"Appeals per 100 denials" uses only insurers that reported both numbers.

## By insurer, 2025 (in network)
| Insurer | Claims | Denied | Denial rate | Appeals filed | Overturned |
|---|---|---|---|---|---|
| Health Net of Arizona | 4,767,071 | 518,619 | 10.9% | 0 (as reported) | 0 |
| UnitedHealthcare of Arizona | 3,020,935 | 740,183 | 24.5% | 1,462 | 790 (54.0%) |
| Blue Cross Blue Shield of Arizona | 802,431 | 116,772 | 14.6% | 6,235 | 3,007 (48.2%) |
| Oscar Health Plan | 387,568 | 69,003 | 17.8% | 3,448 | 680 (19.7%) |
| Imperial Insurance Companies | 8,920 | 4,472 | 50.1% | suppressed | suppressed |
| Antidote Health Plan of Arizona | 1,466 | 140 | 9.6% | 0 | 0 |

## What this shows
- About 1 in 6 in-network claims of Arizona Marketplace plans was denied in 2025 (1 in 5 in 2024).
- People appealed fewer than 1 in 100 denials, both years.
- When they did, 40% of appeals won in 2025 (30% in 2024); at two of the large insurers about half won.
- Denial rates differ widely between insurers (from about 10% to 50%), which a person cannot see when choosing a
  plan. CMS warns that denial rates are not necessarily a measure of plan quality: many denials are resubmitted or
  are duplicate or administrative.

## Limits
- Self-reported by insurers; not audited. Health Net reported zero internal appeals of claims for 518,619 denials in
  2025 and 502 in 2024, which looks like a reporting gap rather than a fact about its members.
- A denied claim is not always a person's bill: many are fixed by the provider resubmitting. The file does not say
  how much money the denials were.
- The plan-level reason columns do not add up to the insurer totals (they cover different subsets and some cells
  are suppressed), so the reasons file is reported per insurer only, and "other" or "administrative" is often the
  largest reason. We do not compare reasons between insurers.
- Marketplace plans only: in Arizona most people are in job-based plans, AHCCCS or Medicare, which this file does
  not cover.
