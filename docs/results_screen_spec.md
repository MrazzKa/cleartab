# Results screen specification (Feature 2 comparison + Feature 6 call summary)

Owner: Nikita Balashov (UI). Data contract: `GET /search` in api/main.py. Wireframe: web/wireframes/results.html.
Targets from proposal Tables 6, 7, 10, 11: up to 10 hospitals, three price types side by side with methodology
labels, city and straight-line distance, default sort lowest price, explainer on the same screen, mobile first
to 360 px, WCAG 2.1 AA, colour never the only signal, no accounts and no stored searches.

## 1. Inputs (one form, top of screen)
| Field | Control | Values | Notes |
|---|---|---|---|
| Procedure | text box with autocomplete (`GET /procedures/suggest?q=`, from 2 letters, target under 150 ms) | plain words or a code (CPT, HCPCS, MS-DRG) | shows plain name + code in the list |
| Plan | select | "No insurance (cash price)" + the 11 canonical insurers from `GET /plans` | default: No insurance |
| ZIP code | text box, 5 digits, numeric keyboard on phones | Arizona ZIP | not stored; used only for distance and metro |
| Search | button | - | Enter key also submits |

No GPS permission is ever requested (proposal 6.1).

## 2. Sort
- Default: lowest **applicable price** first. Applicable price = cash price when the plan is "No insurance";
  otherwise the plan's negotiated median, or the allowed-amount median when the plan has only percent or
  algorithm rates. Hospitals with no applicable price go last, then by distance.
- Alternative: nearest first (toggle, no new request; the client re-sorts).
- Results are limited to the user's metro (Tucson or Phoenix), chosen by the hospital nearest the ZIP centre.

## 3. Result row (one card per hospital on phones, one table row on wide screens)
| Field | API source | Display rule |
|---|---|---|
| Hospital name | results[].hospital | heading, links to provenance |
| City | results[].city | text |
| Distance | results[].distance_miles | "4.2 miles (straight line from your ZIP)"; hidden if no ZIP |
| Gross charge | results[].gross.amount | label "List price (gross charge)"; small, grey; never the first number |
| Cash price | results[].cash.amount | label "Cash price"; bold when plan = No insurance |
| Negotiated rate | results[].negotiated | see section 4 |
| Methodology label | gross / cash / negotiated .methodology | plain text under each figure: "fixed dollar amount", "percent of charges", "per diem", "algorithm" |
| Several items | gross.items, cash.items, negotiated.rates_count | "median of 3 published rates, $245 to $350" when more than 1 |
| Completeness | results[].completeness.label (+ score) | text label "Complete", "Partial", "Not published" plus an icon; the label is always written out |
| Source | provenance.source_url, downloaded_at, file_last_updated, file_version | collapsed "Where this number comes from" with the link, download date, file date and version |
| Call summary | button "Prepare a call" | opens section 6 in place (one tap, proposal Table 11) |

Missing values are written as "Not published" in words, never as $0 or a blank.

## 4. Negotiated column states
| negotiated.kind | What the user sees |
|---|---|
| negotiated rate | "$254 negotiated rate" (median) + range line + "fixed dollar amount" |
| allowed amount estimate | "About $180 (allowed amount estimate, typical range $120 to $260)" + methodology; never styled as a price |
| not a dollar amount | "This plan's rate is a percent of charges, not a dollar amount. Ask the hospital." No number shown |
| plan not matched | "Plan not matched: this hospital's file has no rate we could link to your plan." No number shown |
| (plan = No insurance) | column hidden; cash price is the headline |

## 5. "Not published" list
Below the results, a section "Hospitals near you without usable prices" lists not_published[]: hospital,
city, the reason in words ("No usable price file", "Blocked automated access", "Not checked yet"), the URL that
was checked and the date (proposal 6.7 item 3). It also says: "This is about the price file only, not about
the quality of care."

## 6. Explainer (same screen, above the results on phones, beside them on wide screens)
Text from api/main.py, 519 characters, 91 words, Flesch-Kincaid grade 7.2 (research/readability.py):

> These are prices the hospital published for its own part of the care, called the facility charge. They do not include the doctor's fee, which is billed separately. The gross charge is the list price that almost no one pays. The cash price is what the hospital says it charges people who pay for themselves. A negotiated rate is the amount a hospital agreed with an insurance plan; what you pay depends on your deductible and coinsurance. Your final bill can be different. Call the hospital to confirm before your visit.

Below it: a link to hospital financial assistance and charity care, and the plain-language privacy page
(proposal 6.2 item 3, 6.5). Statement: "ClearTab never asks for payment, insurance ID or Social Security
numbers." (6.3 item 4)

## 7. Call preparation summary (Feature 6)
Opens in place from a result row, fits one phone screen (360 x 640), and has two buttons: Copy and Print.
Print uses a print stylesheet (black text, no navigation). Nothing is sent or stored.

```
Calling: <hospital name>   <phone>
Procedure: <plain name> (CPT <code>)
Published cash price: $<cash>            (file dated <file_last_updated>)
Published negotiated range for <plan>: $<min> - $<max>   or "not published as a dollar amount"
Questions to ask:
 1. What is the all-in estimate for CPT <code>, including every bill I will get?
 2. Is the doctor's (physician) fee included, or billed separately?
 3. Is this cash price available to me, and what do I need to do to get it?
Source: <source_url>
```

## 8. Accessibility and layout
- Mobile first; tested at 360 px width; no horizontal scroll; tap targets at least 44 px.
- WCAG 2.1 AA contrast (4.5:1 text). Cheapest result is marked with the word "Lowest", not only a colour.
- Numbers right-aligned in table view with the dollar sign; screen readers get "cash price 292 dollars".
- The completeness label is text plus icon; the methodology is always text.
