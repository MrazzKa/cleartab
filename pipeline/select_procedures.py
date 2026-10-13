"""Phase 3: pick the 50 launch procedures (proposal Table 6) by how many sampled hospitals publish a price.

Rules (written before selection; a reviewer can change them here):
  Categories (Table 6): imaging, laboratory, endoscopy, common outpatient surgery, by CPT range below.
  Excluded: evaluation and management and psychotherapy (not in the four categories); obstetric delivery
  59000-59899; MS-DRG inpatient stays (not outpatient; still searchable, not in the launch list); oncology
  (proposal 6.2 item 5): 55866 radical prostatectomy, radiation oncology 77261-77799, nuclear therapy 79xxx;
  procedures limited to children (42820, under 12, outside the adult self-pay scope); codes whose most common
  setting in the files is inpatient; "unlisted procedure" codes (ending in 99); vascular access and blood
  draws 36000-36699 (ancillary to other care, not a service a patient shops for); 51798 (bladder volume
  measured by ultrasound: a measurement, not surgery, although its code is in the surgery range; added on
  2026-10-13 when the larger sample first made it eligible).
  Step A: every CMS-specified shoppable service (84 FR 65524 Table 3) in a category with >= 8 hospitals.
  Step B: fill category quotas (imaging 15, laboratory 15, endoscopy 8, outpatient surgery 12) with the
  non-CMS codes published by the most hospitals (>= 8). Ties: more hospitals publishing a cash price first
  (cash is a primary result, proposal 2.2), then more negotiated dollar rates.
  Step C: if a quota is still short, repeat A then B at >= 7, then >= 6 hospitals, and log it.
"""
import polars as pl

from pipeline.cms70 import CMS70, MS_DRG

QUOTA = {"imaging": 15, "laboratory": 15, "endoscopy": 8, "outpatient surgery": 12}
EXCLUDE = {"55866", "42820",
           "51798"}  # bladder volume by ultrasound: a measurement that sits in the surgery code range
THRESHOLDS = (8, 7, 6)


def category(code: str) -> str | None:
    if not code.isdigit() or len(code) != 5:
        return {"G0105": "endoscopy", "G0121": "endoscopy"}.get(code)
    n = int(code)
    if 70010 <= n <= 76999 or 77046 <= n <= 77067 or 78012 <= n <= 78999:
        return "imaging"
    if 80047 <= n <= 89398:
        return "laboratory"
    if (43180 <= n <= 43278 or 45300 <= n <= 45398 or 31615 <= n <= 31654 or 52000 <= n <= 52356
            or 44360 <= n <= 44408):
        return "endoscopy"
    if 10004 <= n <= 69990 and not 59000 <= n <= 59899:
        return "outpatient surgery"
    return None


def select(freq: pl.DataFrame) -> pl.DataFrame:
    cms = {c for v in CMS70.values() for c in v} - MS_DRG
    f = (freq.filter((pl.col("code_system") == "CPT/HCPCS") & ~pl.col("code").is_in(list(EXCLUDE))
                     & (pl.col("setting") != "inpatient") & ~pl.col("code").str.ends_with("99")
                     & ~pl.col("code").str.contains(r"^36[0-6]\d\d$"))
         .with_columns(pl.col("code").map_elements(category, return_dtype=pl.Utf8).alias("category"),
                       pl.col("code").is_in(list(cms)).alias("cms70"))
         .filter(pl.col("category").is_not_null()))
    picked = []
    for cat, quota in QUOTA.items():
        chosen: list[pl.DataFrame] = []
        n = 0
        for t in THRESHOLDS:
            pool = f.filter((pl.col("category") == cat) & (pl.col("hospitals") >= t))
            if chosen:
                pool = pool.join(pl.concat(chosen).select("code"), on="code", how="anti")
            for is_cms, label in ((True, "A: CMS shoppable"), (False, "B: most published")):
                if n >= quota:
                    break
                take = (pool.filter(pl.col("cms70") == is_cms)
                        .sort(["hospitals", "with_cash", "neg_dollar_rows"], descending=True).head(quota - n))
                if take.height:
                    step = label if t == THRESHOLDS[0] else f"C: {label[3:]} at >= {t} hospitals"
                    chosen.append(take.with_columns(pl.lit(step).alias("step")))
                    n += take.height
        picked.append(pl.concat(chosen))
    return pl.concat(picked)


if __name__ == "__main__":
    freq = pl.read_csv("data/processed/code_frequency.csv", schema_overrides={"code": pl.Utf8})
    out = select(freq)
    pl.Config.set_tbl_rows(60)
    pl.Config.set_fmt_str_lengths(40)
    pl.Config.set_tbl_width_chars(200)
    print(out.select("category", "step", "code", "hospitals", "with_cash", "with_neg_dollar", "setting", "short_desc"))
    print(out.group_by("category", "step").len().sort("category"))
    out.write_csv("data/processed/procedure_selection.csv")
