# Contributing to ClearTab

## Branches
- Changes reach `main` only through pull requests approved by a team member who is not the author, with CI passing.
- Branch names: `<area>/<short-description>`, where area is one of `pipeline`, `db`, `api`, `web`, `research`, `docs`, `ci`. Example: `pipeline/csv-wide-parser`.
- One topic per branch. Small commits with messages in the imperative ("Add wide CSV parser").

## Pull requests
- Open a PR into `main` using the template. Fill in "How I tested this" with the exact commands or clicks.
- Link the GitHub Issue it closes.
- The reviewer runs or reads the change; code its author cannot explain in review is not merged (proposal 11.2, item 16.3).
- Never commit raw hospital files (`data/raw/` is gitignored), credentials or personal data.

## Definition of done
A task is done when someone other than its owner has run it, read it or clicked through it and confirmed it does what the issue said. The owner moves the issue to review; only the reviewer closes it.

## Data rules
- Never invent a number, URL, quote or result; if something could not be obtained, write "not found" and why.
- Every data table has source_url and retrieved_at columns.
- Respect robots.txt (RFC 9309), at most 1 request per second per domain and 1 download per file per run, with the ClearTab user agent. Files that robots.txt blocks are downloaded by a person into data/raw/manual/ (see MANUAL_DOWNLOADS.md).
- Stream large files (ijson for JSON, chunked reads for CSV); never load a whole file into memory.
- Do not fix bad data silently: percentages, multipliers and implausible values stay flagged and are never turned into a dollar price.
- Plain English in reports, regular hyphens only.
