"""ClearTab ETL: registry -> download -> validate -> parse -> normalize (F4) -> prices table -> completeness (F5).

Usage:  python -m pipeline.run [CCN ...]        default: the H1 sample hospitals
        python -m pipeline.run --all             every registry hospital with a file URL that robots.txt allows

A second run with unchanged files skips the download (conditional GET, sha256 check), the validator (cached by
sha256) and the parse (parquet cached by sha256). Prices are loaded for the launch procedures only; the
completeness score is computed over the whole file. Each run appends a line per hospital to
data/processed/etl_runs.csv.
"""
import csv
import io
import json
import sys
import time
from datetime import datetime
from urllib.parse import urlsplit

import polars as pl
import psycopg

from pipeline import validate
from pipeline.common import DATABASE_URL, PROCESSED, RAW, REGISTRY_CSV, now_utc
from pipeline.download import download, load_manifest, save_manifest
from pipeline.h1_download import SAMPLE
from pipeline.h1_profile import process_hospital
from pipeline.http import PoliteSession, RobotsDisallowed
from pipeline.load_registry import main as load_registry
from pipeline.normalize import aliases, normalize_file
from pipeline.payers import CANONICAL

CACHE = PROCESSED / "etl_cache.json"      # sha256 -> validator result and profile, so unchanged files are skipped
RUNS = PROCESSED / "etl_runs.csv"
PRICE_COLS = ["hospital_id", "source_file_id", "procedure_id", "payer_id", "raw_payer", "raw_plan", "setting",
              "price_type", "amount", "percentage", "algorithm_text", "methodology", "flags", "source_url",
              "retrieved_at"]


def parse_date(s: str) -> str | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except (ValueError, AttributeError):
            continue
    return None


def ensure_payers(cur) -> dict[str, int]:
    for name in CANONICAL:
        cur.execute("INSERT INTO payers (canonical_name, plan_type, source_url, retrieved_at) SELECT %s, NULL, %s, %s"
                    " WHERE NOT EXISTS (SELECT 1 FROM payers WHERE canonical_name = %s AND plan_type IS NULL)",
                    (name, "pipeline/payers.py", now_utc(), name))
    cur.execute("SELECT canonical_name, id FROM payers WHERE plan_type IS NULL")
    return dict(cur.fetchall())


def load_hospital(conn, ccn: str, m: dict, profile: dict, f4: pl.LazyFrame | None, payer_ids: dict, proc_ids: dict) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM hospitals WHERE ccn = %s", (ccn,))
        hid = cur.fetchone()[0]
        cur.execute("""INSERT INTO source_files (hospital_id, url, sha256, size_bytes, format, schema_version,
                       file_last_updated, attester_name, attestation_present, org_npi, http_last_modified,
                       retrieved_at, validator_errors, validator_warnings)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (hospital_id, sha256) DO UPDATE SET retrieved_at = EXCLUDED.retrieved_at,
                       validator_errors = EXCLUDED.validator_errors, validator_warnings = EXCLUDED.validator_warnings
                       RETURNING id""",
                    (hid, m["url"], m["sha256"], m["size_bytes"], profile.get("format"), profile.get("schema_version"),
                     parse_date(profile.get("file_last_updated", "")), profile.get("attester_name") or None,
                     profile.get("attestation_present"), profile.get("org_npi") or None, m.get("http_last_modified"),
                     m["retrieved_at"], profile.get("validator_errors") or None, profile.get("validator_alerts") or None))
        sfid = cur.fetchone()[0]
        cur.execute("DELETE FROM prices WHERE hospital_id = %s", (hid,))   # idempotent reload of this hospital
        rows = 0
        if f4 is not None:
            launch = (f4.filter(pl.col("code").is_in(list(proc_ids)) & pl.col("code_type").is_in(["CPT", "HCPCS"]))
                      .collect(engine="streaming")
                      .with_columns(pl.col("code").replace_strict(proc_ids).alias("procedure_id"),
                                    pl.col("canonical_payer").replace_strict(payer_ids, default=None).alias("payer_id"),
                                    pl.concat_str([pl.lit("{"), pl.concat_str([
                                        pl.when(pl.col("drop_reason").is_not_null())
                                        .then(pl.lit("dropped:") + pl.col("drop_reason")),
                                        pl.col("check_flag"), pl.col("flags").replace("", None)],
                                        separator=",", ignore_nulls=True), pl.lit("}")]).alias("flags_arr")))
            buf = io.StringIO()
            w = csv.writer(buf)
            src, ts = m["url"], m["retrieved_at"]
            for r in launch.iter_rows(named=True):
                w.writerow([hid, sfid, r["procedure_id"], r["payer_id"] if r["payer_name"] else None, r["payer_name"],
                            r["plan_name"], r["setting"], r["price_type"], r["amount"], r["percentage"], r["algorithm"],
                            r["methodology_label"], r["flags_arr"], src, ts])
                rows += 1
            buf.seek(0)
            with cur.copy(f"COPY prices ({', '.join(PRICE_COLS)}) FROM STDIN WITH (FORMAT csv)") as cp:
                cp.write(buf.read())
        status = "published" if profile.get("usable_coded_rows") in (True, "True") else "not published"
        cur.execute("UPDATE hospitals SET completeness_score = %s, status = %s, retrieved_at = %s WHERE id = %s",
                    (profile.get("completeness_score"), status, m["retrieved_at"], hid))
    conn.commit()
    return rows


def main() -> None:
    args = sys.argv[1:]
    t0 = time.monotonic()
    load_registry()
    with open(REGISTRY_CSV, newline="") as f:
        reg = {r["ccn"]: r for r in csv.DictReader(f)}
    if "--all" in args:
        ccns = [c for c, r in reg.items() if r["mrf_url"].startswith("http")]
    else:
        ccns = [a for a in args if not a.startswith("--")] or SAMPLE
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    manifest = load_manifest()
    session = PoliteSession()
    alias = aliases()
    run_rows = []
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            payer_ids = ensure_payers(cur)
            cur.execute("SELECT code, id FROM procedures WHERE is_launch")
            proc_ids = dict(cur.fetchall())
        conn.commit()
        for ccn in ccns:
            r = reg[ccn]
            url = r["mrf_url"]
            st = {"ccn": ccn, "hospital": r["name"], "started_at": now_utc()}
            t = time.monotonic()
            try:
                m = download(session, ccn, url, manifest, force="--force" in args)
            except RobotsDisallowed:
                m = {"ccn": ccn, "url": url, "status": "robots.txt disallows"}
            except Exception as e:  # reported, never skipped silently
                m = {"ccn": ccn, "url": url, "status": f"error: {str(e)[:200]}"}
            manifest[(ccn, url)] = {**manifest.get((ccn, url), {}), **m}
            save_manifest(manifest)
            st["download"] = m.get("note") or m.get("status")
            st["t_download_s"] = round(time.monotonic() - t, 1)
            if m.get("status") != "ok":
                st.update(result=f"not loaded: {m.get('status')}")
                run_rows.append(st)
                print(st, flush=True)
                continue
            key = m["sha256"]
            entry = cache.get(key, {})
            t = time.monotonic()
            if "validator" not in entry:
                entry["validator"] = validate.run(ccn, m["path"], url)
            st["t_validate_s"] = round(time.monotonic() - t, 1)
            t = time.monotonic()
            parquet = RAW / "normalized" / f"{ccn}.parquet"
            if "profile" not in entry or not parquet.exists():
                profile, _, _ = process_hospital(ccn, r, m, entry["validator"])
                entry["profile"] = profile
            profile = entry["profile"]
            st["t_parse_s"] = round(time.monotonic() - t, 1)
            cache[key] = entry
            CACHE.write_text(json.dumps(cache, indent=1, default=str))
            t = time.monotonic()
            f4 = None
            if profile.get("format", "").startswith("CMS"):
                f4, log, _ = normalize_file(str(parquet), alias)
                st["flags"] = "; ".join(f"{k}={n}" for k, n in sorted(log.items()) if not k.startswith("methodology"))
            st["t_normalize_s"] = round(time.monotonic() - t, 1)
            t = time.monotonic()
            st["price_rows_loaded"] = load_hospital(conn, ccn, m, profile, f4, payer_ids, proc_ids)
            st["t_load_s"] = round(time.monotonic() - t, 1)
            st.update(completeness_score=profile.get("completeness_score"), result="loaded",
                      source_url=url, retrieved_at=m["retrieved_at"], host=urlsplit(url).netloc)
            run_rows.append(st)
            print({k: v for k, v in st.items() if k not in ("flags",)}, flush=True)
    total = round(time.monotonic() - t0, 1)
    cols = ["ccn", "hospital", "started_at", "result", "download", "price_rows_loaded", "completeness_score",
            "t_download_s", "t_validate_s", "t_parse_s", "t_normalize_s", "t_load_s", "flags", "host", "source_url",
            "retrieved_at", "run_total_s"]
    new = not RUNS.exists()
    with open(RUNS, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if new:
            w.writeheader()
        for row in run_rows:
            w.writerow({**row, "run_total_s": total})
    print(f"run finished in {total} s; {sum(1 for x in run_rows if x.get('result') == 'loaded')} hospitals loaded")


if __name__ == "__main__":
    main()
