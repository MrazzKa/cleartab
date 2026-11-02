# Second reader: hospital financial assistance policies

**Who:** Artyom (data owner). **Time:** about 2 hours. **Due:** Thursday, Nov 5 (before the Nov 9 demo).

## Why
The "Help paying" screen tells people whether they may get free or discounted care at each hospital. The values in
`data/processed/assistance_policies.json` were read by one person from each health system's own documents. Same
rule as the payer dictionary: nothing goes in front of users until a second person has checked it independently.

## What to do
1. Open `research/assistance/second_reader.csv` in Excel or Google Sheets (131 items: one row per value).
2. For each row, open the `source_url` (the hospital's own PDF or page) and find the value yourself.
   - Do **not** look at other rows' answers for the same system first; check each value against the document.
3. Fill in:
   - `second_reader_agrees (Y/N)`: Y if the document says the same thing (same number, same meaning), N if not.
   - `second_reader_value_if_different`: what the document actually says, when you put N.
   - `page_or_quote`: the page number or a short quote where you found it (always, for Y and N).
   - `note`: anything unclear (for example the document contradicts itself, or the link is broken).
4. Income bands: check the edges carefully. "Below 200%" and "up to 200%" are different: a family exactly at 200%
   is in the first band in one case and not in the other.
5. "not published" rows: search the hospital's website for a policy with income limits. If you find one, put N and
   the link and values. If you cannot find one, put Y.
6. Save as CSV with the same name and columns, and send it back (Slack or commit on a branch).

## Then
`python -m research.assistance.score_second_reader` prints agreement and lists every disagreement. Timur and
Artyom resolve each one together with the document open; only then is the JSON changed, and the change is noted in
docs/PROGRESS.md.

## Rules
- The documents are public. No personal data is involved.
- Do not change `assistance_policies.json` yourself; disagreements are resolved jointly.
- If a link no longer works, note the date and what you see instead; do not use a third-party summary site
  (careroute.ai, healthbillcentral.com and similar) as a source.
