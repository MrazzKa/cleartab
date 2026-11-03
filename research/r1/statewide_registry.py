"""R1: statewide list of Arizona hospitals with the financial assistance policy status of each.

Base list: CMS Hospital General Information for Arizona (data/raw/reference/cms_hospital_general_info_AZ.json,
retrieved 2026-10-12 by research/h2/fetch_context.py). Scope: acute care and critical access hospitals.
A nonprofit hospital must publish a financial assistance policy under IRS section 501(r); proprietary and
government hospitals are not bound by 501(r) but may have one.

Usage: python -m research.r1.statewide_registry   -> data/processed/r1_az_hospitals.csv
"""
import csv
import json
import re
from collections import Counter

from pipeline.common import PROCESSED, RAW, now_utc

SRC = RAW / "reference" / "cms_hospital_general_info_AZ.json"
SRC_URL = "https://data.cms.gov/provider-data/dataset/xubh-q36u"
# name patterns of the systems whose policies are in data/processed/assistance_policies.json
SYSTEMS = [
    ("Banner Health", r"\bBANNER\b"),
    ("HonorHealth", r"HONORHEALTH|HONOR HEALTH|JOHN C\.? LINCOLN"),
    ("Dignity Health (CommonSpirit)", r"ST\.? JOSEPH'?S HOSPITAL AND MEDICAL|CHANDLER REGIONAL|MERCY GILBERT|DIGNITY|"
                                      r"ARIZONA GENERAL HOSPITAL"),
    ("Tenet (Abrazo, Carondelet)", r"ABRAZO|CARONDELET|ST\.? MARY'S HOSPITAL|ST\.? JOSEPH'?S HOSPITAL$"),
    ("Northwest Healthcare", r"NORTHWEST MEDICAL CENTER|ORO VALLEY HOSPITAL"),
    ("TMC Health", r"TUCSON MEDICAL CENTER"),
    ("Mayo Clinic", r"\bMAYO\b"),
    ("Valleywise Health", r"VALLEYWISE|MARICOPA MEDICAL CENTER"),
]


def main() -> None:
    raw = json.loads(SRC.read_text())
    rows = raw["results"] if "results" in raw else next(iter(raw.values()))
    policies = {s["system"] for s in json.loads((PROCESSED / "assistance_policies.json").read_text())["systems"]}
    out = []
    for r in rows:
        if r["hospital_type"] not in ("Acute Care Hospitals", "Critical Access Hospitals"):
            continue
        name = r["facility_name"].upper()
        system = next((s for s, p in SYSTEMS if re.search(p, name)), "")
        own = r["hospital_ownership"]
        nonprofit = own.startswith("Voluntary non-profit")
        if system in policies:
            status = "collected"
        elif nonprofit:
            status = "to collect (501(r) requires a policy)"
        elif own.startswith(("Government", "Tribal")):
            status = "to check (government or tribal; 501(r) does not apply)"
        else:
            status = "to check (proprietary; 501(r) does not apply)"
        out.append({"ccn": r["facility_id"], "hospital": r["facility_name"], "city": r["citytown"],
                    "county": r["countyparish"], "type": r["hospital_type"], "ownership": own,
                    "nonprofit_501r": nonprofit, "policy_system": system, "policy_status": status,
                    "source_url": SRC_URL, "retrieved_at": now_utc()})
    out.sort(key=lambda x: (x["policy_status"], x["county"], x["hospital"]))
    with open(PROCESSED / "r1_az_hospitals.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "acute care and critical access hospitals")
    print(Counter(x["policy_status"] for x in out))
    print("nonprofit:", sum(x["nonprofit_501r"] for x in out), "; collected and nonprofit:",
          sum(x["nonprofit_501r"] and x["policy_status"] == "collected" for x in out))


if __name__ == "__main__":
    main()
