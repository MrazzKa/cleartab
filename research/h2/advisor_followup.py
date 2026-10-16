"""H2 follow-up for Dr. Li (2026-10-16): pooled primary with a bootstrap CI, per-metro results, hospital counts,
a Phoenix subsampling check, and an exploratory (descriptive) look at hospital-level factors.

Usage: python -m research.h2.advisor_followup
Inputs: data/raw/normalized/<ccn>_f4.parquet for the H1 sample hospitals only (data/processed/h1_file_profile.csv),
data/processed/hospital_context.csv (research/h2/fetch_context.py).
Outputs: data/processed/h2_followup_ratios.csv, h2_followup_subsample.csv, h2_followup_hospital_index.csv,
research/h2/fig_ratios_by_metro.svg, research/h2/fig_subsample.svg; numbers printed for advisor_followup.md.

Comparable rate and ratio: exactly as research/h2/h2_provisional.py (fixed dollar negotiated rate of a canonical
insurer, facility or blank billing class, outpatient or both, not dropped; ratio = highest / lowest hospital median
per procedure and metro, pairs with >= 2 hospitals). The script checks that it reproduces that file's ratios.
PROVISIONAL: the payer dictionary is not accepted yet (inter-rater round 2 pending).
"""
import csv

import numpy as np
import polars as pl

from pipeline.common import PROCESSED, RAW, ROOT, now_utc

SEED = 20261016
B_CI = 10_000          # bootstrap draws for confidence intervals (procedures resampled)
B_SUB = 1_000          # Phoenix subsampling draws (prompt: 1,000)
FIG = ROOT / "research" / "h2"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"   # categorical slots 1 and 2; neutral for reference marks


def load() -> tuple[pl.DataFrame, dict, dict]:
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
                    & pl.col("billing_class").is_in(["facility", ""]) & pl.col("setting").is_in(["outpatient", "both"])
                    & (pl.col("price_type") == "negotiated_dollar") & (pl.col("methodology_label") == "fixed dollar")
                    & (pl.col("canonical_payer") != "other") & pl.col("canonical_payer").is_not_null())
            .select("code", "amount", "canonical_payer")
            .with_columns(pl.lit(ccn).alias("ccn"), pl.lit(p["metro"]).alias("metro"),
                          pl.lit(p["health_system"]).alias("system"))
            .collect())
    return pl.concat(frames), prof, procs


def ci(values: np.ndarray) -> tuple[float, float]:
    lo, hi = np.percentile(values, [2.5, 97.5])
    return float(lo), float(hi)


def boot_median(groups: list[np.ndarray], rng: np.random.Generator, b: int) -> np.ndarray:
    """Median of all ratios in a resample of procedures (each procedure carries its 1 or 2 metro ratios)."""
    out = np.empty(b)
    n = len(groups)
    for i in range(b):
        pick = rng.integers(0, n, n)
        out[i] = np.median(np.concatenate([groups[j] for j in pick]))
    return out


# ---------------------------------------------------------------- SVG charts (no plotting library in the stack)

def _svg(w: int, h: int, body: list[str], title: str, desc: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'font-family="Helvetica, Arial, sans-serif"><title>{title}</title><desc>{desc}</desc>'
            f'<rect width="{w}" height="{h}" fill="#fcfcfb"/>' + "".join(body) + "</svg>")


def fig_ratios(rat: pl.DataFrame, procs: dict) -> str:
    wide = rat.pivot(on="metro", index="code", values="ratio")
    wide = wide.sort(pl.max_horizontal("Phoenix", "Tucson"), descending=True)
    left, top, row, pw = 300, 64, 14, 420
    h = top + row * wide.height + 56
    lo, hi = np.log10(1), np.log10(50)
    x = lambda v: left + (np.log10(v) - lo) / (hi - lo) * pw  # noqa: E731
    b = ['<text x="16" y="24" font-size="15" font-weight="600" fill="#0b0b0b">Highest-to-lowest price ratio per '
         'procedure, by metro</text>',
         '<text x="16" y="42" font-size="12" fill="#52514e">Hospital median fixed-dollar negotiated rates; log scale; '
         'PROVISIONAL payer dictionary</text>']
    for t in (1, 2, 5, 10, 20, 50):
        b.append(f'<line x1="{x(t):.1f}" y1="{top - 6}" x2="{x(t):.1f}" y2="{h - 48}" stroke="#e4e3df"/>'
                 f'<text x="{x(t):.1f}" y="{h - 32}" font-size="11" fill="#52514e" text-anchor="middle">{t}</text>')
    b.append(f'<line x1="{x(2):.1f}" y1="{top - 6}" x2="{x(2):.1f}" y2="{h - 48}" stroke="#52514e" '
             f'stroke-dasharray="4 3"/><text x="{x(2) + 4:.1f}" y="{top - 10}" font-size="11" fill="#52514e">'
             f'rule: 2</text>')
    for i, r in enumerate(wide.iter_rows(named=True)):
        y = top + i * row + row / 2
        b.append(f'<text x="{left - 8}" y="{y + 4:.1f}" font-size="11" fill="#0b0b0b" text-anchor="end">'
                 f'{procs[r["code"]][:42]} ({r["code"]})</text>')
        pts = [(r.get("Phoenix"), BLUE, "Phoenix"), (r.get("Tucson"), ORANGE, "Tucson")]
        if all(v is not None for v, _, _ in pts):
            b.append(f'<line x1="{x(pts[0][0]):.1f}" y1="{y:.1f}" x2="{x(pts[1][0]):.1f}" y2="{y:.1f}" '
                     f'stroke="#d3d2cc" stroke-width="2"/>')
        for v, c, m in pts:
            if v is not None:
                b.append(f'<circle cx="{x(v):.1f}" cy="{y:.1f}" r="4.5" fill="{c}" stroke="#fcfcfb" stroke-width="2">'
                         f'<title>{procs[r["code"]]} ({r["code"]}), {m}: {v:.2f}</title></circle>')
    ly = h - 14
    b.append(f'<circle cx="{left}" cy="{ly - 4}" r="4.5" fill="{BLUE}"/><text x="{left + 10}" y="{ly}" font-size="12" '
             f'fill="#0b0b0b">Phoenix</text><circle cx="{left + 90}" cy="{ly - 4}" r="4.5" fill="{ORANGE}"/>'
             f'<text x="{left + 100}" y="{ly}" font-size="12" fill="#0b0b0b">Tucson</text>')
    return _svg(left + pw + 40, h, b, "Price ratio per procedure by metro",
                "Dot plot of the highest-to-lowest hospital price ratio for each launch procedure, Phoenix and Tucson")


def fig_subsample(panels: list[tuple[str, np.ndarray, float, float, str]]) -> str:
    """Two stacked histograms on one x scale: Phoenix draws matched on hospital count, then on system count."""
    w, left, pw, ph, gap, top0 = 720, 60, 620, 130, 70, 66
    h = top0 + len(panels) * (ph + gap) + 10
    allv = np.concatenate([p[1] for p in panels])
    lo, hi = 1.0, max(3.2, float(allv.max()) + 0.1, max(p[3] for p in panels) + 0.2)
    x = lambda v: left + (v - lo) / (hi - lo) * pw  # noqa: E731
    b = ['<text x="16" y="24" font-size="15" font-weight="600" fill="#0b0b0b">Phoenix cut down to Tucson\'s size: '
         f'median ratio in {len(panels[0][1]):,} random draws</text>',
         '<text x="16" y="42" font-size="12" fill="#52514e">Same procedures in both metros; PROVISIONAL payer '
         'dictionary</text>']
    for p_i, (label, draws, ref, phx, level) in enumerate(panels):
        top = top0 + p_i * (ph + gap) + 18
        counts, edges = np.histogram(draws, bins=np.arange(lo, hi + 0.05, 0.05))
        ymax = counts.max()
        b.append(f'<text x="{left}" y="{top - 8}" font-size="12" font-weight="600" fill="#0b0b0b">{label}</text>')
        for c, e0, e1 in zip(counts, edges[:-1], edges[1:], strict=True):
            if c:
                bh = c / ymax * ph * 0.78   # headroom: the reference labels sit above the tallest bar
                b.append(f'<rect x="{x(e0) + 1:.1f}" y="{top + ph - bh:.1f}" width="{max(x(e1) - x(e0) - 2, 1):.1f}" '
                         f'height="{bh:.1f}" rx="2" fill="{GRAY}"><title>{e0:.2f}-{e1:.2f}: {c} draws</title></rect>')
        b.append(f'<line x1="{left}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}" stroke="#52514e"/>')
        for t in np.arange(lo, hi + 1e-9, 0.5):
            b.append(f'<text x="{x(t):.1f}" y="{top + ph + 16}" font-size="11" fill="#52514e" text-anchor="middle">'
                     f'{t:.1f}</text>')
        for v, c, lab, dy in ((ref, ORANGE, f"Tucson{level} {ref:.2f}", 0),
                              (phx, BLUE, f"Phoenix, all{level} {phx:.2f}", 0),
                              (2.0, "#52514e", "rule: 2", 0)):
            dash = ' stroke-dasharray="4 3"' if v == 2.0 else ""
            b.append(f'<line x1="{x(v):.1f}" y1="{top}" x2="{x(v):.1f}" y2="{top + ph}" stroke="{c}" '
                     f'stroke-width="2"{dash}/><text x="{x(v) + 4:.1f}" y="{top + 10 + dy}" font-size="11" '
                     f'fill="#0b0b0b" stroke="#fcfcfb" stroke-width="4" paint-order="stroke">{lab}</text>')
    b.append(f'<text x="{left + pw / 2}" y="{h - 8}" font-size="12" fill="#52514e" text-anchor="middle">median '
             'highest-to-lowest ratio across procedures</text>')
    return _svg(w, h, b, "Phoenix subsampling check",
                "Histograms of Phoenix median ratios when Phoenix is limited to Tucson's hospital count, and to "
                "Tucson's health system count, per procedure")


# ---------------------------------------------------------------- main

def main() -> None:
    rng = np.random.default_rng(SEED)
    neg, prof, procs = load()
    hosp = neg.group_by("code", "metro", "ccn", "system").agg(pl.col("amount").median().alias("med"))
    rat = (hosp.group_by("code", "metro").agg(pl.len().alias("hospitals"), pl.col("system").n_unique().alias("systems"),
                                              (pl.col("med").max() / pl.col("med").min()).alias("ratio"))
           .filter(pl.col("hospitals") >= 2).sort("metro", "code"))
    # reproduction check against the committed provisional file
    old = pl.read_csv(PROCESSED / "h2_provisional_by_procedure.csv", schema_overrides={"code": pl.Utf8})
    chk = rat.join(old.select("code", "metro", pl.col("ratio").alias("old")), on=["code", "metro"], how="full")
    assert chk.height == old.height == rat.height and (chk["ratio"] - chk["old"]).abs().max() < 1e-9, "not reproduced"

    print("== Hospitals with any comparable rate:", dict(neg.group_by("metro").agg(pl.col("ccn").n_unique()).iter_rows()),
          " systems:", dict(neg.group_by("metro").agg(pl.col("system").n_unique()).iter_rows()))
    for m in ("Phoenix", "Tucson"):
        s = rat.filter(pl.col("metro") == m)
        print(f"   {m}: procedures {s.height}; hospitals per procedure median {s['hospitals'].median()} "
              f"(min {s['hospitals'].min()}, max {s['hospitals'].max()}); systems per procedure median "
              f"{s['systems'].median()} (min {s['systems'].min()}, max {s['systems'].max()})")

    groups = [g["ratio"].to_numpy() for _, g in rat.group_by("code", maintain_order=True)]
    pooled = float(rat["ratio"].median())
    bp = boot_median(groups, rng, B_CI)
    print(f"== PRIMARY pooled median {pooled:.3f}, 95% CI {ci(bp)[0]:.2f}-{ci(bp)[1]:.2f} "
          f"(bootstrap {B_CI:,} draws resampling the {len(groups)} procedures); share of draws >= 2: {(bp >= 2).mean():.1%}")
    res = {"pooled": (pooled, *ci(bp), rat.height)}
    for m in ("Phoenix", "Tucson"):
        s = rat.filter(pl.col("metro") == m)["ratio"].to_numpy()
        bm = boot_median([np.array([v]) for v in s], rng, B_CI)
        res[m] = (float(np.median(s)), *ci(bm), len(s))
        print(f"   {m}: median {np.median(s):.3f}, 95% CI {ci(bm)[0]:.2f}-{ci(bm)[1]:.2f} (n={len(s)}); "
              f"ratio >= 2 in {(s >= 2).sum()} of {len(s)}; share of draws >= 2: {(bm >= 2).mean():.1%}")

    # subsampling: Phoenix limited to Tucson's hospital count per procedure, on the procedures both metros have
    both = rat.pivot(on="metro", index="code", values="hospitals").drop_nulls().sort("code")
    k = dict(zip(both["code"], both["Tucson"], strict=True))
    # sorted arrays: polars group order is not fixed, and the seeded draws must not depend on it
    phx = {c: np.sort(g["med"].to_numpy()) for (c,), g in hosp.filter(pl.col("metro") == "Phoenix").group_by("code")}
    draws = np.empty(B_SUB)
    for i in range(B_SUB):
        rs = []
        for c, n in k.items():
            pick = rng.choice(phx[c], size=min(n, len(phx[c])), replace=False)
            rs.append(pick.max() / pick.min())
        draws[i] = np.median(rs)
    tuc_matched = float(rat.filter((pl.col("metro") == "Tucson") & pl.col("code").is_in(list(k)))["ratio"].median())
    phx_matched = float(rat.filter((pl.col("metro") == "Phoenix") & pl.col("code").is_in(list(k)))["ratio"].median())
    print(f"== SUBSAMPLE on {len(k)} procedures in both metros: Phoenix all hospitals {phx_matched:.3f}; "
          f"Tucson {tuc_matched:.3f}; Phoenix with Tucson-sized sets: median of draws {np.median(draws):.3f}, "
          f"2.5-97.5% {ci(draws)[0]:.2f}-{ci(draws)[1]:.2f}, draws >= 2: {(draws >= 2).mean():.1%}, "
          f"draws <= Tucson: {(draws <= tuc_matched).mean():.1%}")
    print(f"   Tucson hospitals per procedure: {dict(zip(*np.unique(list(k.values()), return_counts=True), strict=True))}")

    # system-level check: one value per health system (median of its hospitals) before taking the ratio
    sysmed = hosp.group_by("code", "metro", "system").agg(pl.col("med").median().alias("med"))
    srat = (sysmed.group_by("code", "metro").agg(pl.len().alias("n"), (pl.col("med").max() / pl.col("med").min())
                                                 .alias("ratio")).filter(pl.col("n") >= 2))
    print("== SYSTEM LEVEL (one value per system):", {m: (round(float(g["ratio"].median()), 3), g.height)
                                                     for (m,), g in srat.group_by("metro")},
          "pooled", round(float(srat["ratio"].median()), 3), srat.height)
    # second check: also match the number of health systems (Tucson's 5 hospitals come from 3 systems)
    sk = dict(srat.filter(pl.col("metro") == "Tucson").sort("code").select("code", "n").iter_rows())
    psys = {c: np.sort(g["med"].to_numpy()) for (c,), g in sysmed.filter(pl.col("metro") == "Phoenix").group_by("code")}
    sdraws = np.empty(B_SUB)
    for i in range(B_SUB):
        rs = []
        for c, n in sk.items():
            pick = rng.choice(psys[c], size=min(n, len(psys[c])), replace=False)
            rs.append(pick.max() / pick.min())
        sdraws[i] = np.median(rs)
    print(f"== SYSTEM-MATCHED SUBSAMPLE ({len(sk)} procedures): Phoenix with Tucson's system count per procedure: "
          f"median of draws {np.median(sdraws):.3f}, 2.5-97.5% {ci(sdraws)[0]:.2f}-{ci(sdraws)[1]:.2f}, "
          f"draws >= 2: {(sdraws >= 2).mean():.1%}; Tucson system level "
          f"{float(srat.filter(pl.col('metro') == 'Tucson')['ratio'].median()):.3f}")

    # exploratory: hospital price index = median over procedures of hospital median / pooled median for the code
    code_med = hosp.group_by("code").agg(pl.col("med").median().alias("code_med"))
    idx = (hosp.join(code_med, on="code").with_columns((pl.col("med") / pl.col("code_med")).alias("rel"))
           .group_by("ccn", "metro", "system").agg(pl.col("rel").median().alias("price_index"),
                                                   pl.len().alias("procedures")))
    with open(PROCESSED / "hospital_context.csv", newline="") as f:
        ctx = pl.DataFrame(list(csv.DictReader(f))).select("ccn", "hospital", "hospital_ownership", "certified_beds",
                                                          "median_household_income", "pct_uninsured")
    idx = idx.join(ctx, on="ccn", how="left").sort("metro", "price_index")
    print("== HOSPITAL PRICE INDEX (1.00 = median hospital for the procedure, both metros)")
    for r in idx.iter_rows(named=True):
        print(f"   {r['metro']:8s} {r['hospital'][:42]:42s} {r['system'][:22]:22s} {r['hospital_ownership'][:28]:28s} "
              f"beds {r['certified_beds']:>4s} procs {r['procedures']:>2d} index {r['price_index']:.2f}")
    beds = idx.filter(pl.col("certified_beds").str.contains(r"^\d+$"))
    rho = np.corrcoef(beds["price_index"].rank().to_numpy(), beds["certified_beds"].cast(pl.Int64).rank().to_numpy())[0, 1]
    print(f"   Spearman rank correlation, price index vs certified beds: {rho:.2f} (n={beds.height}, descriptive only)")
    for m in ("Phoenix", "Tucson"):
        s = idx.filter(pl.col("metro") == m)["price_index"]
        print(f"   {m}: hospitals {s.len()}, index median {s.median():.2f}, min {s.min():.2f}, max {s.max():.2f}")

    ts = now_utc()
    src = "data/raw/normalized/<ccn>_f4.parquet (H1 sample)"
    rat.with_columns(pl.col("code").replace_strict(procs).alias("plain_name"), pl.lit(src).alias("source_url"),
                     pl.lit(ts).alias("retrieved_at")).write_csv(PROCESSED / "h2_followup_ratios.csv")
    pl.DataFrame({"draw": np.arange(1, B_SUB + 1), "phoenix_median_ratio_tucson_sized": draws,
                  "phoenix_median_ratio_tucson_system_count": sdraws}).with_columns(
        pl.lit(src).alias("source_url"), pl.lit(ts).alias("retrieved_at")).write_csv(PROCESSED / "h2_followup_subsample.csv")
    idx.with_columns(pl.lit(src + "; data/processed/hospital_context.csv").alias("source_url"),
                     pl.lit(ts).alias("retrieved_at")).write_csv(PROCESSED / "h2_followup_hospital_index.csv")
    (FIG / "fig_ratios_by_metro.svg").write_text(fig_ratios(rat, procs))
    tuc_sys = float(srat.filter(pl.col("metro") == "Tucson")["ratio"].median())
    phx_sys = float(srat.filter(pl.col("metro") == "Phoenix")["ratio"].median())
    (FIG / "fig_subsample.svg").write_text(fig_subsample(
        [("A. Same number of hospitals as Tucson, per procedure", draws, tuc_matched, phx_matched, ""),
         ("B. Same number of health systems as Tucson (one value per system), per procedure", sdraws, tuc_sys,
          phx_sys, " (system level)")]))
    print("written:", {k2: (round(v[0], 3), round(v[1], 2), round(v[2], 2), v[3]) for k2, v in res.items()})


if __name__ == "__main__":
    main()
