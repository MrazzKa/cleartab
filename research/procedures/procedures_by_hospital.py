"""How many of the 50 launch procedures each H1 hospital publishes a price for (CPT/HCPCS merged)."""
import csv
from collections import Counter

with open("data/processed/procedures.csv", newline="") as f:
    procs = list(csv.DictReader(f))
with open("data/processed/h1_file_profile.csv", newline="") as f:
    hosp = {r["ccn"]: r["hospital"] for r in csv.DictReader(f)}
n = Counter(c for p in procs for c in p["hospital_ccns"].split(";"))
for ccn, name in hosp.items():
    print(f"{ccn}  {name:45s} {n.get(ccn, 0):>2d} of 50")
