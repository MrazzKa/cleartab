"""Load data/processed/hospital_registry.csv into the hospitals table (upsert by CCN)."""
import csv
from urllib.parse import urlsplit

import psycopg

from pipeline.common import DATABASE_URL, REGISTRY_CSV

UPSERT = """
INSERT INTO hospitals (ccn, name, city, metro, county, health_system, website, phone, cms_hpt_url, mrf_url,
                       discovery_method, latitude, longitude, status, source_url, retrieved_at)
VALUES (%(ccn)s, %(name)s, %(city)s, %(metro)s, %(county)s, %(health_system)s, %(website)s, %(phone)s,
        %(cms_hpt_url)s, %(mrf_url)s, %(discovery_method)s, %(latitude)s, %(longitude)s, %(status)s,
        %(source_url)s, %(retrieved_at)s)
ON CONFLICT (ccn) DO UPDATE SET
    name = EXCLUDED.name, city = EXCLUDED.city, metro = EXCLUDED.metro, county = EXCLUDED.county,
    health_system = EXCLUDED.health_system, website = EXCLUDED.website,
    phone = COALESCE(EXCLUDED.phone, hospitals.phone),
    cms_hpt_url = EXCLUDED.cms_hpt_url, mrf_url = EXCLUDED.mrf_url,
    discovery_method = EXCLUDED.discovery_method,
    latitude = COALESCE(EXCLUDED.latitude, hospitals.latitude),
    longitude = COALESCE(EXCLUDED.longitude, hospitals.longitude),
    -- once the ETL has scored a hospital, its status comes from the ETL, not from the registry
    status = CASE WHEN hospitals.completeness_score IS NULL THEN EXCLUDED.status ELSE hospitals.status END,
    source_url = EXCLUDED.source_url,
    retrieved_at = CASE WHEN hospitals.completeness_score IS NULL THEN EXCLUDED.retrieved_at
                        ELSE hospitals.retrieved_at END
"""


def _url(value: str) -> str | None:
    value = (value or "").strip()
    return value if value.startswith("http") else None


def to_row(r: dict) -> dict:
    mrf = _url(r["mrf_url"])
    hpt = _url(r["cms_hpt_url"])
    listed = r["listed_in_cms_hpt"].strip()
    if mrf and listed == "Yes":
        discovery = "cms-hpt.txt"
    elif mrf:
        discovery = "price transparency page"
    else:
        discovery = "not found"
    blocked = r["robots_blocks_mrf"].startswith("Yes")
    status = "blocked" if blocked else ("published" if mrf else "unknown")
    website = f"{urlsplit(hpt).scheme}://{urlsplit(hpt).netloc}" if hpt else None
    lat = r.get("latitude") or None
    lon = r.get("longitude") or None
    return {
        "ccn": r["ccn"], "name": r["name"], "city": r["city"], "metro": r["metro"], "county": r["county"],
        "health_system": r["health_system"], "website": website, "phone": r.get("phone") or None,
        "cms_hpt_url": hpt, "mrf_url": mrf, "discovery_method": r.get("discovery_method") or discovery,
        "latitude": float(lat) if lat else None, "longitude": float(lon) if lon else None,
        "status": r.get("status") or status, "source_url": r["source_url"], "retrieved_at": r["retrieved_at"],
    }


def main() -> None:
    with open(REGISTRY_CSV, newline="") as f:
        rows = [to_row(r) for r in csv.DictReader(f)]
    geo_path = REGISTRY_CSV.parent / "hospital_geo.csv"
    if geo_path.exists():  # phone and coordinates from pipeline/geo.py
        with open(geo_path, newline="") as f:
            geo = {g["ccn"]: g for g in csv.DictReader(f)}
        for r in rows:
            g = geo.get(r["ccn"], {})
            r["phone"] = r["phone"] or g.get("phone") or None
            r["latitude"] = r["latitude"] or (float(g["lat"]) if g.get("lat") else None)
            r["longitude"] = r["longitude"] or (float(g["lon"]) if g.get("lon") else None)
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.executemany(UPSERT, rows)
    print(f"loaded {len(rows)} hospitals")


if __name__ == "__main__":
    main()
