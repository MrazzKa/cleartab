"""Add hospitals that the ETL has profiled (data/processed/etl_cache.json) to the H1 CSVs without re-parsing
the raw file. Used for Mayo (21.5 GB): the profile and validator result come from the ETL cache; the 2026
element counts and payer strings are recomputed from the normalized parquet.

Usage: PYTHONPATH=. python research/h1/backfill_from_cache.py CCN [CCN ...]
"""
import csv
import json
import sys

import polars as pl

from pipeline.common import PROCESSED, RAW, now_utc
from pipeline.parsers.cms import ALLOWED_KEYS

cache = json.loads((PROCESSED / "etl_cache.json").read_text())


def rewrite(path, rows, key_ccn, ccn):
    with open(path, newline="") as f:
        old = [r for r in csv.DictReader(f) if r[key_ccn] != ccn]
    cols = list(dict.fromkeys([*(old[0].keys() if old else []), *(rows[0].keys() if rows else [])]))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(old + rows)


for ccn in sys.argv[1:]:
    entry = next(v for v in cache.values() if v.get("profile", {}).get("ccn") == ccn)
    prof, val = entry["profile"], entry["validator"]
    lf = pl.scan_parquet(RAW / "normalized" / f"{ccn}.parquet")
    payers = (lf.filter(pl.col("payer_name").is_not_null()).group_by("payer_name", "plan_name")
              .agg(pl.len().alias("n")).collect(engine="streaming"))
    allowed = dict(lf.filter(pl.col("price_type").str.starts_with("allowed")).group_by("price_type").len()
                   .collect(engine="streaming").iter_rows())
    url, ts = prof["source_url"], prof["retrieved_at"]
    rewrite(PROCESSED / "h1_validator.csv", [val], "ccn", ccn)
    rewrite(PROCESSED / "h1_file_profile.csv", [prof], "ccn", ccn)
    status = {"org_npi": (prof["org_npi"], "present" if prof["org_npi"] else "missing"),
              "attester_name": (prof["attester_name"], "present" if prof["attester_name"] else "missing"),
              "attestation_statement": (prof["attestation_present"],
                                        "present" if prof["attestation_present"] else "missing")}
    elems = []
    for e in ("org_npi", "attester_name", "attestation_statement", *ALLOWED_KEYS):
        if e in status:
            v, st = status[e]
        else:
            v = allowed.get(ALLOWED_KEYS[e], 0)
            na = "not applicable (no percent or algorithm rates)"
            st = "present" if v else ("missing" if prof["pct_algo_records"] else na)
        elems.append({"ccn": ccn, "hospital": prof["hospital"], "element": e, "status": st, "value_or_count": v,
                      "source_url": url, "retrieved_at": ts})
    rewrite(PROCESSED / "h1_required_elements.csv", elems, "ccn", ccn)
    rewrite(PROCESSED / "payer_strings.csv",
            [{"raw_payer": p, "raw_plan": q or "", "hospital": prof["hospital"], "ccn": ccn, "row_count": n,
              "source_url": url, "retrieved_at": ts} for p, q, n in payers.iter_rows()], "ccn", ccn)
    print(ccn, "profile, validator, 2026 elements and", payers.height, "payer strings added", now_utc())
