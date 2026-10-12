"""For percent or algorithm negotiated records with no median allowed amount, how many report count 0 or
"1 through 10" (no median expected) versus no count at all (median simply omitted)."""
import glob

import polars as pl

KEY = ["code", "code_type", "setting", "billing_class", "modifiers", "description", "payer_name", "plan_name"]
print("ccn     pct_algo  no_median  of_which_count0  of_which_1to10  of_which_no_count")
for path in sorted(glob.glob("data/raw/normalized/*.parquet")):
    df = pl.read_parquet(path).with_columns(pl.col(KEY).fill_null(""))
    pa = df.filter(pl.col("price_type").is_in(["negotiated_percent", "negotiated_algorithm"])).select(KEY).unique()
    if pa.height == 0:
        continue
    med = df.filter((pl.col("price_type") == "allowed_median") & pl.col("amount").is_not_null()).select(KEY).unique()
    cnt = df.filter(pl.col("price_type") == "allowed_count").select(
        KEY + [pl.when(pl.col("flags") == "count_1_through_10").then(pl.lit("1-10"))
               .when(pl.col("amount") == 0).then(pl.lit("0")).otherwise(pl.lit("n")).alias("c")]).unique(KEY)
    nomed = pa.join(med, on=KEY, how="anti").join(cnt, on=KEY, how="left")
    c = nomed["c"].value_counts().to_dict(as_series=False)
    d = dict(zip(c["c"], c["count"], strict=True))
    print(f"{path[-14:-8]}  {pa.height:8d}  {nomed.height:9d}  {d.get('0', 0):15d}  {d.get('1-10', 0):14d}  "
          f"{d.get(None, 0):17d}")
