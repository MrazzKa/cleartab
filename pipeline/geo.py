"""Reference geography for Feature 2 distances and Feature 6 phone numbers.

1. ZIP centroids: 2020 Census ZCTA internal points (INTPTLAT, INTPTLON) for Arizona ZCTAs (85xxx, 86xxx) from
   the Census TIGERweb REST service, layer "2020 Census ZIP Code Tabulation Areas". These are the same internal
   points the Census ZCTA gazetteer file lists; the gazetteer itself is on www2.census.gov, whose robots.txt
   (read strictly per RFC 9309) disallows all agents not listed, so it was not fetched.
2. Hospital address and phone: CMS Hospital General Information (data.cms.gov dataset xubh-q36u), the same
   base list as the registry.
3. Hospital coordinates: U.S. Census Geocoder, one-line address, benchmark Public_AR_Current.
Outputs (committed, small): data/processed/az_zcta_centroids.csv, data/processed/hospital_geo.csv.
"""
import csv
from urllib.parse import quote_plus

from pipeline.common import PROCESSED, REGISTRY_CSV, now_utc
from pipeline.http import PoliteSession

ZCTA: dict[str, tuple[float, float]] = {}

TIGER = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/1/query"
         "?where={where}&outFields=ZCTA5,INTPTLAT,INTPTLON&returnGeometry=false&f=json"
         "&resultOffset={offset}&resultRecordCount=1000")
CMS = ("https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0?conditions[0][property]=state"
       "&conditions[0][value]=AZ&conditions[0][operator]=%3D&limit=500")
GEOCODER = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address={addr}"
            "&benchmark=Public_AR_Current&format=json")


def zcta(s: PoliteSession) -> int:
    rows, offset = [], 0
    where = quote_plus("ZCTA5 LIKE '85%' OR ZCTA5 LIKE '86%'")
    while True:
        url = TIGER.format(where=where, offset=offset)
        feats = s.get(url).json().get("features", [])
        for f in feats:
            a = f["attributes"]
            rows.append({"zip": a["ZCTA5"], "lat": float(a["INTPTLAT"]), "lon": float(a["INTPTLON"]),
                         "source_url": url, "retrieved_at": now_utc()})
        if len(feats) < 1000:
            break
        offset += 1000
    with open(PROCESSED / "az_zcta_centroids.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["zip"]))
    return len(rows)


def hospitals(s: PoliteSession) -> list[dict]:
    global ZCTA
    with open(PROCESSED / "az_zcta_centroids.csv", newline="") as f:
        ZCTA = {r["zip"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)}
    cms = {r["facility_id"]: r for r in s.get(CMS).json()["results"]}
    with open(REGISTRY_CSV, newline="") as f:
        reg = list(csv.DictReader(f))
    out = []
    for r in reg:
        c = cms.get(r["ccn"])
        row = {"ccn": r["ccn"], "address": "", "city": "", "zip": "", "phone": "", "lat": "", "lon": "",
               "geocode_match": "", "cms_source_url": CMS, "geocoder_source_url": "", "retrieved_at": now_utc()}
        if not c:
            row["geocode_match"] = "not found in CMS Hospital General Information"
            out.append(row)
            continue
        row.update(address=c["address"], city=c["citytown"], zip=c["zip_code"][:5], phone=c["telephone_number"])
        addr = f"{c['address']}, {c['citytown']}, AZ {c['zip_code'][:5]}"
        url = GEOCODER.format(addr=quote_plus(addr))
        matches = s.get(url, timeout=60).json().get("result", {}).get("addressMatches", [])
        row["geocoder_source_url"] = url
        if matches:
            row.update(lat=matches[0]["coordinates"]["y"], lon=matches[0]["coordinates"]["x"],
                       geocode_match=matches[0]["matchedAddress"])
        else:
            z = ZCTA.get(row["zip"])
            if z:
                row.update(lat=z[0], lon=z[1], geocode_match="no geocoder match; ZIP centroid used")
            else:
                row["geocode_match"] = "no geocoder match; ZIP not in AZ ZCTA list"
        out.append(row)
        print(r["ccn"], row["geocode_match"][:60], flush=True)
    with open(PROCESSED / "hospital_geo.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    return out


if __name__ == "__main__":
    import sys
    session = PoliteSession()
    if "--hospitals-only" not in sys.argv:
        print("ZCTAs:", zcta(session))
    hospitals(session)
