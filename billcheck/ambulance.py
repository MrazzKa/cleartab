"""Arizona ground ambulance rates set by ADHS (A.R.S. 36-2232, 36-2239; A.A.C. R9-25 Article 11).

ADHS publishes the "Arizona Ground Ambulance Service Rate Schedule": for each certificate of necessity (CON), the
approved base rates for advanced life support (ALS), basic life support (BLS) and, for some, critical care (CCS),
the rate per mile, and whether disposable supplies may be charged separately. The standby and subscription columns
are not kept: when one of them is empty the PDF text does not show which, so they cannot be read reliably.

Usage: python -m billcheck.ambulance   -> data/processed/az_ground_ambulance_rates.csv (from the downloaded PDF)
"""
import csv
import re
from functools import lru_cache

from pipeline.common import PROCESSED, RAW, now_utc
from pipeline.http import PoliteSession

URL = ("https://www.azdhs.gov/documents/preparedness/emergency-medical-services-trauma-system/ambulance/ground/"
       "rates/ground-ambulance-rate-schedule.pdf")
PDF = RAW / "reference" / "ambulance" / "ground-ambulance-rate-schedule.pdf"
CSV = PROCESSED / "az_ground_ambulance_rates.csv"
TYPES = {"fd": "fire district", "fp": "for profit", "np": "nonprofit", "cnty": "county", "muni": "municipality",
         "hosp": "hospital", "trbl": "tribal"}
HEAD = re.compile(r"^(\d+)\s+(fd|fp|np|cnty|muni|hosp|trbl)\b\s*(.*)$")
VAL = re.compile(r"\(\s*([\d,]+\.\d\d)\s*\)|\bNONE\b")
TAIL = re.compile(r"\s(\S{5})\s+(\d\d/\d\d/\d\d)\s+(Yes|No|only Oxygen)\s*$")


def parse(text: str) -> list[dict]:
    rows, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        m = HEAD.match(line)
        if m:
            cur = {"con": m.group(1), "type": TYPES[m.group(2)], "name": ""}
            line = m.group(3)
        if cur is None:
            continue
        tail = TAIL.search(" " + line)
        vals = [None if v.group(0) == "NONE" else float(v.group(1).replace(",", "")) for v in VAL.finditer(line)]
        name_part = VAL.split(line)[0] if vals else line
        if not vals:
            cur["name"] = (cur["name"] + " " + line).strip()
            continue
        cur["name"] = (cur["name"] + " " + name_part).strip()
        mi = next(i for i, v in enumerate(vals) if v is not None and v < 100)
        base = vals[:mi]
        rows.append({
            "con": cur["con"], "entity": re.sub(r"\s+", " ", cur["name"]).strip(" *^"),
            "rate_group": "Phoenix" if "***" in cur["name"] else "Tucson" if "^^^" in cur["name"] else "",
            "entity_type": cur["type"], "als": base[0], "bls": base[1] if len(base) > 1 else None,
            "ccs": base[2] if len(base) > 2 else None, "mileage": vals[mi],
            "control_no": tail.group(1) if tail else "", "effective": tail.group(2) if tail else "",
            "supplies_separate": tail.group(3) if tail else ""})
        cur = None
    for r in rows:
        r["entity"] = r["entity"].replace("***", "").replace("^^^", "").strip()
    return rows


def build() -> list[dict]:
    if not PDF.exists():
        PDF.parent.mkdir(parents=True, exist_ok=True)
        r = PoliteSession().request("GET", URL)
        r.raise_for_status()
        PDF.write_bytes(r.content)
    import pypdf
    text = "\n".join(p.extract_text() for p in pypdf.PdfReader(PDF).pages)
    prepared = re.search(r"Prepared:\s*([A-Za-z]+ \d+, \d{4})", text)
    rows = parse(text)
    stamp = now_utc()
    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[*rows[0], "schedule_prepared", "source_url", "retrieved_at"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "schedule_prepared": prepared.group(1) if prepared else "", "source_url": URL,
                        "retrieved_at": stamp})
    return rows


@lru_cache(maxsize=1)
def rates() -> list[dict]:
    if not CSV.exists():
        return []
    with open(CSV, newline="") as f:
        out = []
        for r in csv.DictReader(f):
            for k in ("als", "bls", "ccs", "mileage"):
                r[k] = float(r[k]) if r[k] else None
            out.append(r)
        return out


def find(con: str) -> dict | None:
    return next((r for r in rates() if r["con"] == str(con)), None)


if __name__ == "__main__":
    rs = build()
    print(len(rs), "ambulance services")
    for r in rs[:3] + [x for x in rs if "Phoenix" in x["entity"] or "Tucson" in x["entity"]][:4]:
        print(r)
