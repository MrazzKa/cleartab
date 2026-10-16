"""Payer coverage with confidence intervals that respect clustering, and the Mayo sensitivity check (Dr. Li,
2026-10-14).

Usage: python -m research.h2.coverage_followup
Coverage (proposal Table 9) = share of priced negotiated rows (kept after the F4 outlier rules) whose payer maps to
one of the 11 canonical insurers. Same definition as data/processed/f4_coverage.csv; the script checks the totals.

- Overall (pooled): all rows of the included hospitals together (row-weighted; Mayo has 85% of all rows).
- Mean of per-hospital coverage: each hospital counts once (hospital-weighted).
- CIs: cluster bootstrap that resamples hospitals with replacement (2,000 draws, seed 20261016), recomputing both
  measures in each draw. Rows within a hospital are not independent (one payer string covers thousands of rows),
  so a row-level binomial CI would be far too narrow.
- Per hospital: point coverage, plus a descriptive interval that resamples the hospital's payer strings (each
  string with all its rows), 2,000 draws.
- Main analysis includes Mayo; the sensitivity analysis excludes it.
PROVISIONAL: the payer dictionary is not accepted yet (inter-rater round 2 pending).
Writes data/processed/coverage_followup_strings.csv and coverage_followup_summary.csv.
"""
import csv

import numpy as np
import polars as pl

from pipeline.common import PROCESSED, RAW, now_utc

SEED = 20261016
B = 2_000
MAYO = "030103"
TARGET = 0.60


def strings() -> pl.DataFrame:
    """Kept negotiated rows per hospital and payer string, and whether the string maps to a canonical insurer."""
    with open(PROCESSED / "h1_file_profile.csv", newline="") as f:
        prof = {r["ccn"]: r for r in csv.DictReader(f)}
    frames = []
    for ccn, p in prof.items():
        path = RAW / "normalized" / f"{ccn}_f4.parquet"
        if not path.exists():
            continue
        frames.append(
            pl.scan_parquet(path)
            .filter(pl.col("price_type").str.starts_with("negotiated") & pl.col("drop_reason").is_null())
            .group_by("payer_name", "plan_name", "canonical_payer")
            .agg(pl.len().alias("rows"))
            .collect(engine="streaming")
            .with_columns(pl.lit(ccn).alias("ccn"), pl.lit(p["hospital"]).alias("hospital"),
                          pl.lit(p["metro"]).alias("metro")))
    df = pl.concat(frames).with_columns((pl.col("canonical_payer") != "other").fill_null(False).alias("canonical"))
    return df.with_columns(pl.col("canonical").cast(pl.Int64) * pl.col("rows"))


def measures(n: np.ndarray, c: np.ndarray) -> tuple[float, float]:
    return float(c.sum() / n.sum()), float(np.mean(c / n))


def cluster_ci(n: np.ndarray, c: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    k = len(n)
    pooled, mean = np.empty(B), np.empty(B)
    for i in range(B):
        pick = rng.integers(0, k, k)
        pooled[i], mean[i] = measures(n[pick], c[pick])
    return pooled, mean


def pct(a: np.ndarray) -> str:
    lo, hi = np.percentile(a, [2.5, 97.5])
    return f"{lo:.1%} - {hi:.1%}"


def main() -> None:
    rng = np.random.default_rng(SEED)
    s = strings()
    hosp = (s.group_by("ccn", "hospital", "metro").agg(pl.col("rows").sum().alias("negotiated_rows"),
                                                       pl.col("canonical").sum().alias("canonical_rows"),
                                                       pl.len().alias("payer_strings"))
            .filter(pl.col("negotiated_rows") > 0).sort("ccn"))
    ref = pl.read_csv(PROCESSED / "f4_coverage.csv", schema_overrides={"ccn": pl.Utf8})
    chk = hosp.join(ref.select("ccn", pl.col("negotiated_rows").alias("n0"), pl.col("canonical_rows").alias("c0")),
                    on="ccn")
    assert chk.height == hosp.height and (chk["negotiated_rows"] == chk["n0"]).all() \
        and (chk["canonical_rows"] == chk["c0"]).all(), "does not match f4_coverage.csv"

    # per-hospital descriptive interval: resample payer strings within the hospital
    per = []
    for (ccn,), g in s.filter(pl.col("rows") > 0).sort("payer_name", "plan_name", nulls_last=True).group_by(
            "ccn", maintain_order=True):
        n, c = g["rows"].to_numpy(), g["canonical"].to_numpy()
        k = len(n)
        draws = np.array([c[p].sum() / n[p].sum() for p in (rng.integers(0, k, k) for _ in range(B))])
        lo, hi = np.percentile(draws, [2.5, 97.5])
        per.append({"ccn": ccn, "ci_low": float(lo), "ci_high": float(hi)})
    hosp = hosp.join(pl.DataFrame(per), on="ccn").with_columns(
        (pl.col("canonical_rows") / pl.col("negotiated_rows")).alias("coverage")).sort("coverage", descending=True)

    rows = []
    print("== per hospital (coverage, payer-string bootstrap interval, strings, rows)")
    for r in hosp.iter_rows(named=True):
        print(f"   {r['metro']:8s} {r['hospital'][:42]:42s} {r['coverage']:6.1%}  ({r['ci_low']:.1%} - {r['ci_high']:.1%})"
              f"  strings {r['payer_strings']:>5d}  rows {r['negotiated_rows']:>11,d}"
              f"  {'below 60%' if r['coverage'] < TARGET else ''}")
    for label, sub in (("main: all hospitals incl. Mayo", hosp),
                       ("sensitivity: Mayo excluded", hosp.filter(pl.col("ccn") != MAYO))):
        n, c = sub["negotiated_rows"].to_numpy(), sub["canonical_rows"].to_numpy()
        pooled, mean = measures(n, c)
        bp, bm = cluster_ci(n, c, rng)
        below = int((c / n < TARGET).sum())
        print(f"== {label}: hospitals {len(n)}; pooled {pooled:.1%} (95% CI {pct(bp)}),"
              f" P(pooled >= 60%) {np.mean(bp >= TARGET):.1%};"
              f" mean of hospitals {mean:.1%} (95% CI {pct(bm)}), P(mean >= 60%) {np.mean(bm >= TARGET):.1%};"
              f" hospitals below 60%: {below}")
        for m in ("Phoenix", "Tucson"):
            mm = sub.filter(pl.col("metro") == m)
            nn, cc = mm["negotiated_rows"].to_numpy(), mm["canonical_rows"].to_numpy()
            bpp, bmm = cluster_ci(nn, cc, rng)
            p2, m2 = measures(nn, cc)
            print(f"     {m}: hospitals {len(nn)}; pooled {p2:.1%} ({pct(bpp)}); mean {m2:.1%} ({pct(bmm)})")
            rows.append({"analysis": label, "group": m, "hospitals": len(nn), "pooled": p2,
                         "pooled_ci": pct(bpp), "mean_of_hospitals": m2, "mean_ci": pct(bmm)})
        rows.append({"analysis": label, "group": "both metros", "hospitals": len(n), "pooled": pooled,
                     "pooled_ci": pct(bp), "mean_of_hospitals": mean, "mean_ci": pct(bm),
                     "p_pooled_ge_60": float(np.mean(bp >= TARGET)), "p_mean_ge_60": float(np.mean(bm >= TARGET)),
                     "hospitals_below_60": below})
    ts, src = now_utc(), "data/raw/normalized/<ccn>_f4.parquet (H1 sample)"
    s.with_columns(pl.lit(src).alias("source_url"), pl.lit(ts).alias("retrieved_at")).write_csv(
        PROCESSED / "coverage_followup_strings.csv")
    pl.DataFrame(rows).with_columns(pl.lit(src).alias("source_url"), pl.lit(ts).alias("retrieved_at")).write_csv(
        PROCESSED / "coverage_followup_summary.csv")
    hosp.with_columns(pl.lit(src).alias("source_url"), pl.lit(ts).alias("retrieved_at")).write_csv(
        PROCESSED / "coverage_followup_hospitals.csv")


if __name__ == "__main__":
    main()
