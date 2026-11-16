"""Medicare Physician Fee Schedule amounts for Arizona (plan items P3 Medicare yardstick and P12 global periods).

Source: CMS RVU26D (October 2026 release of the 2026 PFS relative value file),
https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26d , downloaded to
data/raw/reference/pfs/ (gitignored: the file carries AMA CPT descriptors, which are never copied here).

Arizona is one Medicare locality (MAC 03102, locality 00). CMS formula per code:
  amount = (work RVU x work GPCI + PE RVU x PE GPCI + MP RVU x MP GPCI) x conversion factor
with the non-facility PE RVU for services in an office and the facility PE RVU for services in a hospital. The
work GPCI is the one the file gives (the October 2026 file lists only the work GPCI with the 1.0 floor: 1.000 for
Arizona), and the conversion factor is the non-QP one (33.4009), which applies to most clinicians.

Output: data/processed/medicare_pfs_az_2026.csv with code, modifier, status, RVUs, global days, the Arizona
non-facility and facility amounts, source_url and retrieved_at. Codes with no Medicare amount (bundled, carrier
priced, not covered) are left out. Run: python -m pipeline.medicare_pfs
"""
import csv

from pipeline.common import PROCESSED, RAW

DIR = RAW / "reference" / "pfs"
RVU = DIR / "PPRRVU2026_Oct_nonQPP.csv"
GPCI = DIR / "GPCI2026.csv"
SOURCE_URL = "https://www.cms.gov/files/zip/rvu26d-updated-08-26-2026.zip"
OUT = PROCESSED / "medicare_pfs_az_2026.csv"
PRICED = {"A", "R", "T"}     # active, restricted, paid only if no other service that day (CMS status codes)
FIELDS = ["code", "modifier", "status", "work_rvu", "pe_rvu_nonfacility", "pe_rvu_facility", "mp_rvu",
          "global_days", "conversion_factor", "az_nonfacility", "az_facility", "locality", "source_url",
          "retrieved_at"]


def arizona_gpci() -> dict[str, float]:
    """Arizona GPCIs, columns found by their header (the October file keeps only the work GPCI with the floor)."""
    with open(GPCI, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    head = next(r for r in rows if r and r[0].startswith("Medicare Administrative Contractor"))
    col = {k: next(i for i, h in enumerate(head) if k in h) for k in ("PW GPCI", "PE GPCI", "MP GPCI")}
    for row in rows:
        if len(row) > 3 and row[1] == "AZ":
            return {"work": float(row[col["PW GPCI"]]), "pe": float(row[col["PE GPCI"]]),
                    "mp": float(row[col["MP GPCI"]]), "locality": f"{row[0]}-{row[2]}",
                    "work_gpci": head[col["PW GPCI"]]}
    raise SystemExit("Arizona not found in GPCI2026.csv")


def num(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return 0.0


def main() -> None:
    g = arizona_gpci()
    retrieved = (DIR / "rvu26d.retrieved_at").read_text().strip()
    out = []
    with open(RVU, newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = csv.reader(f)
        for row in rows:
            if row and row[0] == "HCPCS":
                break
        for r in rows:
            if len(r) < 26 or not r[0] or r[3] not in PRICED:
                continue
            work, pe_nf, pe_f, mp, cf = num(r[5]), num(r[6]), num(r[8]), num(r[10]), num(r[25])
            nf = (work * g["work"] + pe_nf * g["pe"] + mp * g["mp"]) * cf
            fa = (work * g["work"] + pe_f * g["pe"] + mp * g["mp"]) * cf
            if nf <= 0 and fa <= 0:
                continue
            out.append({"code": r[0], "modifier": r[1], "status": r[3], "work_rvu": work, "pe_rvu_nonfacility": pe_nf,
                        "pe_rvu_facility": pe_f, "mp_rvu": mp, "global_days": r[14], "conversion_factor": cf,
                        # "NA" in the non-facility indicator: CMS does not price the service in an office
                        "az_nonfacility": round(nf, 2) if r[7].strip() != "NA" else "",
                        "az_facility": round(fa, 2), "locality": g["locality"], "source_url": SOURCE_URL,
                        "retrieved_at": retrieved})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(f"{OUT}: {len(out)} priced codes, Arizona GPCI {g}")


if __name__ == "__main__":
    main()
