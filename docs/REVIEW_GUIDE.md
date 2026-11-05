# Review guide for the open pull requests (#15-#24)

Rule (CONTRIBUTING.md): every pull request needs an approval from a team member who is not the author. The
PRs are stacked: each one is based on the previous branch, so they are merged in order, starting with #15.

## Who reviews what (proposal; swap if needed)
| PR | Branch | What it contains | Reviewer |
|---|---|---|---|
| #15 | pipeline/phase1-registry | Hospital registry, discovery of price files (cms-hpt.txt) | Danil |
| #16 | pipeline/phase2-h1 | Download and parsing of hospital files, H1 result | Danil |
| #17 | pipeline/phase3-procedures | 50 launch procedures and their codes | Artyom |
| #18 | pipeline/phase4-normalization | Payer dictionary, methodology labels, flags | Artyom |
| #19 | pipeline/phase5-etl | Database load, completeness score | Danil |
| #20 | api/phase6-search | Search API and the first web screens | Nikita |
| #21 | research/advisor-followup | Advisor data pack, H2 intervals, inter-rater round 2 | Artyom |
| #22 | research/discovery | Cash vs per-insurer rate analysis | Artyom |
| #23 | feature/bill-check | v2: bill check, dispute kit, assistance finder, document reading, Spanish, My visits | Nikita (web) + Danil (api, billcheck) |
| #24 | deploy/beta | Docker stack for the public beta, reading limits | Danil |

## What to check (about 20-30 minutes per PR)
Large PRs are mostly data and generated files; do not read every line. Check these:
1. **It runs.** `git fetch && git checkout <branch>`, then `.venv/bin/python -m pytest -q` and
   `.venv/bin/python -m ruff check .` pass. For web changes: `cd web && npm ci && npx tsc -b && npx eslint .`.
2. **Nothing private is committed.** No raw hospital files (`data/raw/`), no `.env`, no API keys, no names or
   personal data, no CPT descriptor tables (NCCI/MUE stay in `data/raw/`).
3. **Numbers match the log.** Pick two numbers from the PR's entry in `docs/PROGRESS.md` and confirm the file
   they come from exists and shows them (for example `data/processed/f4_coverage.csv`).
4. **Every data table has `source_url` and `retrieved_at`** (hard rule 2).
5. **Read one core file properly.** Suggested: #15 `pipeline/load_registry.py` and `pipeline/robots.py`, #16 `pipeline/parsers/`, #18
   `pipeline/normalize.py`, #19 `pipeline/run.py`, #20 `api/main.py`, #23 `billcheck/rules.py` and
   `web/src/pages/`, #24 `deploy/compose.yml` and `api/limits.py`. Leave comments on anything unclear.
6. **Try it** (#20, #23, #24): run the app (README) and click through one example bill.

Approve in GitHub (Files changed -> Review changes -> Approve) or request changes with a comment.

## Merging (PM, after approval)
1. Merge #15 into main with "Create a merge commit", and tick "Delete branch".
2. GitHub then retargets #16 to main automatically; merge it the same way. Repeat up to #24.
3. If a later PR shows conflicts after retargeting, the author rebases it on main and pushes.

Target: all merged by Nov 12, so the beta runs from main.
