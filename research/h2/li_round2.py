"""Second follow-up for Dr. Li (meeting 2026-10-16): the four analyses he asked for.

1. H2 as estimates with 95% intervals and a reference line at 2 (pooled, Phoenix, Tucson, and the two Phoenix
   subsamples), instead of a yes/no.
2. Mayo Clinic compared with every other hospital: price index (hospital median / median hospital, per
   procedure) with a bootstrap interval, and payer coverage.
3. Sensitivity of the 60% payer coverage threshold from 30% to 90%.
4. Completeness score weights: 10,000 random weight sets (flat Dirichlet over the 5 components); how stable is
   each hospital's rank.

Same comparable-rate definition as research/h2/advisor_followup.py (pre-registered in research/h2/REPORT.md).
Seed 20261102. Usage: python -m research.h2.li_round2
Outputs: data/processed/li2_*.csv, research/h2/fig_li2_*.svg; numbers printed for research/h2/li_round2.md.
"""
import csv

import numpy as np
import polars as pl

from pipeline.common import PROCESSED, ROOT, now_utc
from research.h2.advisor_followup import boot_median, ci, load

SEED = 20261102
B = 10_000
B_SUB = 1_000
FIG = ROOT / "research" / "h2"
INK, MUTED, RULE, ACCENT, ORANGE = "#1d2a30", "#5b6b73", "#cfd8dc", "#2a78d6", "#eb6834"


def read_csv(path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def text(x: float, y: float, s: str, size: int = 11, fill: str = MUTED, anchor: str = "start", bold: bool = False) -> str:
    weight = ' font-weight="700"' if bold else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{weight}>'
            f'{s}</text>')


def svg(w: int, h: int, body: list[str], title: str, desc: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'font-family="Helvetica, Arial, sans-serif"><title>{title}</title><desc>{desc}</desc>'
            f'<rect width="{w}" height="{h}" fill="#fcfcfb"/>' + "".join(body) + "</svg>")


def forest(rows: list[tuple[str, float, float, float, str]], ref: float | None, lo_x: float, hi_x: float,
           title: str, desc: str, xlabel: str, highlight: str = "") -> str:
    left, top, rowh, pw = 330, 46, 30, 420
    h = top + rowh * len(rows) + 60
    x = lambda v: left + (v - lo_x) / (hi_x - lo_x) * pw  # noqa: E731
    body = [f'<text x="16" y="24" font-size="15" font-weight="700" fill="{INK}">{title}</text>']
    ticks = np.linspace(lo_x, hi_x, 6)
    for t in ticks:
        body.append(f'<line x1="{x(t):.1f}" y1="{top - 8}" x2="{x(t):.1f}" y2="{top + rowh * len(rows)}" stroke="{RULE}"/>'
                    f'<text x="{x(t):.1f}" y="{top + rowh * len(rows) + 18}" font-size="11" text-anchor="middle" '
                    f'fill="{MUTED}">{t:.2f}</text>')
    if ref is not None:
        body.append(f'<line x1="{x(ref):.1f}" y1="{top - 12}" x2="{x(ref):.1f}" y2="{top + rowh * len(rows)}" '
                    f'stroke="{ORANGE}" stroke-width="2" stroke-dasharray="5 4"/>'
                    f'<text x="{x(ref) + 4:.1f}" y="{top - 14}" font-size="11" fill="{ORANGE}">{ref:g}</text>')
    for i, (label, est, lo, hi, note) in enumerate(rows):
        y = top + rowh * i + rowh / 2
        col = ORANGE if highlight and highlight in label else ACCENT
        body.append(f'<text x="16" y="{y + 4:.1f}" font-size="12" fill="{INK}">{label}</text>'
                    f'<line x1="{x(lo):.1f}" y1="{y:.1f}" x2="{x(hi):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2.5"/>'
                    f'<circle cx="{x(est):.1f}" cy="{y:.1f}" r="5" fill="{col}"/>'
                    + text(left + pw + 12, y + 4, f"{est:.2f} ({lo:.2f}-{hi:.2f}){note}"))
    body.append(f'<text x="{left + pw / 2}" y="{h - 12}" font-size="11" text-anchor="middle" fill="{MUTED}">{xlabel}</text>')
    return svg(left + pw + 200, h, body, title, desc)


def main() -> None:
    rng = np.random.default_rng(SEED)
    stamp = now_utc()
    neg, prof, _procs = load()
    hosp = neg.group_by("code", "metro", "ccn", "system").agg(pl.col("amount").median().alias("med"))
    rat = (hosp.group_by("code", "metro").agg(pl.len().alias("hospitals"),
                                              (pl.col("med").max() / pl.col("med").min()).alias("ratio"))
           .filter(pl.col("hospitals") >= 2).sort("metro", "code"))

    # ---- 1. estimates with intervals
    groups = [np.sort(g["ratio"].to_numpy()) for _, g in rat.sort("code", "metro").group_by("code", maintain_order=True)]
    est = []
    bp = boot_median(groups, rng, B)
    est.append(("Pooled, both metros (pre-registered)", float(rat["ratio"].median()), *ci(bp), f"  n={rat.height}"))
    for m in ("Phoenix", "Tucson"):
        s = rat.filter(pl.col("metro") == m)["ratio"].to_numpy()
        bm = boot_median([np.array([v]) for v in np.sort(s)], rng, B)
        est.append((m, float(np.median(s)), *ci(bm), f"  n={len(s)}"))
    both = rat.pivot(on="metro", index="code", values="hospitals").drop_nulls().sort("code")
    k = dict(zip(both["code"], both["Tucson"], strict=True))
    phx = {c: np.sort(g["med"].to_numpy()) for (c,), g in hosp.filter(pl.col("metro") == "Phoenix").group_by("code")}
    draws = np.array([np.median([(p := rng.choice(phx[c], size=min(n, len(phx[c])), replace=False)).max() / p.min()
                                 for c, n in sorted(k.items())]) for _ in range(B_SUB)])
    est.append(("Phoenix, Tucson-sized hospital sets", float(np.median(draws)), *ci(draws), f"  {B_SUB:,} draws"))
    sysmed = hosp.group_by("code", "metro", "system").agg(pl.col("med").median().alias("med"))
    srat = (sysmed.group_by("code", "metro").agg(pl.len().alias("n"), (pl.col("med").max() / pl.col("med").min())
                                                 .alias("ratio")).filter(pl.col("n") >= 2))
    sk = dict(srat.filter(pl.col("metro") == "Tucson").sort("code").select("code", "n").iter_rows())
    psys = {c: np.sort(g["med"].to_numpy()) for (c,), g in sysmed.filter(pl.col("metro") == "Phoenix").group_by("code")}
    sdraws = np.array([np.median([(p := rng.choice(psys[c], size=min(n, len(psys[c])), replace=False)).max() / p.min()
                                  for c, n in sorted(sk.items()) if c in psys]) for _ in range(B_SUB)])
    est.append(("Phoenix, Tucson's number of systems", float(np.median(sdraws)), *ci(sdraws), f"  {B_SUB:,} draws"))
    for e in est:
        print(f"[1] {e[0]}: {e[1]:.2f} (95% {e[2]:.2f}-{e[3]:.2f}){e[4]}")
    (FIG / "fig_li2_h2_intervals.svg").write_text(forest(
        est, 2.0, 1.0, 4.0, "Highest-to-lowest price ratio, median across procedures",
        "H2 estimates with 95% intervals; dashed line at the pre-registered threshold of 2",
        "median ratio (95% interval: bootstrap over procedures, or 2.5-97.5% of subsampling draws)"))
    with open(PROCESSED / "li2_h2_intervals.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["estimate", "median", "ci_low", "ci_high", "note", "source_url", "retrieved_at"])
        for e in est:
            w.writerow([e[0], round(e[1], 4), round(e[2], 4), round(e[3], 4), e[4].strip(),
                        "data/raw/normalized/<ccn>_f4.parquet (H1 sample)", stamp])

    # ---- 2. Mayo vs every other hospital: price index with bootstrap over procedures
    code_med = hosp.group_by("code").agg(pl.col("med").median().alias("code_med"))
    rel = hosp.join(code_med, on="code").with_columns((pl.col("med") / pl.col("code_med")).alias("rel"))
    names = {c: p["hospital"] for c, p in prof.items()}
    idx = []
    for (ccn,), g in sorted(rel.group_by("ccn"), key=lambda t: t[0][0]):
        v = np.sort(g["rel"].to_numpy())
        bi = np.array([np.median(rng.choice(v, len(v))) for _ in range(2000)])
        idx.append((f"{names[ccn][:40]}", float(np.median(v)), *ci(bi), f"  n={len(v)}", ccn, g["system"][0]))
    idx.sort(key=lambda r: r[1])
    mayo = next(r for r in idx if r[5] == "030103")
    others = [r for r in idx if r[5] != "030103"]
    above = sum(1 for r in others if r[3] < mayo[2])      # others entirely below Mayo's interval
    print(f"[2] Mayo price index {mayo[1]:.2f} ({mayo[2]:.2f}-{mayo[3]:.2f}), procedures {mayo[4].strip()}; "
          f"rank {idx.index(mayo) + 1} of {len(idx)}; hospitals whose interval lies entirely below Mayo's: {above}")
    # Mayo vs pooled others, per procedure (paired): Mayo median / median of the other hospitals' medians
    m_rows = []
    for _, g in hosp.group_by("code"):
        mv = g.filter(pl.col("ccn") == "030103")["med"]
        ov = g.filter(pl.col("ccn") != "030103")["med"]
        if mv.len() and ov.len():
            m_rows.append(float(mv[0] / ov.median()))
    m_rows = np.sort(np.array(m_rows))
    bm = np.array([np.median(rng.choice(m_rows, len(m_rows))) for _ in range(B)])
    print(f"[2] Mayo vs the median of all other hospitals, per procedure: median ratio {np.median(m_rows):.2f} "
          f"(95% {ci(bm)[0]:.2f}-{ci(bm)[1]:.2f}), {len(m_rows)} procedures, Mayo higher in {(m_rows > 1).sum()}")
    (FIG / "fig_li2_mayo_index.svg").write_text(forest(
        [(r[0], r[1], r[2], r[3], r[4]) for r in idx], 1.0, 0.0, 2.5,
        "Hospital price index (1.00 = median hospital for the procedure)",
        "Each hospital's median relative price with a bootstrap interval; Mayo highlighted",
        "price index (95% interval: bootstrap over procedures)", highlight="Mayo"))
    with open(PROCESSED / "li2_price_index.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ccn", "hospital", "system", "price_index", "ci_low", "ci_high", "procedures", "source_url",
                    "retrieved_at"])
        for r in idx:
            w.writerow([r[5], r[0], r[6], round(r[1], 4), round(r[2], 4), round(r[3], 4), r[4].strip()[2:],
                        "data/raw/normalized/<ccn>_f4.parquet (H1 sample)", stamp])
    cov = read_csv(PROCESSED / "coverage_followup_hospitals.csv")
    mc = next(r for r in cov if r["ccn"] == "030103")
    oc = np.array([float(r["coverage"]) for r in cov if r["ccn"] != "030103"])
    tot = sum(int(r["negotiated_rows"]) for r in cov)
    print(f"[2] Mayo payer coverage {float(mc['coverage']):.1%} on {int(mc['negotiated_rows']):,} rows "
          f"({int(mc['negotiated_rows']) / tot:.0%} of all negotiated rows); other hospitals median {np.median(oc):.1%} "
          f"(min {oc.min():.1%}, max {oc.max():.1%})")

    # ---- 3. coverage threshold 30-90%
    th_rows = []
    pooled_all = sum(int(r["canonical_rows"]) for r in cov) / tot
    no_mayo = [r for r in cov if r["ccn"] != "030103"]
    pooled_nm = sum(int(r["canonical_rows"]) for r in no_mayo) / sum(int(r["negotiated_rows"]) for r in no_mayo)
    covs = np.array([float(r["coverage"]) for r in cov])
    for t in range(30, 91, 5):
        th_rows.append((t, int((covs >= t / 100).sum()), len(covs), pooled_all >= t / 100, pooled_nm >= t / 100,
                        float(covs.mean()) >= t / 100))
    print("[3] threshold: hospitals passing (of 14), pooled with Mayo passes, pooled without Mayo passes, mean passes")
    for r in th_rows:
        print(f"    {r[0]}%: {r[1]}/{r[2]}  pooled {r[3]}  without Mayo {r[4]}  mean {r[5]}")
    with open(PROCESSED / "li2_coverage_threshold.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold_pct", "hospitals_passing", "hospitals", "pooled_with_mayo_passes",
                    "pooled_without_mayo_passes", "mean_of_hospitals_passes", "source_url", "retrieved_at"])
        for r in th_rows:
            w.writerow([*r, "data/processed/coverage_followup_hospitals.csv", stamp])
    left, top, pw, ph = 60, 40, 520, 220
    x = lambda t: left + (t - 30) / 60 * pw  # noqa: E731
    y = lambda n: top + ph - n / 14 * ph  # noqa: E731
    body = [text(16, 22, "Hospitals at or above the payer coverage threshold", 15, INK, bold=True)]
    for n in range(0, 15, 2):
        body.append(f'<line x1="{left}" y1="{y(n):.1f}" x2="{left + pw}" y2="{y(n):.1f}" stroke="{RULE}"/>'
                    f'<text x="{left - 8}" y="{y(n) + 4:.1f}" font-size="11" text-anchor="end" fill="{MUTED}">{n}</text>')
    for t in range(30, 91, 10):
        body.append(text(x(t), top + ph + 18, f"{t}%", anchor="middle"))
    pts = " ".join(f"{x(r[0]):.1f},{y(r[1]):.1f}" for r in th_rows)
    body.append(f'<polyline points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>')
    body += [f'<circle cx="{x(r[0]):.1f}" cy="{y(r[1]):.1f}" r="3.5" fill="{ACCENT}"/>' for r in th_rows]
    body.append(f'<line x1="{x(60):.1f}" y1="{top}" x2="{x(60):.1f}" y2="{top + ph}" stroke="{ORANGE}" '
                f'stroke-dasharray="5 4" stroke-width="2"/>'
                + text(x(60) + 4, top + 12, "60% (proposal)", fill=ORANGE)
                + text(left + pw / 2, top + ph + 38,
                       "threshold: share of a hospital's negotiated rows mapped to a named insurer", anchor="middle"))
    (FIG / "fig_li2_coverage_threshold.svg").write_text(svg(left + pw + 30, top + ph + 52, body,
        "Payer coverage threshold sensitivity", "Number of the 14 hospitals passing each threshold from 30% to 90%"))

    # ---- 4. random weights for the completeness score
    comp = read_csv(PROCESSED / "completeness_options.csv")
    comp = [r for r in comp if r["ccn"] != "030108"] + [r for r in comp if r["ccn"] == "030108"]
    X = np.array([[float(r[f"c{i}"]) / 20 for i in range(1, 6)] for r in comp])      # each component 0-1
    W = rng.dirichlet(np.ones(5), size=B) * 100
    S = X @ W.T                                                                        # hospitals x draws
    ranks = (-S).argsort(axis=0).argsort(axis=0) + 1
    eq = X @ np.full(5, 20.0)
    eq_rank = (-eq).argsort().argsort() + 1
    n = len(comp)
    w_rows = []
    for i, r in enumerate(comp):
        rk = ranks[i]
        w_rows.append((r["hospital"], r["metro"], round(float(eq[i]), 1), int(eq_rank[i]), int(np.median(rk)),
                       int(np.percentile(rk, 5)), int(np.percentile(rk, 95)), round(float((rk <= 5).mean()), 3),
                       round(float((rk > n - 5).mean()), 3)))
    w_rows.sort(key=lambda t: t[4])
    print("[4] random weights: hospital, equal-weight score, equal rank, median rank, 5-95% rank, P(top 5), P(bottom 5)")
    for r in w_rows:
        print(f"    {r[0][:40]:40s} {r[2]:5.1f}  {r[3]:2d}  {r[4]:2d}  {r[5]:2d}-{r[6]:2d}  {r[7]:.2f}  {r[8]:.2f}")
    taus = []
    for j in range(0, B, 10):
        a, b = eq_rank, ranks[:, j]
        conc = sum(np.sign(a[p] - a[q]) * np.sign(b[p] - b[q]) for p in range(n) for q in range(p + 1, n))
        taus.append(conc / (n * (n - 1) / 2))
    print(f"[4] Kendall tau between equal-weight ranking and random-weight rankings ({len(taus):,} draws): median "
          f"{np.median(taus):.2f}, 5th percentile {np.percentile(taus, 5):.2f}")
    with open(PROCESSED / "li2_weights_rank_stability.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hospital", "metro", "equal_weight_score", "equal_weight_rank", "median_rank", "rank_p5",
                    "rank_p95", "share_top5", "share_bottom5", "source_url", "retrieved_at"])
        for r in w_rows:
            w.writerow([*r, "data/processed/completeness_options.csv", stamp])


if __name__ == "__main__":
    main()
