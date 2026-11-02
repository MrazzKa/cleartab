"""Published-file figures for one accuracy-check pair when the hospital is not in the H1 sample.

Usage: python -m research.accuracy_check.published_figures CCN CODE

The file is downloaded once (same polite downloader as the ETL), checked with the CMS validator, parsed and
normalized with the pipeline code, but written to data/raw/accuracy/ instead of data/raw/normalized/, so the H1,
H2 and coverage analyses (which read data/raw/normalized/) do not change. Figures follow api/main.py: median of
the published items for the code, setting outpatient or both, dropped rows excluded. Printed as JSON.
"""
import csv
import json
import sys

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from pipeline import validate
from pipeline.common import RAW, REGISTRY_CSV, ROOT, now_utc
from pipeline.download import download, load_manifest, save_manifest
from pipeline.h1_profile import SCHEMA
from pipeline.http import PoliteSession
from pipeline.normalize import aliases, normalize_file
from pipeline.parsers.cms import parse_file

OUT = RAW / "accuracy"


def main() -> None:
    ccn, code = sys.argv[1], sys.argv[2]
    with open(REGISTRY_CSV, newline="") as f:
        reg = {r["ccn"]: r for r in csv.DictReader(f)}[ccn]
    manifest = load_manifest()
    m = download(PoliteSession(), ccn, reg["mrf_url"], manifest)
    manifest[(ccn, reg["mrf_url"])] = m
    save_manifest(manifest)
    if m.get("status") != "ok":
        print(json.dumps({"ccn": ccn, "error": m.get("status")}))
        return
    path = str(ROOT / m["path"])
    val = validate.run(ccn, path, reg["mrf_url"])
    OUT.mkdir(parents=True, exist_ok=True)
    raw_pq = OUT / f"{ccn}.parquet"
    prof, rows = parse_file(path, ccn)
    with pq.ParquetWriter(raw_pq, SCHEMA, compression="zstd") as w:
        batch = []
        for r in rows:
            batch.append(r)
            if len(batch) == 500_000:
                w.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
                batch = []
        if batch:
            w.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
    f4, _, _ = normalize_file(str(raw_pq), aliases())
    rows = (f4.filter((pl.col("code") == code) & pl.col("setting").is_in(["outpatient", "both"])
                      & pl.col("drop_reason").is_null()).collect())

    def figures(df: pl.DataFrame) -> dict:
        def med(pt: str) -> dict:
            s = df.filter(pl.col("price_type") == pt)["amount"]
            return {"median": s.median(), "min": s.min(), "max": s.max(), "items": s.len()}
        neg = df.filter((pl.col("price_type") == "negotiated_dollar") & (pl.col("methodology_label") == "fixed dollar")
                        & (pl.col("canonical_payer") != "other"))["amount"]
        return {"gross": med("gross"), "cash": med("cash"),
                "negotiated_fixed_dollar_canonical_insurers": {"min": neg.min(), "median": neg.median(),
                                                               "max": neg.max(), "rows": neg.len()},
                "billing_classes": sorted(set(df["billing_class"].to_list())),
                "items": df.filter(pl.col("price_type").is_in(["gross", "cash"])).select(
                    "description", "billing_class", "modifiers", "price_type", "amount").unique().sort(
                    "price_type", "amount").to_dicts()}

    print(json.dumps({
        "ccn": ccn, "hospital": reg["name"], "code": code, "source_url": reg["mrf_url"],
        "sha256": m["sha256"], "size_bytes": m["size_bytes"], "file_last_updated": prof.last_updated_on,
        "http_last_modified": m.get("http_last_modified"), "downloaded_at": m["retrieved_at"],
        "validator": {k: val.get(k) for k in ("valid", "error_count", "alert_count", "note")},
        "api_rules": figures(rows), "facility_only": figures(rows.filter(pl.col("billing_class") == "facility")),
        "computed_at": now_utc()}, indent=1, default=str))


if __name__ == "__main__":
    main()
