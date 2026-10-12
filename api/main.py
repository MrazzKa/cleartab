"""ClearTab API (Feature 1 search, Feature 2 comparison data, Feature 5 provenance, Feature 6 call summary data).

GET /search?q=&plan=&zip=   best-matching launch procedure, up to 10 hospitals sorted by the applicable price
GET /procedures/suggest?q=  autocomplete over launch procedures
GET /plans                  the plan choices (canonical insurers, plus "cash")

Matching is deterministic: PostgreSQL full-text search plus pg_trgm similarity. No ML.
Privacy (proposal 6.1): request logs keep the path only; the query string (procedure, plan, ZIP) is never logged.
Figures per hospital when a file lists several line items for the same code: the median of those items, with
the count and the min-max shown, so nothing is hidden.
"""
import logging
import math
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from pipeline.common import DATABASE_URL, PROCESSED

log = logging.getLogger("cleartab")
pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=int(os.environ.get("DB_POOL", "8")), open=False,
                      kwargs={"row_factory": dict_row})
ZCTA: dict[str, tuple[float, float]] = {}
CASH_WORDS = {"", "cash", "none", "no insurance", "uninsured", "self pay", "self-pay"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import csv
    with open(PROCESSED / "az_zcta_centroids.csv", newline="") as f:
        ZCTA.update({r["zip"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)})
    pool.open()
    yield
    pool.close()


app = FastAPI(title="ClearTab API", version="0.1", lifespan=lifespan)


@app.middleware("http")
async def path_only_log(request: Request, call_next):
    response = await call_next(request)
    log.info("%s %s %s", request.method, request.url.path, response.status_code)  # no query string
    return response


def miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


MATCH_SQL = """
SELECT id, code, code_type, plain_name, description, category, setting,
       GREATEST(similarity(plain_name, %(q)s), similarity(coalesce(synonyms, ''), %(q)s),
                CASE WHEN code = %(q)s THEN 1 ELSE 0 END,
                ts_rank(search_tsv, websearch_to_tsquery('english', %(q)s))) AS score
FROM procedures
WHERE is_launch AND (code = %(q)s OR search_tsv @@ websearch_to_tsquery('english', %(q)s)
                     OR plain_name %% %(q)s OR synonyms %% %(q)s OR word_similarity(%(q)s, synonyms) > 0.5)
ORDER BY score DESC, plain_name
LIMIT %(n)s
"""

# One row per hospital for the procedure: gross, cash, the plan's fixed-dollar negotiated rates, and the
# allowed-amount range for percent / algorithm rates. Dropped rows (flag dropped:*) are excluded.
PRICE_SQL = """
WITH p AS (
  SELECT pr.*, py.canonical_name
  FROM prices pr LEFT JOIN payers py ON py.id = pr.payer_id
  WHERE pr.procedure_id = %(pid)s AND pr.setting IN ('outpatient', 'both')
    AND NOT EXISTS (SELECT 1 FROM unnest(pr.flags) f WHERE f LIKE 'dropped:%%')
)
SELECT h.id, h.ccn, h.name, h.city, h.metro, h.phone, h.latitude, h.longitude, h.completeness_score, h.status,
  sf.url AS source_url, sf.retrieved_at AS downloaded_at, sf.file_last_updated, sf.schema_version,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'gross') AS gross,
  count(*) FILTER (WHERE p.price_type = 'gross') AS gross_n,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'cash') AS cash,
  count(*) FILTER (WHERE p.price_type = 'cash') AS cash_n,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar'
      AND p.methodology = 'fixed dollar' AND p.canonical_name = %(plan)s) AS neg_median,
  min(p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
      AND p.canonical_name = %(plan)s) AS neg_min,
  max(p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
      AND p.canonical_name = %(plan)s) AS neg_max,
  count(*) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
      AND p.canonical_name = %(plan)s) AS neg_n,
  array_agg(DISTINCT p.methodology) FILTER (WHERE p.canonical_name = %(plan)s
      AND p.price_type LIKE 'negotiated%%') AS plan_methods,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'allowed_median'
      AND p.canonical_name = %(plan)s) AS allowed_median,
  min(p.amount) FILTER (WHERE p.price_type = 'allowed_p10' AND p.canonical_name = %(plan)s) AS allowed_p10,
  max(p.amount) FILTER (WHERE p.price_type = 'allowed_p90' AND p.canonical_name = %(plan)s) AS allowed_p90,
  count(*) FILTER (WHERE p.canonical_name = %(plan)s) AS plan_rows,
  count(*) FILTER (WHERE p.price_type LIKE 'negotiated%%') AS any_negotiated
FROM p
JOIN hospitals h ON h.id = p.hospital_id
JOIN source_files sf ON sf.id = p.source_file_id
GROUP BY h.id, sf.id
"""

NOT_PUBLISHED_SQL = """
SELECT h.ccn, h.name, h.city, h.metro, h.phone, h.latitude, h.longitude, h.status, h.completeness_score,
       coalesce(h.mrf_url, h.cms_hpt_url) AS url_checked, h.retrieved_at AS checked_at
FROM hospitals h
WHERE h.id <> ALL(%(ids)s) AND (%(metro)s::text IS NULL OR h.metro = %(metro)s)
ORDER BY h.name
"""


def money(x) -> float | None:
    return None if x is None else round(float(x), 2)


def completeness_label(score, status) -> str:
    if score is None:
        return "not checked yet"
    if status == "not published" or float(score) == 0:
        return "not published"
    return "complete" if float(score) >= 80 else "partial"


@app.get("/plans")
def plans():
    with pool.connection() as conn:
        names = [r["canonical_name"] for r in conn.execute(
            "SELECT canonical_name FROM payers WHERE plan_type IS NULL AND canonical_name <> 'other' ORDER BY 1")]
    return {"plans": ["cash"] + names}


@app.get("/procedures/suggest")
def suggest(q: str = Query(..., min_length=2, max_length=80)):
    with pool.connection() as conn:
        rows = conn.execute(MATCH_SQL, {"q": q.strip(), "n": 8}).fetchall()
    return {"suggestions": [{"code": r["code"], "plain_name": r["plain_name"], "category": r["category"]}
                            for r in rows]}


@app.get("/search")
def search(q: str = Query(..., min_length=2, max_length=80), plan: str = "", zip: str = Query("", max_length=10)):
    plan_key = plan.strip()
    is_cash = plan_key.casefold() in CASH_WORDS
    origin = ZCTA.get(zip.strip()[:5]) if zip else None
    with pool.connection() as conn:
        match = conn.execute(MATCH_SQL, {"q": q.strip(), "n": 1}).fetchone()
        if not match:
            raise HTTPException(404, "No launch procedure matches this search.")
        if not is_cash:
            known = conn.execute("SELECT 1 FROM payers WHERE canonical_name = %s", (plan_key,)).fetchone()
            if not known:
                raise HTTPException(422, "Unknown plan. Use GET /plans for the list, or 'cash'.")
        rows = conn.execute(PRICE_SQL, {"pid": match["id"], "plan": plan_key}).fetchall()
        metro = None
        if origin:
            nearest = min(rows, key=lambda r: miles(origin, (r["latitude"], r["longitude"])), default=None)
            metro = nearest["metro"] if nearest else None
        all_ids = [r["id"] for r in rows]
        if metro:  # results stay inside the user's metro area (Tucson or Phoenix)
            rows = [r for r in rows if r["metro"] == metro]
        missing = conn.execute(NOT_PUBLISHED_SQL, {"ids": all_ids, "metro": metro}).fetchall()

    results = []
    for r in rows:
        dist = round(miles(origin, (r["latitude"], r["longitude"])), 1) if origin and r["latitude"] else None
        negotiated = None
        if not is_cash:
            if r["neg_n"]:
                negotiated = {"kind": "negotiated rate", "methodology": "fixed dollar", "median": money(r["neg_median"]),
                              "min": money(r["neg_min"]), "max": money(r["neg_max"]), "rates_count": r["neg_n"]}
            elif r["allowed_median"] is not None:
                negotiated = {"kind": "allowed amount estimate", "methodology": ", ".join(
                    m for m in (r["plan_methods"] or []) if m and m != "fixed dollar") or "percent of charges",
                    "median": money(r["allowed_median"]), "p10": money(r["allowed_p10"]),
                    "p90": money(r["allowed_p90"])}
            elif r["plan_rows"]:
                negotiated = {"kind": "not a dollar amount", "methodology": ", ".join(
                    m for m in (r["plan_methods"] or []) if m) or "unlabelled", "median": None}
            else:
                negotiated = {"kind": "plan not matched", "median": None}
        applicable = money(r["cash"]) if is_cash else (negotiated or {}).get("median")
        results.append({
            "ccn": r["ccn"], "hospital": r["name"], "city": r["city"], "metro": r["metro"], "phone": r["phone"],
            "distance_miles": dist, "distance_note": "straight line from the ZIP code centre" if dist is not None else None,
            "gross": {"amount": money(r["gross"]), "methodology": "gross charge (list price)", "items": r["gross_n"]},
            "cash": {"amount": money(r["cash"]), "methodology": "discounted cash price", "items": r["cash_n"]},
            "negotiated": negotiated, "applicable_price": applicable,
            "completeness": {"score": float(r["completeness_score"]) if r["completeness_score"] is not None else None,
                             "label": completeness_label(r["completeness_score"], r["status"])},
            "provenance": {"source_url": r["source_url"], "downloaded_at": r["downloaded_at"].isoformat(),
                           "file_last_updated": r["file_last_updated"].isoformat() if r["file_last_updated"] else None,
                           "file_version": r["schema_version"]},
        })
    results.sort(key=lambda x: (x["applicable_price"] is None, x["applicable_price"] or 0,
                                x["distance_miles"] if x["distance_miles"] is not None else 1e9))
    return {
        "procedure": {k: match[k] for k in ("code", "code_type", "plain_name", "description", "category")},
        "plan": "cash" if is_cash else plan_key, "zip": zip[:5] or None, "metro": metro,
        "sort": "lowest applicable price first; no price last",
        "explainer": EXPLAINER,
        "results": results[:10],
        "not_published": [{"hospital": m["name"], "city": m["city"],
                           "status": completeness_label(m["completeness_score"], m["status"])
                           if m["completeness_score"] is not None else ("blocked by robots.txt or site"
                                                                        if m["status"] == "blocked" else "not checked yet"),
                           "url_checked": m["url_checked"],
                           "checked_at": m["checked_at"].isoformat() if m["checked_at"] else None}
                          for m in missing],
    }


EXPLAINER = ("These are prices the hospital published for its own part of the care, called the facility charge. "
             "They do not include the doctor's fee, which is billed separately. The gross charge is the list price "
             "that almost no one pays. The cash price is what the hospital says it charges people who pay for "
             "themselves. A negotiated rate is the amount a hospital agreed with an insurance plan; what you pay "
             "depends on your deductible and coinsurance. Your final bill can be different. Call the hospital to "
             "confirm before your visit.")
