"""Download the CMS NCCI medically unlikely edit (MUE) tables into data/raw/reference/ (gitignored).

Usage: python -m billcheck.fetch_reference [--quarter 2026-q4]
One polite request per file (robots.txt checked, ClearTab user agent). The PTP tables need the AMA license
click-through on cms.gov and are downloaded by hand (MANUAL_DOWNLOADS.md).
"""
import argparse

from billcheck.reference import REFERENCE
from pipeline.http import PoliteSession

BASE = "https://www.cms.gov/files/zip/"
TABLES = ["medicare-ncci-{q}-facility-outpatient-hospital-services-mue-table.zip",
          "medicare-ncci-{q}-practitioner-services-mue-table.zip"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarter", default="2026-q4")
    args = ap.parse_args()
    REFERENCE.mkdir(parents=True, exist_ok=True)
    s = PoliteSession()
    for t in TABLES:
        name = t.format(q=args.quarter)
        r = s.request("GET", BASE + name)
        r.raise_for_status()
        (REFERENCE / name).write_bytes(r.content)
        print(name, len(r.content), "bytes")


if __name__ == "__main__":
    main()
