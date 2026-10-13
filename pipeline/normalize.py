"""Feature 4: apply payer matching, methodology labels and outlier rules to the normalized long tables.

Rules (proposal Table 9), applied in this order; every dropped or flagged row is counted by reason:
  - negotiated_dollar, cash or gross amount under $1           -> dropped, reason under_1_dollar
  - negotiated_dollar above the gross charge of the same item   -> dropped, reason above_gross
  - item has no gross but the same code has one elsewhere in the file -> compare with the highest such gross,
    flag gross_from_code
  - negotiated_dollar with no gross for the code at all         -> kept, flag no_gross_to_check
  - negotiated_percent / negotiated_algorithm                   -> kept, never a dollar price
  - unparseable amounts from the parser                         -> dropped, reason unparseable
Methodology labels: case rate and fee schedule -> fixed dollar; percent of total billed charges -> percent of
charges; per diem -> per diem; other or an algorithm text -> algorithm. Only fixed dollar rows may be a
headline price (headline_ok).
Output: data/raw/normalized/<ccn>_f4.parquet, data/processed/f4_flag_log.csv, data/processed/f4_coverage.csv.
"""
import csv
import glob
from collections import Counter

import polars as pl
import pyarrow.parquet as pq

from pipeline.common import PROCESSED, RAW, now_utc
from pipeline.payers import match

ITEM = ["code", "code_type", "setting", "billing_class", "modifiers", "description"]
METHOD = {"case rate": "fixed dollar", "fee schedule": "fixed dollar", "percent of total billed charges":
          "percent of charges", "per diem": "per diem", "other": "algorithm"}


def aliases() -> pl.DataFrame:
    with open(PROCESSED / "payer_aliases.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    return pl.DataFrame({"payer_name": [r["raw_payer"] for r in rows], "plan_name": [r["raw_plan"] for r in rows],
                         "canonical_payer": [r["canonical_payer"] for r in rows],
                         "plan_type": [r["plan_type"] for r in rows]})


def normalize_file(path: str, alias: pl.DataFrame) -> tuple[pl.LazyFrame, Counter, dict]:
    """Stream <ccn>.parquet -> <ccn>_f4.parquet without loading the file into memory (Mayo: 57M rows).

    Returns a lazy scan of the output, the flag log and the coverage counts for this file.
    """
    out = path.replace(".parquet", "_f4.parquet")
    src = pl.scan_parquet(path).with_columns(pl.col(ITEM).fill_null(""))
    gross_rows = src.filter((pl.col("price_type") == "gross") & pl.col("amount").is_not_null())
    gross = gross_rows.group_by(ITEM).agg(pl.col("amount").max().alias("gross_charge")).collect(engine="streaming")
    # Some files (HonorHealth) put gross on a chargemaster row and rates on separate fee-schedule rows of the
    # same code. Fallback: the highest gross the hospital publishes for that code (conservative for dropping).
    code_gross = (gross_rows.group_by("code", "code_type").agg(pl.col("amount").max().alias("code_gross"))
                  .collect(engine="streaming"))
    pairs = (src.filter(pl.col("payer_name").is_not_null()).select("payer_name", "plan_name").unique()
             .collect(engine="streaming"))
    missing = pairs.join(alias, on=["payer_name", "plan_name"], how="anti")
    if missing.height:  # strings seen after the dictionary was built: match them with the same rules
        extra = [match(p, q) for p, q in missing.iter_rows()]
        alias = pl.concat([alias, pl.DataFrame({"payer_name": [e["raw_payer"] for e in extra],
                                                "plan_name": [e["raw_plan"] for e in extra],
                                                "canonical_payer": [e["canonical_payer"] for e in extra],
                                                "plan_type": [e["plan_type"] for e in extra]})])
    is_dollar = pl.col("price_type").is_in(["negotiated_dollar", "cash", "gross"])
    reason = (pl.when(pl.col("flags").is_in(["unparseable_amount", "unparseable_percentage"])).then(pl.lit("unparseable"))
              .when(is_dollar & (pl.col("amount") < 1)).then(pl.lit("under_1_dollar"))
              .when((pl.col("price_type") == "negotiated_dollar") & (pl.col("amount") > pl.col("gross_charge")))
              .then(pl.lit("above_gross"))
              .otherwise(pl.lit(None, dtype=pl.Utf8)))
    meth = pl.col("methodology").fill_null("").str.to_lowercase()
    label = (pl.when(pl.col("price_type") == "negotiated_algorithm").then(pl.lit("algorithm"))
             .when(pl.col("price_type") == "negotiated_percent").then(pl.lit("percent of charges"))
             .when(pl.col("price_type").is_in(["gross", "cash"])).then(pl.lit("fixed dollar"))
             .otherwise(meth.replace_strict(METHOD, default="unlabelled")))
    # Batches keep memory bounded on very large files: each batch is joined with the small lookup tables
    # (gross per item, gross per code, payer aliases) and appended to the output.
    gross_l, code_l, alias_l = gross.lazy(), code_gross.lazy(), alias.lazy()
    writer = None
    try:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=1_000_000):
            part = (pl.from_arrow(batch).lazy().with_columns(pl.col(ITEM).fill_null(""))
                    .join(gross_l, on=ITEM, how="left").join(code_l, on=["code", "code_type"], how="left")
                    .with_columns(pl.col("gross_charge").is_null().alias("_no_item_gross"))
                    .with_columns(pl.coalesce("gross_charge", "code_gross").alias("gross_charge")).drop("code_gross")
                    .join(alias_l, on=["payer_name", "plan_name"], how="left")
                    .with_columns(reason.alias("drop_reason"), label.alias("methodology_label"))
                    .with_columns(
                        pl.when((pl.col("price_type") == "negotiated_dollar") & pl.col("gross_charge").is_null())
                        .then(pl.lit("no_gross_to_check"))
                        .when((pl.col("price_type") == "negotiated_dollar") & pl.col("_no_item_gross"))
                        .then(pl.lit("gross_from_code")).otherwise(pl.lit(None, dtype=pl.Utf8)).alias("check_flag"),
                        (pl.col("drop_reason").is_null()
                         & pl.col("price_type").is_in(["negotiated_dollar", "cash", "gross"])
                         & (pl.col("methodology_label") == "fixed dollar")).alias("headline_ok"))
                    .collect().to_arrow())
            if writer is None:
                writer = pq.ParquetWriter(out, part.schema, compression="zstd")
            writer.write_table(part.cast(writer.schema))
    finally:
        if writer is not None:
            writer.close()
    f4 = pl.scan_parquet(out)
    log = Counter()
    for col in ("drop_reason", "check_flag"):
        for r, n in f4.group_by(col).len().collect(engine="streaming").iter_rows():
            if r:
                log[r] = n
    neg = f4.filter(pl.col("price_type").str.starts_with("negotiated"))
    for lab, n in neg.group_by("methodology_label").len().collect(engine="streaming").iter_rows():
        log[f"methodology: {lab}"] = n
    kept = neg.filter(pl.col("drop_reason").is_null())
    total, canon = kept.select(pl.len(), (pl.col("canonical_payer") != "other").sum()).collect(engine="streaming").row(0)
    return f4, log, {"negotiated_rows": total, "canonical_rows": canon or 0}


def main() -> None:
    alias = aliases()
    logs, cov = [], []
    for path in sorted(glob.glob(str(RAW / "normalized" / "[0-9]*.parquet"))):
        if path.endswith("_f4.parquet"):
            continue
        ccn = path.rsplit("/", 1)[-1][:6]
        _, log, c = normalize_file(path, alias)
        for k, n in sorted(log.items()):
            logs.append({"ccn": ccn, "reason": k, "rows": n, "source_url": f"data/raw/normalized/{ccn}.parquet",
                         "retrieved_at": now_utc()})
        cov.append({"ccn": ccn, **c, "coverage": round(c["canonical_rows"] / c["negotiated_rows"], 4)
                    if c["negotiated_rows"] else "",
                    "source_url": f"data/raw/normalized/{ccn}.parquet", "retrieved_at": now_utc()})
        print(ccn, dict(log), cov[-1]["coverage"], flush=True)
    tot_n = sum(c["negotiated_rows"] for c in cov)
    tot_c = sum(c["canonical_rows"] for c in cov)
    cov.append({"ccn": "ALL", "negotiated_rows": tot_n, "canonical_rows": tot_c,
                "coverage": round(tot_c / tot_n, 4) if tot_n else "", "source_url": "", "retrieved_at": now_utc()})
    for name, data in (("f4_flag_log.csv", logs), ("f4_coverage.csv", cov)):
        with open(PROCESSED / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print("overall coverage", cov[-1])


if __name__ == "__main__":
    main()
