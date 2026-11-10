"""Emergency department visit rates per hospital and insurer (plan item P10).

Source: the normalized hospital files (data/raw/normalized/<ccn>_f4.parquet, built by pipeline.normalize from each
hospital's machine-readable file). Kept: CPT 99281-99285 (ED visit levels 1-5), facility or unlabeled billing
class, outpatient or both settings, negotiated dollar amounts with a canonical insurer, plus the cash and gross
charge per level. Percent-of-charges and algorithm rates are not dollar prices and are left out (hard rule 7).

A rate that F4 dropped as "above_gross" is kept with that flag: a per-visit case rate is often higher than the
gross charge of the level-1 line it is attached to, which is how the hospital publishes it, not an error to fix.

Output: data/processed/er_rates.csv (one row per hospital, insurer, plan, plan type, level, amount, methodology),
with source_url and retrieved_at of the hospital file. Run: python -m pipeline.er_rates
"""
import csv
import glob
import os

import polars as pl

from pipeline.common import DATABASE_URL, PROCESSED, RAW

LEVELS = ["99281", "99282", "99283", "99284", "99285"]
OUT = PROCESSED / "er_rates.csv"
FIELDS = ["ccn", "hospital", "price_type", "canonical_payer", "plan_name", "plan_type", "code", "amount",
          "methodology", "f4_flag", "source_url", "retrieved_at"]


def hospitals() -> dict[str, dict]:
    """Name, file URL and download time per CCN from the database (latest file per hospital)."""
    import psycopg
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute("""
            SELECT DISTINCT ON (h.ccn) h.ccn, h.name, s.url, s.retrieved_at
            FROM hospitals h JOIN source_files s ON s.hospital_id = h.id
            ORDER BY h.ccn, s.retrieved_at DESC""").fetchall()
    return {r[0]: {"hospital": r[1], "source_url": r[2], "retrieved_at": r[3].isoformat()} for r in rows}


def rows_for(path: str) -> pl.DataFrame:
    lf = pl.scan_parquet(path).filter(
        pl.col("code").is_in(LEVELS)
        & pl.col("setting").is_in(["outpatient", "both", ""])
        & pl.col("billing_class").is_in(["facility", ""])
        & pl.col("amount").is_not_null()
        & (pl.col("amount") >= 1))
    neg = lf.filter((pl.col("price_type") == "negotiated_dollar") & pl.col("canonical_payer").is_not_null()
                    & (pl.col("drop_reason").is_null() | (pl.col("drop_reason") == "above_gross")))
    std = lf.filter(pl.col("price_type").is_in(["cash", "gross"]))
    cols = ["ccn", "price_type", "canonical_payer", "plan_name", "plan_type", "code", "amount", "methodology",
            "drop_reason"]
    both = pl.concat([neg.select(cols), std.select(cols)]).with_columns(
        pl.col("amount").round(2), pl.col("drop_reason").fill_null("").alias("f4_flag")).drop("drop_reason")
    return both.unique().collect(engine="streaming")


def main() -> None:
    meta = hospitals()
    files = sorted(glob.glob(os.path.join(RAW, "normalized", "*_f4.parquet")))
    out = []
    for f in files:
        df = rows_for(f)
        for r in df.iter_rows(named=True):
            m = meta.get(r["ccn"])
            if not m:
                continue
            out.append({**r, **m, "canonical_payer": r["canonical_payer"] or "", "plan_name": r["plan_name"] or "",
                        "plan_type": r["plan_type"] or "", "methodology": r["methodology"] or ""})
    out.sort(key=lambda r: (r["ccn"], r["price_type"], r["canonical_payer"], r["plan_name"], r["code"], r["amount"]))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    hosp = {r["ccn"] for r in out}
    print(f"{OUT}: {len(out)} rows, {len(hosp)} hospitals of {len(files)} files")
    for ccn in sorted({os.path.basename(f)[:6] for f in files} - hosp):
        print(f"  no ED visit rates (99281-99285) in {ccn}")


if __name__ == "__main__":
    main()
