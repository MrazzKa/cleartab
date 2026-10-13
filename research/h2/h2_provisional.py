"""Provisional H2 numbers on rows that survive the Feature 4 rules (PROVISIONAL until both raters accept the
payer dictionary).

Comparable negotiated rate: a negotiated_dollar row for a launch procedure code (CPT and HCPCS labels merged),
methodology label "fixed dollar", not dropped by an outlier rule, billing class facility (or blank), setting
outpatient or both, canonical payer not "other".

Primary measure (proposal Table 13): for each launch procedure and metro with >= 2 hospitals, the ratio of the
highest to the lowest hospital-level median comparable rate; then the median of those ratios.
Sensitivity: (a) same insurer: the ratio computed within each canonical insurer, then the median per
procedure-metro; (b) row level: highest / lowest single comparable rate per procedure-metro.
Cash: share of the 50 procedures where the median of hospital cash prices is below the median of all
comparable negotiated rates; and the share of hospital-procedure pairs where the hospital's own cash price is
below its own median comparable rate.
Writes data/processed/h2_provisional_by_procedure.csv.

Option --payer-rule (sensitivity for the round 1 inter-rater disagreement, research/h2/REPORT.md): mappings made
by the "network contract" rule (payer is an employer plan, fund or administrator; the plan column names a listed
insurer's contract, for example Mayo's "AZ CIGNA [39]") are put back to "other", as in the round 1 dictionary.
Writes data/processed/h2_payer_rule_by_procedure.csv instead.
"""
import csv
import glob
import sys

import polars as pl

from pipeline.common import now_utc

with open("data/processed/hospital_registry.csv", newline="") as f:
    metro = {r["ccn"]: r["metro"] for r in csv.DictReader(f)}
with open("data/processed/procedures.csv", newline="") as f:
    procs = {r["code"]: r["plain_name"] for r in csv.DictReader(f)}

frames = []
for path in glob.glob("data/raw/normalized/*_f4.parquet"):
    ccn = path.rsplit("/", 1)[-1][:6]
    frames.append(
        pl.scan_parquet(path)
        .filter(pl.col("code").is_in(list(procs)) & pl.col("code_type").is_in(["CPT", "HCPCS"])
                & pl.col("drop_reason").is_null()
                & pl.col("billing_class").is_in(["facility", ""]) & pl.col("setting").is_in(["outpatient", "both"]))
        .select("code", "price_type", "amount", "methodology_label", "canonical_payer", "plan_type", "payer_name",
                "plan_name")
        .with_columns(pl.lit(ccn).alias("ccn"), pl.lit(metro[ccn]).alias("metro"))
        .collect())
df = pl.concat(frames)
PAYER_RULE = "--payer-rule" in sys.argv
if PAYER_RULE:
    with open("data/processed/payer_aliases.csv", newline="") as f:
        contract = [(r["raw_payer"], r["raw_plan"]) for r in csv.DictReader(f) if r["method"] == "network contract"]
    revert = pl.DataFrame({"payer_name": [x for x, _ in contract], "plan_name": [y for _, y in contract],
                           "_revert": [True] * len(contract)})
    df = (df.join(revert, on=["payer_name", "plan_name"], how="left")
          .with_columns(pl.when(pl.col("_revert")).then(pl.lit("other")).otherwise(pl.col("canonical_payer"))
                        .alias("canonical_payer")).drop("_revert"))
neg = df.filter((pl.col("price_type") == "negotiated_dollar") & (pl.col("methodology_label") == "fixed dollar")
                & (pl.col("canonical_payer") != "other") & pl.col("canonical_payer").is_not_null())
cash = df.filter(pl.col("price_type") == "cash")

hosp_med = neg.group_by("code", "metro", "ccn").agg(pl.col("amount").median().alias("med"))
primary = (hosp_med.group_by("code", "metro")
           .agg(pl.len().alias("hospitals"), (pl.col("med").max() / pl.col("med").min()).alias("ratio"))
           .filter(pl.col("hospitals") >= 2))
payer_med = neg.group_by("code", "metro", "canonical_payer", "ccn").agg(pl.col("amount").median().alias("med"))
same_payer = (payer_med.group_by("code", "metro", "canonical_payer")
              .agg(pl.len().alias("h"), (pl.col("med").max() / pl.col("med").min()).alias("r"))
              .filter(pl.col("h") >= 2)
              .group_by("code", "metro").agg(pl.col("r").median().alias("same_payer_ratio")))
rowlevel = neg.group_by("code", "metro").agg((pl.col("amount").max() / pl.col("amount").min()).alias("row_ratio"))

hosp_cash = cash.group_by("code", "ccn").agg(pl.col("amount").min().alias("cash"))
cash_cmp = (hosp_cash.group_by("code").agg(pl.col("cash").median().alias("median_cash"))
            .join(neg.group_by("code").agg(pl.col("amount").median().alias("median_negotiated")), on="code",
                  how="full", coalesce=True))
pairs = hosp_cash.join(neg.group_by("code", "ccn").agg(pl.col("amount").median().alias("own_med")),
                       on=["code", "ccn"], how="inner")

out = (primary.join(same_payer, on=["code", "metro"], how="left").join(rowlevel, on=["code", "metro"], how="left")
       .with_columns(pl.col("code").replace_strict(procs, default="").alias("plain_name"),
                     pl.lit("data/raw/normalized/*_f4.parquet").alias("source_url"),
                     pl.lit(now_utc()).alias("retrieved_at"))
       .sort("metro", "code"))
out.write_csv("data/processed/h2_payer_rule_by_procedure.csv" if PAYER_RULE
              else "data/processed/h2_provisional_by_procedure.csv")

print("comparable negotiated rows:", neg.height, "hospitals:", neg["ccn"].n_unique(),
      "by metro:", dict(neg.group_by("metro").agg(pl.col("ccn").n_unique()).iter_rows()))
print("procedure-metro pairs with >= 2 hospitals:", primary.height,
      "by metro:", dict(primary.group_by("metro").len().iter_rows()))
print(f"PRIMARY median highest-to-lowest ratio: {primary['ratio'].median():.2f}  "
      f"(IQR {primary['ratio'].quantile(0.25):.2f}-{primary['ratio'].quantile(0.75):.2f})")
for m in ("Phoenix", "Tucson"):
    s = primary.filter(pl.col("metro") == m)["ratio"]
    print(f"  {m}: n={s.len()} median={s.median() if s.len() else 'n/a'}")
print(f"procedures with ratio >= 2: {primary.filter(pl.col('ratio') >= 2).height} of {primary.height}")
print(f"sensitivity same-insurer median ratio: {out['same_payer_ratio'].drop_nulls().median():.2f} "
      f"(n={out['same_payer_ratio'].drop_nulls().len()})")
print(f"sensitivity row-level median ratio: {out['row_ratio'].median():.2f}")
cc = cash_cmp.drop_nulls()
below = cc.filter(pl.col("median_cash") < pl.col("median_negotiated")).height
print(f"CASH: procedures with median cash < median negotiated: {below} of {cc.height} "
      f"({below / cc.height:.0%}); procedures in launch list: {len(procs)}")
pb = pairs.filter(pl.col("cash") < pl.col("own_med")).height
print(f"CASH: hospital-procedure pairs with cash < own median negotiated: {pb} of {pairs.height} "
      f"({pb / pairs.height:.0%})")
