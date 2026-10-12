"""Draw the 200 payer strings for the inter-rater test. Seed and method are fixed here and in REPORT.md.

Method: from the distinct (raw_payer, raw_plan) strings in data/processed/payer_aliases.csv, draw 100 without
replacement with probability proportional to row_count, then 100 uniformly from the strings not yet drawn
(so rare strings are included). Order is shuffled so raters cannot tell which half a string came from.
"""
import csv
import random

SEED = 20261012
N_WEIGHTED, N_UNIFORM = 100, 100

with open("data/processed/payer_aliases.csv", newline="") as f:
    pool = list(csv.DictReader(f))
with open("data/processed/payer_strings.csv", newline="") as f:
    where: dict = {}
    for r in csv.DictReader(f):
        where.setdefault((r["raw_payer"], r["raw_plan"]), []).append((int(r["row_count"]), r["hospital"]))

rng = random.Random(SEED)
remaining = list(pool)
chosen = []
for _ in range(min(N_WEIGHTED, len(remaining))):
    pick = rng.choices(remaining, weights=[int(r["row_count"]) for r in remaining])[0]
    chosen.append(pick)
    remaining.remove(pick)
chosen += rng.sample(remaining, min(N_UNIFORM, len(remaining)))
rng.shuffle(chosen)

for name in ("irr_rater_A.csv", "irr_rater_B.csv"):
    with open(f"research/h2/{name}", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["raw_payer", "raw_plan", "hospital", "canonical_payer", "plan_type", "notes"])
        for r in chosen:
            hosp = max(where[(r["raw_payer"], r["raw_plan"])])[1]
            w.writerow([r["raw_payer"], r["raw_plan"], hosp, "", "", ""])
print(f"{len(chosen)} strings written (pool {len(pool)}), seed {SEED}")
