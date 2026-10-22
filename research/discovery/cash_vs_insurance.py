"""Cash or insurance: how often does a hospital's own discounted cash price sit below what a named insurer pays
that hospital for the same procedure?

Question (discovery, 2026-10-22): the H2 cash measure compares cash with the median negotiated rate across all
insurers (1 of 50 procedures). A patient with a deductible pays their own insurer's rate, so the comparison that
matters to them is per insurer. The UA Campus Health insurance office reported (written answer, 2026-10-21) that
students are "in disbelief that services often cost more with insurance than without".

Comparable rows: exactly the H2 filters (research/h2/h2_provisional.py): launch procedure codes (CPT and HCPCS),
billing class facility or blank, setting outpatient or both, not dropped by an F4 rule. Negotiated: fixed dollar
negotiated rate of a canonical insurer (not "other").
Main population: plan types commercial and marketplace, where a patient below the deductible pays the negotiated
rate and could choose to pay cash instead. AHCCCS, Medicare Advantage and other government plans are reported
separately for reference only (their members usually pay little or nothing themselves).

Units:
- pair: hospital x procedure with a cash price and at least one main-population insurer rate.
- triple: hospital x procedure x insurer x plan type, rate = median of that insurer's fixed dollar rates there.
Cash per hospital and procedure = median of its cash rows (sensitivity: highest cash row, the least favourable
to cash). Confidence intervals: cluster bootstrap over hospitals.

Usage: python -m research.discovery.cash_vs_insurance
Inputs: data/raw/normalized/<ccn>_f4.parquet (H1 sample, data/processed/h1_file_profile.csv), procedures.csv.
Outputs: data/processed/cash_vs_insurance_triples.csv, cash_vs_insurance_summary.csv; numbers printed for
research/discovery/cash_vs_insurance.md.
"""
import csv

import numpy as np
import polars as pl

from pipeline.common import PROCESSED, RAW, now_utc

SEED = 20261022
B = 2_000          # cluster bootstrap draws (hospitals resampled)
MAIN = ["commercial", "marketplace"]
REFERENCE = ["ahcccs", "medicare advantage", "government"]


def load() -> tuple[pl.DataFrame, dict]:
    with open(PROCESSED / "h1_file_profile.csv", newline="") as f:
        prof = {r["ccn"]: r for r in csv.DictReader(f)}
    with open(PROCESSED / "procedures.csv", newline="") as f:
        procs = {r["code"]: r["plain_name"] for r in csv.DictReader(f)}
    frames = []
    for ccn, p in prof.items():
        path = RAW / "normalized" / f"{ccn}_f4.parquet"
        if not path.exists():
            continue
        frames.append(
            pl.scan_parquet(path)
            .filter(pl.col("code").is_in(list(procs)) & pl.col("code_type").is_in(["CPT", "HCPCS"])
                    & pl.col("drop_reason").is_null()
                    & pl.col("billing_class").is_in(["facility", ""]) & pl.col("setting").is_in(["outpatient", "both"]))
            .select("code", "price_type", "amount", "methodology_label", "canonical_payer", "plan_type")
            .with_columns(pl.lit(ccn).alias("ccn"), pl.lit(p["hospital"]).alias("hospital"),
                          pl.lit(p["health_system"]).alias("system"), pl.lit(p["metro"]).alias("metro"))
            .collect())
    return pl.concat(frames), procs


def triples(df: pl.DataFrame, cash_agg: pl.Expr, plan_types: list[str]) -> pl.DataFrame:
    cash = df.filter(pl.col("price_type") == "cash").group_by("ccn", "code").agg(cash_agg.alias("cash"))
    neg = df.filter((pl.col("price_type") == "negotiated_dollar") & (pl.col("methodology_label") == "fixed dollar")
                    & (pl.col("canonical_payer") != "other") & pl.col("canonical_payer").is_not_null()
                    & pl.col("plan_type").is_in(plan_types))
    return (neg.group_by("ccn", "hospital", "system", "metro", "code", "canonical_payer", "plan_type")
            .agg(pl.col("amount").median().alias("rate"), pl.len().alias("rate_rows"))
            .join(cash, on=["ccn", "code"], how="inner")
            .with_columns((pl.col("rate") > pl.col("cash")).alias("insurer_above_cash"),
                          (pl.col("rate") - pl.col("cash")).alias("rate_minus_cash")))


def shares(t: pl.DataFrame) -> tuple[float, float]:
    """(share of pairs where at least one insurer pays more than cash, share of triples above cash)."""
    pairs = t.group_by("ccn", "code").agg(pl.col("insurer_above_cash").any().alias("any"))
    return pairs["any"].mean(), t["insurer_above_cash"].mean()


def cluster_ci(t: pl.DataFrame, rng: np.random.Generator) -> list[tuple[float, float]]:
    by_h = {c: g for (c,), g in t.partition_by("ccn", as_dict=True).items()}
    ccns = list(by_h)
    draws = np.empty((B, 2))
    for i in range(B):
        pick = rng.choice(ccns, len(ccns), replace=True)
        # relabel resampled hospitals so a hospital drawn twice counts as two clusters
        s = pl.concat([by_h[c].with_columns(pl.lit(f"{c}#{k}").alias("ccn")) for k, c in enumerate(pick)])
        draws[i] = shares(s)
    return [tuple(np.percentile(draws[:, j], [2.5, 97.5])) for j in range(2)]


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    df, procs = load()
    rng = np.random.default_rng(SEED)
    t = triples(df, pl.col("amount").median(), MAIN)
    t_hi = triples(df, pl.col("amount").max(), MAIN)
    t_ref = triples(df, pl.col("amount").median(), REFERENCE)
    multi_cash = (df.filter(pl.col("price_type") == "cash").group_by("ccn", "code")
                  .agg(pl.col("amount").n_unique().alias("n")).filter(pl.col("n") > 1).height)

    rows = []

    def add(group: str, value: str, s: pl.DataFrame, ci: list | None = None) -> None:
        p_any, p_tri = shares(s)
        above = s.filter(pl.col("insurer_above_cash"))
        rows.append({"group": group, "value": value, "hospitals": s["ccn"].n_unique(),
                     "pairs": s.select("ccn", "code").unique().height, "triples": s.height,
                     "share_pairs_any_insurer_above_cash": round(p_any, 4),
                     "pairs_ci_low": round(ci[0][0], 4) if ci else "", "pairs_ci_high": round(ci[0][1], 4) if ci else "",
                     "share_triples_above_cash": round(p_tri, 4),
                     "triples_ci_low": round(ci[1][0], 4) if ci else "",
                     "triples_ci_high": round(ci[1][1], 4) if ci else "",
                     "median_excess_dollars_when_above": round(above["rate_minus_cash"].median(), 2)
                     if above.height else "",
                     "median_excess_pct_of_cash_when_above":
                     round(float((above["rate_minus_cash"] / above["cash"]).median()), 4) if above.height else ""})

    add("main", "commercial + marketplace", t, cluster_ci(t, rng))
    add("sensitivity", "highest cash row", t_hi, cluster_ci(t_hi, rng))
    add("reference", "AHCCCS + Medicare Advantage + government", t_ref)
    for col in ("plan_type", "metro", "system", "canonical_payer"):
        for (v,), g in sorted(t.partition_by(col, as_dict=True).items()):
            add(col, v, g)
    for (v,), g in sorted(t.partition_by("code", as_dict=True).items()):
        add("procedure", f"{v} {procs.get(v, '')}", g)

    stamp = now_utc()
    src = "data/raw/normalized/<ccn>_f4.parquet"
    (t.with_columns(pl.col("code").replace_strict(procs, default="").alias("plain_name"),
                    pl.lit(src).alias("source_url"), pl.lit(stamp).alias("retrieved_at"))
     .sort("ccn", "code", "canonical_payer", "plan_type")
     .write_csv(PROCESSED / "cash_vs_insurance_triples.csv"))
    with open(PROCESSED / "cash_vs_insurance_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[*rows[0], "source_url", "retrieved_at"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "source_url": src, "retrieved_at": stamp})

    m = rows[0]
    print(f"hospitals {m['hospitals']}, pairs {m['pairs']}, triples {m['triples']}; "
          f"hospital-procedure keys with >1 distinct cash value: {multi_cash}")
    for r in rows:
        ci = (f" (95% CI {pct(r['pairs_ci_low'])}-{pct(r['pairs_ci_high'])};"
              f" triples CI {pct(r['triples_ci_low'])}-{pct(r['triples_ci_high'])})") if r["pairs_ci_low"] != "" else ""
        print(f"[{r['group']}] {r['value']}: h={r['hospitals']} pairs={r['pairs']} triples={r['triples']} "
              f"any-above={pct(r['share_pairs_any_insurer_above_cash'])} "
              f"triples-above={pct(r['share_triples_above_cash'])}{ci} "
              f"excess median ${r['median_excess_dollars_when_above']} "
              f"({r['median_excess_pct_of_cash_when_above']})")


if __name__ == "__main__":
    main()
