"""Pick 10 procedure-hospital pairs for the Section 4.2 phone accuracy check and pre-fill the CSV template.

Rule: 10 commonly shopped launch procedures in a fixed priority order (PRIORITY); each gets a different hospital
that publishes a cash price for it, preferring the metro with fewer pairs so far, then the lowest CCN.
Displayed figures come from GET /search (plan = cash) at the time of writing.
"""
import csv

from fastapi.testclient import TestClient

from api.main import app
from pipeline.common import PROCESSED, ROOT, now_utc

with open(PROCESSED / "procedures.csv", newline="") as f:
    procs = list(csv.DictReader(f))
PRIORITY = ["73721", "45378", "70450", "80053", "77067", "74177", "85025", "76700", "47562", "29881"]
pairs, used = [], set()
with TestClient(app) as c:
    cash = {}
    for code in PRIORITY:
        for zipc in ("85006", "85719"):
            for r in c.get("/search", params={"q": code, "plan": "cash", "zip": zipc}).json()["results"]:
                if r["cash"]["amount"] is not None:
                    cash.setdefault(code, {})[r["ccn"]] = r
    names = {p["code"]: p["plain_name"] for p in procs}
    for code in PRIORITY:
        per_metro = {m: sum(p["metro"] == m for p in pairs) for m in ("Tucson", "Phoenix")}
        options = sorted((r for ccn, r in cash.get(code, {}).items() if ccn not in used),
                         key=lambda r: (per_metro[r["metro"]], r["ccn"]))
        if not options:
            print("no hospital left with a cash price for", code)
            continue
        r = options[0]
        used.add(r["ccn"])
        pairs.append({"hospital": r["hospital"], "ccn": r["ccn"], "phone": r["phone"], "metro": r["metro"],
                      "code": code, "procedure": names[code], "displayed_price": r["cash"]["amount"],
                      "displayed_type": f"cash price (median of {r['cash']['items']} published items)",
                      "quoted_price": "", "what_was_included": "", "date": "", "notes": "",
                      "source_url": r["provenance"]["source_url"], "retrieved_at": now_utc()})
out = ROOT / "research" / "accuracy_check" / "phone_check.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pairs[0]))
    w.writeheader()
    w.writerows(pairs)
for p in pairs:
    print(p["metro"], p["hospital"][:40], p["code"], p["procedure"], p["displayed_price"])
