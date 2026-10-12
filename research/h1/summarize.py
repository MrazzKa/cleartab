"""Print the H1 numbers used in research/h1/REPORT.md from the committed CSVs."""
import pandas as pd

P = "data/processed/"
prof = pd.read_csv(P + "h1_file_profile.csv", dtype={"ccn": str})
elem = pd.read_csv(P + "h1_required_elements.csv", dtype={"ccn": str})

attempted = prof
usable = prof[prof.usable_coded_rows.astype(str) == "True"]
print(f"hospitals attempted: {len(attempted)} across {attempted.health_system.nunique()} systems")
print(f"usable coded rows: {len(usable)} of {len(attempted)} across {usable.health_system.nunique()} systems")
print("not usable:", "; ".join(f"{r.hospital} ({r.format})" for r in prof[~prof.index.isin(usable.index)].itertuples()))
parsed = prof[prof.format.str.startswith("CMS")]
print(f"CMS-template files parsed: {len(parsed)}; formats: {parsed.format.value_counts().to_dict()}")
print(f"validator valid: {(parsed.validator_valid.astype(str) == 'True').sum()} of {len(parsed)}")
print("score bands:", prof.completeness_label.value_counts().to_dict())
print("score >= 90:", (prof.completeness_score >= 90).sum(), " 80-89:", prof.completeness_score.between(80, 89.99).sum(),
      " 1-79:", prof.completeness_score.between(0.01, 79.99).sum(), " 0:", (prof.completeness_score == 0).sum())
e = elem[~elem.status.str.startswith("not applicable (no CMS")]
print(f"\n2026 elements over {e.ccn.nunique()} CMS-template files:")
for el, g in e.groupby("element", sort=False):
    print(f"  {el:22s}", g.status.value_counts().to_dict())
anymiss = e[e.status.isin(["missing", "present but empty"])].ccn.nunique()
print(f"files missing or empty on at least one applicable 2026 element: {anymiss} of {e.ccn.nunique()}")
neg = parsed[parsed.negotiated_records > 0]
print(f"\nfiles with any payer-specific negotiated rate: {len(neg)} of {len(parsed)}")
print("no negotiated rates:", ", ".join(parsed[parsed.negotiated_records == 0].hospital))
print("\npercent or algorithm records carrying a median allowed amount:")
for r in parsed[parsed.pct_algo_records > 0].itertuples():
    print(f"  {r.hospital:45s} {int(r.pct_algo_with_median):>6d} of {int(r.pct_algo_records):>6d} "
          f"({r.pct_algo_with_median / r.pct_algo_records:.1%})")
print("\nfile last_updated_on:", dict(zip(parsed.hospital, parsed.file_last_updated, strict=True)))
