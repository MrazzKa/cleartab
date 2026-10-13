"""Count, per code, how many usable H1 hospitals publish a priced row for it.

CPT and HCPCS labels are merged into one code system for counting: CPT is HCPCS Level I and HonorHealth
labels CPT codes as "HCPCS". The original labels stay in the normalized data.
"""
import glob

import pandas as pd
import polars as pl

from pipeline.common import now_utc

prof = pd.read_csv("data/processed/h1_file_profile.csv", dtype={"ccn": str})
usable = set(prof[prof.usable_coded_rows.astype(str) == "True"].ccn)
SYSTEM = pl.when(pl.col("code_type").is_in(["CPT", "HCPCS"])).then(pl.lit("CPT/HCPCS")).otherwise(pl.col("code_type"))
frames = []
for path in glob.glob("data/raw/normalized/*.parquet"):
    ccn = path[-14:-8]
    if ccn not in usable:
        continue
    frames.append(
        pl.scan_parquet(path)
        .filter(pl.col("usable_code") & (pl.col("amount").is_not_null() | pl.col("percentage").is_not_null()))
        .with_columns(SYSTEM.alias("code_system"))
        .group_by("code_system", "code")
        .agg(pl.lit(ccn).alias("ccn"),
             (pl.col("price_type") == "cash").any().alias("has_cash"),
             (pl.col("price_type") == "negotiated_dollar").any().alias("has_neg_dollar"),
             (pl.col("price_type") == "negotiated_dollar").sum().alias("neg_dollar_rows"),
             pl.col("setting").mode().first().alias("setting"),
             pl.col("description").mode().first().alias("description"))
        .collect())
allc = pl.concat(frames)
freq = (allc.group_by("code_system", "code")
        .agg(pl.len().alias("hospitals"), pl.col("has_cash").sum().alias("with_cash"),
             pl.col("has_neg_dollar").sum().alias("with_neg_dollar"), pl.col("neg_dollar_rows").sum(),
             pl.col("setting").mode().first().alias("setting"),
             pl.col("description").sort_by(pl.col("description").str.len_chars()).first().alias("short_desc"),
             pl.col("ccn").sort().str.join(";").alias("ccns"))
        .with_columns(pl.lit("data/raw/normalized/<ccn>.parquet; file URLs in h1_file_profile.csv").alias("source_url"),
                      pl.lit(now_utc()).alias("retrieved_at"))
        .sort(["hospitals", "neg_dollar_rows"], descending=True))
freq.write_csv("data/processed/code_frequency.csv")
n8 = freq.filter(pl.col("hospitals") >= 8).height
print(f"{len(usable)} usable hospitals; {freq.height} codes; in >= 8 hospitals: {n8}")
