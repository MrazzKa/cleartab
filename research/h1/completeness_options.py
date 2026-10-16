"""Alternative completeness scores (F5) for the team and Dr. Li to choose from (meeting 2026-10-16). No option is
picked here.

Usage: python -m research.h1.completeness_options
Inputs: data/processed/h1_file_profile.csv (components C1-C5, 20 points each, research/h1/REPORT.md) and the
normalized files data/raw/normalized/<ccn>_f4.parquet for the launch-procedure measure.
Writes data/processed/completeness_options.csv.

A. Equal weights (current): C1 + C2 + C3 + C4 + C5.
B. Negotiated rates required: as A, but a hospital whose file has no payer-specific negotiated rate at all
   cannot score above 50.
C. Patient-weighted: P = share of the 50 launch procedures for which the hospital publishes a usable dollar price
   (a cash price or a fixed dollar negotiated rate that survives the F4 rules, facility or blank billing class,
   outpatient or both). Score = 50 x P + 10 x (C1 + C2 + C3 + C4 + C5) / 20. The 50/10 split is an illustration
   of "P counts most", not a recommendation.
"""
import csv

import polars as pl

from pipeline.common import PROCESSED, RAW, now_utc


def launch_share(ccn: str, codes: list[str]) -> tuple[float, int]:
    path = RAW / "normalized" / f"{ccn}_f4.parquet"
    if not path.exists():
        return 0.0, 0
    n = (pl.scan_parquet(path)
         .filter(pl.col("code").is_in(codes) & pl.col("code_type").is_in(["CPT", "HCPCS"]) & pl.col("headline_ok")
                 & pl.col("price_type").is_in(["cash", "negotiated_dollar"])
                 & pl.col("billing_class").fill_null("").is_in(["facility", ""])
                 & pl.col("setting").is_in(["outpatient", "both"]))
         .select(pl.col("code").n_unique()).collect().item())
    return n / len(codes), n


def main() -> None:
    with open(PROCESSED / "h1_file_profile.csv", newline="") as f:
        prof = list(csv.DictReader(f))
    with open(PROCESSED / "procedures.csv", newline="") as f:
        codes = [r["code"] for r in csv.DictReader(f)]
    rows = []
    for p in prof:
        c = [float(p[k] or 0) for k in ("c1_file_found", "c2_schema_valid", "c3_coded_rows", "c4_dollar_or_allowed",
                                        "c5_2026_elements")]
        a = round(sum(c), 1)
        has_neg = int(p["negotiated_records"] or 0) > 0
        share, n = launch_share(p["ccn"], codes)
        rows.append({"ccn": p["ccn"], "hospital": p["hospital"], "metro": p["metro"], "c1": c[0], "c2": c[1],
                     "c3": c[2], "c4": c[3], "c5": c[4], "has_negotiated_rates": has_neg,
                     "launch_procedures_with_usable_price": n, "launch_share": round(share, 3),
                     "score_a_equal": a, "score_b_negotiated_required": a if has_neg else min(a, 50.0),
                     "score_c_patient": round(50 * share + 10 * sum(c) / 20, 1)})
    df = pl.DataFrame(rows)
    for col, rk in (("score_a_equal", "rank_a"), ("score_b_negotiated_required", "rank_b"),
                    ("score_c_patient", "rank_c")):
        df = df.with_columns(pl.col(col).rank(method="min", descending=True).cast(pl.Int64).alias(rk))
    df = df.sort("rank_a", "hospital")
    df.with_columns(pl.lit("data/processed/h1_file_profile.csv; data/raw/normalized/<ccn>_f4.parquet").alias(
        "source_url"), pl.lit(now_utc()).alias("retrieved_at")).write_csv(PROCESSED / "completeness_options.csv")
    with pl.Config(tbl_rows=30, tbl_cols=20, tbl_width_chars=250):
        print(df.select("hospital", "c1", "c2", "c3", "c4", "c5", "has_negotiated_rates",
                        "launch_procedures_with_usable_price", "score_a_equal", "rank_a",
                        "score_b_negotiated_required", "rank_b", "score_c_patient", "rank_c"))
    for col in ("score_a_equal", "score_b_negotiated_required", "score_c_patient"):
        s = df[col]
        print(col, {"90+": int((s >= 90).sum()), "80-89": int(s.is_between(80, 89.99).sum()),
                    "50-79": int(s.is_between(50, 79.99).sum()), "1-49": int(s.is_between(0.01, 49.99).sum()),
                    "0": int((s == 0).sum())})


if __name__ == "__main__":
    main()
