"""Draw the 200 payer strings for one round of the inter-rater test. Seeds and method are fixed here and in
REPORT.md.

Usage: python -m research.h2.make_irr_sample ROUND   (1 or 2; files that already exist are never overwritten)

Method: from the distinct (raw_payer, raw_plan) strings in data/processed/payer_aliases.csv, minus the strings
used in earlier rounds, draw 100 without replacement with probability proportional to row_count, then 100
uniformly from the strings not yet drawn (so rare strings are included). Order is shuffled so raters cannot
tell which half a string came from. Round 1: seed 20261012. Round 2 (after the round 1 guide was clarified):
seed 20261013, round 1 strings excluded.
"""
import csv
import os
import random
import sys

ROUND = int(sys.argv[1]) if len(sys.argv) > 1 else 2
SEED = {1: 20261012, 2: 20261013}[ROUND]
N_WEIGHTED, N_UNIFORM = 100, 100

with open("data/processed/payer_aliases.csv", newline="") as f:
    pool = list(csv.DictReader(f))
with open("data/processed/payer_strings.csv", newline="") as f:
    where: dict = {}
    for r in csv.DictReader(f):
        where.setdefault((r["raw_payer"], r["raw_plan"]), []).append((int(r["row_count"]), r["hospital"]))

used = set()
for earlier in range(1, ROUND):
    with open(f"research/h2/irr_round{earlier}_rater_A.csv", newline="") as f:
        used |= {(r["raw_payer"], r["raw_plan"]) for r in csv.DictReader(f)}
rng = random.Random(SEED)
remaining = [r for r in pool if (r["raw_payer"], r["raw_plan"]) not in used]
eligible = len(remaining)
chosen = []
for _ in range(min(N_WEIGHTED, len(remaining))):
    pick = rng.choices(remaining, weights=[int(r["row_count"]) for r in remaining])[0]
    chosen.append(pick)
    remaining.remove(pick)
chosen += rng.sample(remaining, min(N_UNIFORM, len(remaining)))
rng.shuffle(chosen)

PLAN_TYPES = ["commercial", "medicare advantage", "medicare supplement", "ahcccs", "marketplace", "government",
              "workers comp", "rental network", "unknown"]


def write_xlsx(name: str) -> None:
    """Excel copy with drop-down lists, so a rater only picks values (same rows as the CSV)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    from pipeline.payers import CANONICAL
    wb = Workbook()
    ws = wb.active
    ws.title = "label"
    lists = wb.create_sheet("lists")
    for i, v in enumerate(CANONICAL, 1):
        lists.cell(i, 1, v)
    for i, v in enumerate(PLAN_TYPES, 1):
        lists.cell(i, 2, v)
    ws.append(["raw_payer", "raw_plan", "hospital", "canonical_payer", "plan_type", "notes"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in chosen:
        ws.append([r["raw_payer"], r["raw_plan"], max(where[(r["raw_payer"], r["raw_plan"])])[1], "", "", ""])
    n = len(chosen) + 1
    dv1 = DataValidation(type="list", formula1=f"=lists!$A$1:$A${len(CANONICAL)}", allow_blank=False)
    dv2 = DataValidation(type="list", formula1=f"=lists!$B$1:$B${len(PLAN_TYPES)}", allow_blank=False)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(f"D2:D{n}")
    dv2.add(f"E2:E{n}")
    fill = PatternFill("solid", fgColor="FFF2CC")
    for row in ws.iter_rows(min_row=2, min_col=4, max_col=5):
        for c in row:
            c.fill = fill
    for col, w in zip("ABCDEF", (38, 44, 34, 40, 20, 30), strict=True):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    wb.save(f"research/h2/{name}")


names = [f"irr_round{ROUND}_rater_{x}.{ext}" for ext in ("xlsx", "csv") for x in "AB"]
if any(os.path.exists(f"research/h2/{n}") for n in names):
    sys.exit(f"round {ROUND} files already exist; not overwritten")
for name in names[:2]:
    write_xlsx(name)

for name in names[2:]:
    with open(f"research/h2/{name}", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["raw_payer", "raw_plan", "hospital", "canonical_payer", "plan_type", "notes"])
        for r in chosen:
            hosp = max(where[(r["raw_payer"], r["raw_plan"])])[1]
            w.writerow([r["raw_payer"], r["raw_plan"], hosp, "", "", ""])
print(f"round {ROUND}: {len(chosen)} strings written (pool {eligible} of {len(pool)}), "
      f"seed {SEED}")
