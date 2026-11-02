"""Public hospital-level and ZIP-level context for the exploratory part of the H2 follow-up (descriptive only).

Usage: python -m research.h2.fetch_context
Writes data/processed/hospital_context.csv (one row per H1 sample hospital).

Sources (each value keeps its own source URL in the CSV):
- CMS Hospital General Information (dataset xubh-q36u): hospital_type, hospital_ownership.
- CMS Provider of Services file, Hospital & Non-Hospital Facilities, release 2025-04-02 (dataset
  4bdd6342-510f-42fd-9a75-3068e84d80ec): CRTFD_BED_CNT (certified beds).
- Census ACS 5-year, ZCTA of the hospital's address: B19013_001E (median household income) and
  S2701_C05_001E (percent uninsured, civilian noninstitutionalized population). The Census API now requires a
  key; set CENSUS_API_KEY in .env (free: https://api.census.gov/data/key_signup.html). Without a key these columns
  stay empty and the note says why.
"""
import csv
import os

from pipeline.common import PROCESSED, now_utc
from pipeline.http import PoliteSession

HGI = ("https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0?conditions[0][property]=state"
       "&conditions[0][value]=AZ&conditions[0][operator]=%3D&limit=500")
POS = ("https://data.cms.gov/data-api/v1/dataset/4bdd6342-510f-42fd-9a75-3068e84d80ec/data"
       "?filter[STATE_CD]=AZ&filter[PRVDR_CTGRY_CD]=01&size=5000")
ACS_YEAR = "2024"
ACS = "https://api.census.gov/data/{y}/acs/acs5{sub}?get={var}&for=zip%20code%20tabulation%20area:{zips}"


def main() -> None:
    with open(PROCESSED / "h1_file_profile.csv", newline="") as f:
        prof = {r["ccn"]: r for r in csv.DictReader(f)}
    with open(PROCESSED / "hospital_geo.csv", newline="") as f:
        geo = {r["ccn"]: r for r in csv.DictReader(f)}
    s = PoliteSession()
    hgi = {r["facility_id"]: r for r in s.get(HGI).json()["results"]}
    pos_rows = s.get(POS).json()
    pos = {r["PRVDR_NUM"]: r for r in pos_rows}
    zips = sorted({geo[c]["zip"][:5] for c in prof})
    acs: dict[str, dict] = {z: {} for z in zips}
    key = os.environ.get("CENSUS_API_KEY", "")
    acs_note = ""
    if key:
        for var, sub, col in (("B19013_001E", "", "median_household_income"),
                              ("S2701_C05_001E", "/subject", "pct_uninsured")):
            url = ACS.format(y=ACS_YEAR, sub=sub, var=var, zips=",".join(zips))
            r = s.get(url + f"&key={key}")
            if r.status_code != 200:
                acs_note = f"ACS {var}: HTTP {r.status_code}"
                continue
            head, *rows = r.json()
            for row in rows:
                d = dict(zip(head, row, strict=True))
                v = d[var]
                # Census marks suppressed or unavailable estimates with large negative codes
                acs[d["zip code tabulation area"]][col] = v if v and not v.startswith("-") else ""
                acs[d["zip code tabulation area"]][col + "_source_url"] = url
    else:
        acs_note = ("not obtained: api.census.gov requires a key (HTTP 302 to missing_key.html on 2026-10-16); "
                    "set CENSUS_API_KEY in .env and re-run")
    out = []
    for ccn, p in prof.items():
        h, b, z = hgi.get(ccn, {}), pos.get(ccn, {}), geo[ccn]["zip"][:5]
        out.append({
            "ccn": ccn, "hospital": p["hospital"], "health_system": p["health_system"], "metro": p["metro"],
            "zip": z, "hospital_type": h.get("hospital_type", "not found"),
            "hospital_ownership": h.get("hospital_ownership", "not found"),
            "certified_beds": b.get("CRTFD_BED_CNT", "") or "not found",
            "median_household_income": acs[z].get("median_household_income", ""),
            "pct_uninsured": acs[z].get("pct_uninsured", ""),
            "acs_note": acs_note, "hgi_source_url": HGI, "pos_source_url": POS,
            "acs_source_url": acs[z].get("median_household_income_source_url", ""),
            "source_url": HGI, "retrieved_at": now_utc()})
    with open(PROCESSED / "hospital_context.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r["ccn"], r["hospital"][:35], r["hospital_ownership"], r["certified_beds"], r["median_household_income"],
              r["pct_uninsured"])
    print(acs_note)


if __name__ == "__main__":
    main()
