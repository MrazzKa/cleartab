"""Phase 2 steps 5-9: parse every downloaded H1 file, profile it and score completeness (Feature 5).

Outputs
  data/raw/normalized/<ccn>.parquet       normalized long table (derived from raw files, not committed)
  data/processed/h1_file_profile.csv      one row per hospital in the sample
  data/processed/h1_required_elements.csv one row per hospital x CY 2026 element
  data/processed/payer_strings.csv        raw_payer, raw_plan, hospital, row_count (input to Phase 4)

Completeness score (proposal Table 10 names 5 components but no weights; equal weights of 20 are used):
  C1 file found          20 if a CMS-template CSV or JSON file was downloaded and parsed, else 0
  C2 schema valid        20 if the CMS validator reports the file valid (0 errors), else 0
  C3 coded rows          20 x share of normalized rows whose code is CPT, HCPCS or MS-DRG
  C4 dollar or allowed   20 x share of priced records carrying a dollar figure: gross and cash records,
                         negotiated records with a dollar amount, and percent or algorithm records that
                         carry a median allowed amount, over gross + cash + all negotiated records
  C5 2026 elements       20 x (CY 2026 elements present) / (elements applicable). The 4 allowed-amount elements
                         are not applicable when a file has no percent or algorithm negotiated rates.
  score = C1 + C2 + C3 + C4 + C5, 0-100. Labels: complete >= 80, partial 1-79, not published = no usable file.
A hospital "yields usable coded rows" (H1) when its file parses and has priced rows for at least
100 distinct CPT, HCPCS or MS-DRG codes.
"""
import csv
import pathlib
import sys
from collections import Counter

import pyarrow as pa
import pyarrow.parquet as pq

from pipeline.common import PROCESSED, RAW, REGISTRY_CSV, now_utc
from pipeline.download import load_manifest
from pipeline.h1_download import SAMPLE
from pipeline.parsers.cms import ELEMENTS_2026, USABLE_CODE_TYPES, parse_file

NORM = RAW / "normalized"
USABLE_MIN_CODES = 100
SCHEMA = pa.schema([
    ("ccn", pa.string()), ("description", pa.string()), ("code", pa.string()), ("code_type", pa.string()),
    ("setting", pa.string()), ("billing_class", pa.string()), ("modifiers", pa.string()),
    ("usable_code", pa.bool_()), ("payer_name", pa.string()), ("plan_name", pa.string()),
    ("price_type", pa.string()), ("amount", pa.float64()), ("percentage", pa.float64()),
    ("algorithm", pa.string()), ("methodology", pa.string()), ("flags", pa.string()),
])
BATCH = 200_000


def write_parquet(ccn: str, rows) -> Counter:
    """Stream rows to parquet in batches; return counts by price_type and priced usable codes."""
    NORM.mkdir(parents=True, exist_ok=True)
    counts: Counter = Counter()
    priced_codes: set = set()
    buf: list[dict] = []
    with pq.ParquetWriter(NORM / f"{ccn}.parquet", SCHEMA, compression="zstd") as w:
        for r in rows:
            counts[r["price_type"]] += 1
            if r["usable_code"] and (r["amount"] is not None or r["percentage"] is not None):
                priced_codes.add((r["code_type"], r["code"]))
            buf.append(r)
            if len(buf) >= BATCH:
                w.write_table(pa.Table.from_pylist(buf, schema=SCHEMA))
                buf = []
        if buf:
            w.write_table(pa.Table.from_pylist(buf, schema=SCHEMA))
    counts["_priced_codes"] = len(priced_codes)
    return counts


def score(found: bool, valid: bool, prof, counts: Counter) -> dict:
    if not found:
        return {"c1_file_found": 0, "c2_schema_valid": 0, "c3_coded_rows": 0, "c4_dollar_or_allowed": 0,
                "c5_2026_elements": 0, "completeness_score": 0, "completeness_label": "not published"}
    neg_total = prof.negotiated["dollar"] + prof.negotiated["percent"] + prof.negotiated["algorithm"]
    den = counts["gross"] + counts["cash"] + neg_total
    num = counts["gross"] + counts["cash"] + prof.negotiated["dollar"] + prof.pct_algo_with_median
    statuses = [prof.element_status(e) for e in ELEMENTS_2026]
    applicable = [x for x in statuses if not x.startswith("not applicable")]
    present = sum(x == "present" for x in applicable)
    c = {"c1_file_found": 20, "c2_schema_valid": 20 if valid else 0,
         "c3_coded_rows": round(20 * prof.usable_rows / prof.rows, 1) if prof.rows else 0,
         "c4_dollar_or_allowed": round(20 * num / den, 1) if den else 0,
         "c5_2026_elements": round(20 * present / len(applicable), 1) if applicable else 0}
    total = round(sum(c.values()), 1)
    return {**c, "completeness_score": total, "completeness_label": "complete" if total >= 80 else "partial"}


def main() -> None:
    only = set(sys.argv[1:])
    with open(REGISTRY_CSV, newline="") as f:
        reg = {r["ccn"]: r for r in csv.DictReader(f)}
    validator = {}
    vpath = PROCESSED / "h1_validator.csv"
    if vpath.exists():
        with open(vpath, newline="") as f:
            validator = {r["ccn"]: r for r in csv.DictReader(f)}
    manifest = {ccn: m for (ccn, _), m in load_manifest().items()}

    prof_path, elem_path, payer_path = (PROCESSED / n for n in
                                        ("h1_file_profile.csv", "h1_required_elements.csv", "payer_strings.csv"))
    old_profiles, old_elems, old_payers = {}, {}, {}
    if only:  # partial re-run: keep other hospitals' rows
        for path, store, key in ((prof_path, old_profiles, "ccn"), (elem_path, old_elems, "ccn"),
                                 (payer_path, old_payers, "ccn")):
            if path.exists():
                with open(path, newline="") as f:
                    for r in csv.DictReader(f):
                        store.setdefault(r[key], []).append(r)

    profiles, elements, payers = [], [], []
    for ccn in SAMPLE:
        if only and ccn not in only:
            profiles += old_profiles.get(ccn, [])
            elements += old_elems.get(ccn, [])
            payers += old_payers.get(ccn, [])
            continue
        r, m = reg[ccn], manifest.get(ccn)
        base = {"ccn": ccn, "hospital": r["name"], "health_system": r["health_system"], "metro": r["metro"],
                "source_url": r["mrf_url"], "retrieved_at": (m or {}).get("retrieved_at", now_utc())}
        if not m or m["status"] != "ok":
            profiles.append({**base, "format": "not downloaded", "download_status": (m or {}).get("status", "not tried"),
                             "usable_coded_rows": False, **score(False, False, None, Counter())})
            print(ccn, "not downloaded", flush=True)
            continue
        prof, rows = parse_file(m["path"], ccn)
        counts = write_parquet(ccn, rows)
        found = prof.format.startswith("CMS")
        v = validator.get(ccn, {})
        valid = str(v.get("valid")) == "True"
        usable = found and counts["_priced_codes"] >= USABLE_MIN_CODES
        neg_total = sum(prof.negotiated[k] for k in ("dollar", "percent", "algorithm"))
        codes = {t: len(c) for t, c in prof.codes.items()}
        profiles.append({
            **base, "format": prof.format, "download_status": "ok", "schema_version": prof.schema_version,
            "sha256": m["sha256"], "size_bytes": m["size_bytes"], "file_last_updated": prof.last_updated_on,
            "http_last_modified": m["http_last_modified"], "source_items": prof.source_items, "rows": prof.rows,
            "distinct_cpt": codes.get("CPT", 0), "distinct_hcpcs": codes.get("HCPCS", 0),
            "distinct_ms_drg": codes.get("MS-DRG", 0),
            "distinct_other_codes": "; ".join(f"{t}={n}" for t, n in sorted(codes.items())
                                              if t not in USABLE_CODE_TYPES),
            "priced_usable_codes": counts["_priced_codes"],
            "share_rows_usable_code": round(prof.usable_rows / prof.rows, 4) if prof.rows else 0,
            "gross_rows": counts["gross"], "cash_rows": counts["cash"], "negotiated_records": neg_total,
            "share_negotiated_dollar": round(prof.negotiated["dollar"] / neg_total, 4) if neg_total else "",
            "share_negotiated_percent": round(prof.negotiated["percent"] / neg_total, 4) if neg_total else "",
            "share_negotiated_algorithm": round(prof.negotiated["algorithm"] / neg_total, 4) if neg_total else "",
            "pct_algo_records": prof.pct_algo_total, "pct_algo_with_median": prof.pct_algo_with_median,
            "validator_valid": v.get("valid", "not run"), "validator_errors": v.get("error_count", ""),
            "validator_alerts": v.get("alert_count", ""),
            "flags": "; ".join(f"{k}={n}" for k, n in prof.flags.items()),
            "usable_coded_rows": usable, **score(found, valid, prof, counts),
        })
        for e in ELEMENTS_2026:
            elements.append({"ccn": ccn, "hospital": r["name"], "element": e,
                             "status": prof.element_status(e) if found else "not applicable (no CMS file)",
                             "value_or_count": {"org_npi": prof.org_npi, "attester_name": prof.attester_name,
                                                "attestation_statement": prof.attestation_confirmed}.get(
                                 e, prof.element_filled.get(e, 0)),
                             "source_url": r["mrf_url"], "retrieved_at": base["retrieved_at"]})
        for (payer, plan), n in prof.payer_strings.items():
            payers.append({"raw_payer": payer, "raw_plan": plan, "hospital": r["name"], "ccn": ccn, "row_count": n,
                           "source_url": r["mrf_url"], "retrieved_at": base["retrieved_at"]})
        print(ccn, prof.format, prof.rows, counts["_priced_codes"], profiles[-1]["completeness_score"], flush=True)

    for path, data in ((prof_path, profiles), (elem_path, elements), (payer_path, payers)):
        cols = list(dict.fromkeys(k for d in data for k in d))
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(data)


if __name__ == "__main__":
    pathlib.Path(NORM).mkdir(parents=True, exist_ok=True)
    main()
