"""R4: claim denials and appeals of Arizona Marketplace insurers, from the CMS Transparency in Coverage PUF.

Source: CMS Health Insurance Exchange Public Use Files, "Transparency in Coverage PUF"
(https://www.cms.gov/marketplace/resources/data/public-use-files). The PY2027 file holds 2025 claims and the PY2026
file 2024 claims ("The 2017-2027 Transparency PUF public data are derived from data from Plan Years 2015-2025",
CMS data disclaimer PY27). Issuers self-report; the files cover plans sold on HealthCare.gov (Arizona uses it), not
job-based, AHCCCS or Medicare plans. "**" marks cells CMS suppressed for small counts; they stay empty here.

Downloaded to data/raw/reference/tcpuf/ (python -m pipeline.tc_puf --download). Outputs:
- data/processed/r4_az_marketplace_denials.csv: one row per Arizona issuer and data year (in-network claims received
  and denied, denial rate, internal and external appeals of denied claims and how many were overturned).
- data/processed/r4_az_denial_reasons.csv: in-network denials by reason, summed over each issuer's Arizona plans
  (2025 data only; the 2024 file does not split reasons by network).
- data/processed/r4_us_marketplace_totals.csv: the same totals over all issuers with reported numbers, for context.
"""
import csv
import io
import sys
import time
import zipfile

import requests

from pipeline.common import PROCESSED, RAW, USER_AGENT

DIR = RAW / "reference" / "tcpuf"
FILES = {2027: "https://download.cms.gov/marketplace-puf/2027/transparency-in-coverage-puf.zip",
         2026: "https://download.cms.gov/marketplace-puf/2026/transparency-in-coverage-puf.zip"}
DATA_YEAR = {2027: 2025, 2026: 2024}
REASONS = {  # 2025 file, in-network plan-level columns
    "referral_required": "Plan_Number_Claims_Denied_Referral_Required_In_Network",
    "services_excluded": "Plan_Number_Claims_Denied_Services_Excluded_In_Network",
    "not_medically_necessary": "Plan_Number_Claims_Denied_Not_Medically_Necessary_Excluding_Behavioral_Health_In_Network",
    "not_medically_necessary_behavioral": ("Plan_Number_Claims_Denied_Not_Medically_Necessary_Behavioral_Health_Only_"
                                           "In_Network"),
    "benefit_limit": "Plan_Number_Claims_Denied_Due_To_Enrollee_Benefit_Limit_Reached_In_Network",
    "member_not_covered": "Plan_Number_Claims_Denied_Due_To_Member_Not_Covered_In_Network",
    "experimental_cosmetic": "Plan_Number_Claims_Denied_Due_To_Investigational_Experimental_Cosmetic_Procedure_In_Network",
    "administrative": "Plan_Number_Claims_Denied_Due_To_Administrative_Reason_In_Network",
    "other": "Plan_Number_Claims_Denied_Other_In_Network",
}


def download() -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    for py, url in FILES.items():
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        (DIR / f"tcpuf_py{py}.zip").write_bytes(r.content)
        time.sleep(1)
    (DIR / "retrieved_at").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + "\n")


def num(v):
    """A count, or None for suppressed ('**'), missing ('*', '***') and not applicable ('N/A') cells."""
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def rows(py: int) -> list[dict]:
    import openpyxl
    z = zipfile.ZipFile(DIR / f"tcpuf_py{py}.zip")
    name = next(n for n in z.namelist() if n.lower().endswith(".xlsx"))
    wb = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True, data_only=True)
    ws = next(s for s in wb.worksheets if s.title.endswith("Ind QHP"))
    it = ws.iter_rows(values_only=True)
    head = next(r for r in it if r and r[0] == "Individual/SHOP")
    return [dict(zip(head, r, strict=False)) for r in it if r and r[0]]


def col(row: dict, *names: str):
    for n in names:
        if n in row:
            return num(row[n])
    return None


def issuer_row(r: dict, py: int) -> dict:
    received = col(r, "Issuer_Claims_Received_In_Network")
    denied = col(r, "Issuer_Claims_Denied_In_Network")
    appeals = col(r, "Issuer_Internal_Appeals_Claims_Filed", "Issuer_Internal_Appeals_Filed")
    overturned = col(r, "Issuer_Number_Internal_Appeals_Claims_Overturned", "Issuer_Number_Internal_Appeals_Overturned")
    ext = col(r, "Issuer_External_Appeals_Claims_Filed", "Issuer_External_Appeals_Filed")
    ext_over = col(r, "Issuer_Number_External_Appeals_Claims_Overturned", "Issuer_Number_External_Appeals_Overturned")
    pct = lambda a, b: round(100 * a / b, 2) if a is not None and b else None  # noqa: E731
    return {"data_year": DATA_YEAR[py], "plan_year_file": py, "state": r["State"], "issuer_id": r["Issuer_ID"],
            "issuer": r["Issuer_Name"], "in_network_claims_received": received, "in_network_claims_denied": denied,
            "in_network_denial_rate_pct": pct(denied, received),
            "out_of_network_claims_received": col(r, "Issuer_Claims_Received_Out_Of_Network",
                                                  "Issuer_Claims_Received_Out_of_Network"),
            "out_of_network_claims_denied": col(r, "Issuer_Claims_Denied_Out_Of_Network",
                                                "Issuer_Claims_Denied_Out_of_Network"),
            "internal_appeals_filed": appeals, "internal_appeals_overturned": overturned,
            "internal_appeals_overturned_pct": pct(overturned, appeals),
            "appeals_per_100_in_network_denials": pct(appeals, denied),
            "external_appeals_filed": ext, "external_appeals_overturned": ext_over,
            "source_url": FILES[py]}


def main() -> None:
    if "--download" in sys.argv:
        download()
    retrieved = (DIR / "retrieved_at").read_text().strip()
    issuers, reasons, totals = [], [], []
    for py in FILES:
        data = rows(py)
        seen = {}
        for r in data:
            seen.setdefault((r["State"], r["Issuer_ID"]), r)
        all_issuers = [issuer_row(r, py) for r in seen.values()]
        for x in all_issuers:
            x["retrieved_at"] = retrieved
        issuers += [x for x in all_issuers if x["state"] == "AZ"]
        ok = [x for x in all_issuers if x["in_network_claims_received"] and x["in_network_claims_denied"] is not None]
        rec = sum(x["in_network_claims_received"] for x in ok)
        den = sum(x["in_network_claims_denied"] for x in ok)
        app = [x for x in ok if x["internal_appeals_filed"] is not None and x["internal_appeals_overturned"] is not None]
        totals.append({"data_year": DATA_YEAR[py], "scope": "all HealthCare.gov issuers with reported counts",
                       "issuers": len(ok), "in_network_claims_received": rec, "in_network_claims_denied": den,
                       "in_network_denial_rate_pct": round(100 * den / rec, 2),
                       "internal_appeals_filed": sum(x["internal_appeals_filed"] for x in app),
                       "internal_appeals_overturned": sum(x["internal_appeals_overturned"] for x in app),
                       "source_url": FILES[py], "retrieved_at": retrieved})
        if py == 2027:
            for (state, iid), first in seen.items():
                if state != "AZ":
                    continue
                plans = [r for r in data if r["State"] == "AZ" and r["Issuer_ID"] == iid]
                row = {"data_year": DATA_YEAR[py], "issuer_id": iid, "issuer": first["Issuer_Name"], "plans": len(plans)}
                for k, c in REASONS.items():
                    vals = [num(p.get(c)) for p in plans]
                    row[k] = sum(v for v in vals if v is not None) if any(v is not None for v in vals) else None
                    row[k + "_suppressed_plans"] = sum(1 for p in plans if str(p.get(c)).strip() == "**")
                row.update(source_url=FILES[py], retrieved_at=retrieved)
                reasons.append(row)
    for name, data in (("r4_az_marketplace_denials.csv", issuers), ("r4_az_denial_reasons.csv", reasons),
                       ("r4_us_marketplace_totals.csv", totals)):
        with open(PROCESSED / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
        print(PROCESSED / name, len(data), "rows")


if __name__ == "__main__":
    main()
