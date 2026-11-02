"""Build the advisor data pack (exports/advisor_pack/ and a dated zip) from committed CSVs and local parquet files.

Usage: python -m research.advisor_pack [--zip] [--no-samples] [--samples-only CCN ...]
       (--samples-only must come last; --zip writes exports/ClearTab_advisor_pack_<date>.zip)

Inputs: data/processed/*.csv (committed), data/raw/normalized/<ccn>_f4.parquet and the raw hospital files in
data/raw/ (local only). Raw hospital files are never copied into the pack; source_files.csv lists their URLs.
samples/: for each hospital, 50 raw records drawn with a fixed seed (reservoir sampling over the whole file, one
streaming pass), shown as column/value pairs, next to the normalized rows the pipeline stored for the same
records. The match re-parses each sampled record with pipeline.parsers.cms and joins on the parsed fields.
"""
import csv
import json
import random
import shutil
import sys
import zipfile
from pathlib import Path

import ijson
import polars as pl

from pipeline.common import PROCESSED, RAW, ROOT, now_utc
from pipeline.parsers.cms import ALLOWED_KEYS, Item, Profile, _codes, _emit, detect_format, norm_key
from pipeline.run import parse_date

PACK_DATE = "2026-10-16"
OUT = ROOT / "exports" / "advisor_pack"
ZIP = ROOT / "exports" / f"ClearTab_advisor_pack_{PACK_DATE}.zip"
SEED = 20261016
N_SAMPLE = 50
ITEM = ["code", "code_type", "setting", "billing_class", "modifiers", "description"]
H1_TABLES = ["h1_file_profile.csv", "h1_required_elements.csv", "h1_validator.csv", "downloads.csv",
             "code_frequency.csv", "procedure_selection.csv", "robots_snapshots.csv", "completeness_options.csv"]
H2_TABLES = ["h2_provisional_by_procedure.csv", "h2_payer_rule_by_procedure.csv", "f4_coverage.csv",
             "f4_flag_log.csv", "payer_strings.csv", "procedures.csv", "h2_followup_ratios.csv",
             "h2_followup_subsample.csv", "h2_followup_hospital_index.csv", "hospital_context.csv",
             "coverage_followup_hospitals.csv", "coverage_followup_summary.csv", "coverage_followup_strings.csv"]
H2_RESEARCH = ["irr_round1_rater_A.csv", "irr_round1_rater_B.csv", "irr_round1_score.txt", "labeling_guide.md",
               "advisor_followup.md", "coverage_followup.md", "fig_ratios_by_metro.svg", "fig_subsample.svg"]
H1_RESEARCH = ["completeness_options.md"]


def read(name: str) -> list[dict]:
    with open(PROCESSED / name, newline="") as f:
        return list(csv.DictReader(f))


def write(path: Path, rows: list[dict], cols: list[str] | None = None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = cols or (list(rows[0]) if rows else [])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def file_map() -> dict[str, dict]:
    """ccn -> download manifest row (path, url, sha256, retrieved_at) for the H1 sample files."""
    return {r["ccn"]: r for r in read("downloads.csv")}


# ---------------------------------------------------------------- tables

def hospitals_table(prof: dict[str, dict]) -> list[dict]:
    geo = {r["ccn"]: r for r in read("hospital_geo.csv")}
    out = []
    for r in read("hospital_registry.csv"):
        p, g = prof.get(r["ccn"], {}), geo.get(r["ccn"], {})
        out.append({
            "ccn": r["ccn"], "name": r["name"], "health_system": r["health_system"], "city": r["city"],
            "metro": r["metro"], "county": r["county"], "address": g.get("address", ""), "zip": g.get("zip", ""),
            "phone": g.get("phone", ""), "in_h1_sample": bool(p), "usable_coded_rows": p.get("usable_coded_rows", ""),
            "completeness_score": p.get("completeness_score", ""), "completeness_label": p.get("completeness_label", ""),
            "c1_file_found": p.get("c1_file_found", ""), "c2_schema_valid": p.get("c2_schema_valid", ""),
            "c3_coded_rows": p.get("c3_coded_rows", ""), "c4_dollar_or_allowed": p.get("c4_dollar_or_allowed", ""),
            "c5_2026_elements": p.get("c5_2026_elements", ""), "mrf_url": r["mrf_url"],
            "discovery_method": r["discovery_method"], "robots_blocks_mrf": r["robots_blocks_mrf"],
            "terms_restrict_reproduction": r["terms_restrict_reproduction"], "notes": r["notes"],
            "source_url": r["source_url"], "retrieved_at": r["retrieved_at"]})
    return out


def source_files_table(prof: dict[str, dict], files: dict[str, dict]) -> list[dict]:
    val = {r["ccn"]: r for r in read("h1_validator.csv")}
    out = []
    for ccn, p in prof.items():
        d, v = files.get(ccn, {}), val.get(ccn, {})
        url = d.get("url") or p["source_url"]
        out.append({
            "ccn": ccn, "hospital": p["hospital"], "url": url, "final_url": d.get("final_url", ""),
            "sha256": p["sha256"], "size_bytes": p["size_bytes"], "format": p["format"],
            "schema_version": p["schema_version"], "file_date": parse_date(p["file_last_updated"]) or "",
            "file_date_as_published": p["file_last_updated"], "http_last_modified": p["http_last_modified"],
            "validator_valid": v.get("valid", "not run (non-standard layout)"),
            "validator_errors": v.get("error_count", ""), "validator_warnings": v.get("alert_count", ""),
            "validator_top_errors": v.get("top_errors", ""), "validator_version": v.get("validator_version", ""),
            "data_dictionary_version": v.get("data_dictionary_version", ""), "download_note": d.get("note", ""),
            "source_url": url, "retrieved_at": p["retrieved_at"]})
    return out


def prices_table(prof: dict[str, dict], files: dict[str, dict]) -> pl.DataFrame:
    """Every normalized row for the 50 launch procedures (the same filter pipeline.run loads into prices)."""
    procs = {r["code"]: r["plain_name"] for r in read("procedures.csv")}
    frames = []
    for ccn, p in prof.items():
        path = RAW / "normalized" / f"{ccn}_f4.parquet"
        if not path.exists():
            continue
        d = files.get(ccn, {})
        frames.append(
            pl.scan_parquet(path)
            .filter(pl.col("code").is_in(list(procs)) & pl.col("code_type").is_in(["CPT", "HCPCS"]))
            .collect(engine="streaming")
            .with_columns(pl.lit(p["hospital"]).alias("hospital"), pl.lit(p["metro"]).alias("metro"),
                          pl.lit(p["health_system"]).alias("health_system"),
                          pl.col("code").replace_strict(procs).alias("procedure_name"),
                          pl.lit(d.get("url") or p["source_url"]).alias("source_url"),
                          pl.lit(parse_date(p["file_last_updated"]) or "").alias("file_date"),
                          pl.lit(p["retrieved_at"]).alias("retrieved_at")))
    df = pl.concat(frames, how="diagonal_relaxed")
    return (df.rename({"description": "description_in_file", "canonical_payer": "payer_canonical",
                       "payer_name": "raw_payer", "plan_name": "raw_plan", "methodology": "methodology_in_file",
                       "flags": "parser_flags", "gross_charge": "gross_charge_for_check"})
            .select("hospital", "ccn", "metro", "health_system", "code", "code_type", "procedure_name",
                    "description_in_file", "setting", "billing_class", "modifiers", "payer_canonical", "plan_type",
                    "raw_payer", "raw_plan", "price_type", "amount", "percentage", "algorithm",
                    "methodology_in_file", "methodology_label", "headline_ok", "drop_reason", "check_flag",
                    "parser_flags", "gross_charge_for_check", "source_url", "file_date", "retrieved_at")
            .sort("metro", "hospital", "code", "price_type", "raw_payer", "raw_plan", nulls_last=True))


# ---------------------------------------------------------------- samples

def reservoir(records, rng: random.Random, k: int) -> list:
    picked = []
    for i, rec in enumerate(records):
        if i < k:
            picked.append(rec)
        else:
            j = rng.randint(0, i)
            if j < k:
                picked[j] = rec
    return sorted(picked, key=lambda r: r[0])


def json_records(path: str):
    """(item index, charge index) records: one standard_charges entry with its item's description and codes."""
    with open(path, "rb") as f:
        for i, obj in enumerate(ijson.items(f, "standard_charge_information.item", use_float=True)):
            for j, sc in enumerate(obj.get("standard_charges") or []):
                yield f"{i}.{j}", {k: v for k, v in obj.items() if k != "standard_charges"}, sc


def csv_records(path: str, skip: int):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        head = [next(reader) for _ in range(skip)]
        for n, raw in enumerate(reader, start=skip + 1):
            if any(raw):
                yield n, head, raw


def flatten(prefix: str, v, out: list) -> None:
    if isinstance(v, dict):
        for k, x in v.items():
            flatten(f"{prefix}.{k}" if prefix else k, x, out)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            flatten(f"{prefix}[{i}]", x, out)
    elif v not in (None, ""):
        out.append((prefix, v))


def parse_json_record(ccn: str, obj: dict, sc: dict) -> list[dict]:
    """Same field mapping as pipeline.parsers.cms.iter_json, for one record."""
    codes = [(str(c.get("code", "")).strip(), str(c.get("type", "")).strip().upper())
             for c in obj.get("code_information") or []]
    payers = [{"payer_name": p.get("payer_name"), "plan_name": p.get("plan_name"),
               "dollar": p.get("standard_charge_dollar"), "percentage": p.get("standard_charge_percentage"),
               "algorithm": p.get("standard_charge_algorithm"), "methodology": p.get("methodology"),
               **{k: p[k] for k in ALLOWED_KEYS if k in p}} for p in sc.get("payers_information") or []]
    mods = sc.get("modifier_code") or obj.get("modifier_code") or ""
    item = Item(description=str(obj.get("description") or ""), codes=codes,
                setting=str(sc.get("setting") or "").lower(), billing_class=str(sc.get("billing_class") or "").lower(),
                modifiers="|".join(mods) if isinstance(mods, list) else str(mods),
                gross=sc.get("gross_charge"), cash=sc.get("discounted_cash"), payers=payers)
    return list(_emit(ccn, item, Profile(), None))


def parse_csv_record(ccn: str, cols: list[str], raw: list[str]) -> list[dict]:
    """Same field mapping as pipeline.parsers.cms.iter_csv (tall and wide), for one record."""
    keys = [norm_key(c) for c in cols]
    row = dict(zip(keys, raw, strict=False))
    item = Item(description=row.get("description", ""), codes=_codes(row),
                setting=(row.get("setting") or "").strip().lower(),
                billing_class=(row.get("billing_class") or "").strip().lower(),
                modifiers=(row.get("modifiers") or "").strip(),
                gross=row.get("standard_charge|gross"), cash=row.get("standard_charge|discounted_cash"))
    wide: dict[tuple[str, str], dict[str, int]] = {}
    for i, k in enumerate(keys):
        parts = k.split("|")
        rp = cols[i].replace("﻿", "").strip().split("|")
        rp = [x.strip() for x in rp]
        if parts[0] == "standard_charge" and len(parts) == 4:
            wide.setdefault((rp[1], rp[2]), {})[parts[3]] = i
        elif len(parts) == 3 and parts[0] in (*ALLOWED_KEYS, "estimated_amount", "additional_payer_notes"):
            wide.setdefault((rp[1], rp[2]), {})[parts[0]] = i
    if wide:
        for (payer, plan), idx in wide.items():
            p = {"payer_name": payer, "plan_name": plan}
            for src, dst in (("negotiated_dollar", "dollar"), ("negotiated_percentage", "percentage"),
                             ("negotiated_algorithm", "algorithm"), ("methodology", "methodology")):
                if src in idx:
                    p[dst] = raw[idx[src]] if idx[src] < len(raw) else ""
            for k in ALLOWED_KEYS:
                if k in idx:
                    p[k] = raw[idx[k]] if idx[k] < len(raw) else ""
            if any((p.get(x) or "").strip() for x in ("dollar", "percentage", "algorithm")):
                item.payers.append(p)
    elif (row.get("payer_name") or "").strip():
        p = {"payer_name": row.get("payer_name", "").strip(), "plan_name": row.get("plan_name", "").strip(),
             "dollar": row.get("standard_charge|negotiated_dollar"),
             "percentage": row.get("standard_charge|negotiated_percentage"),
             "algorithm": row.get("standard_charge|negotiated_algorithm"),
             "methodology": row.get("standard_charge|methodology")}
        for k in ALLOWED_KEYS:
            if k in row:
                p[k] = row[k]
        item.payers.append(p)
    return list(_emit(ccn, item, Profile(), None))


def sample_hospital(ccn: str, p: dict, path: str) -> dict:
    """Write samples/<ccn>_raw.csv and samples/<ccn>_normalized.csv; return a summary row."""
    rng = random.Random(f"{SEED}-{ccn}")
    fmt = detect_format(path)
    raw_rows, parsed = [], []
    if fmt == "json":
        picked = reservoir(json_records(path), rng, N_SAMPLE)
        for sid, (rec, obj, sc) in enumerate(picked, start=1):
            pairs: list = []
            flatten("", {**obj, "standard_charge": sc}, pairs)
            raw_rows += [{"sample_id": sid, "record": f"item {rec}", "column": c, "value": v} for c, v in pairs]
            parsed += [{**r, "sample_id": sid} for r in parse_json_record(ccn, obj, sc)]
    else:
        skip = 3 if fmt == "csv" else 1
        picked = reservoir(csv_records(path, skip), rng, N_SAMPLE)
        for sid, (line, head, raw) in enumerate(picked, start=1):
            cols = head[-1]
            raw_rows += [{"sample_id": sid, "record": f"line {line}", "column": cols[i] if i < len(cols) else f"col{i}",
                          "value": v} for i, v in enumerate(raw) if v.strip()]
            if fmt == "csv":
                parsed += [{**r, "sample_id": sid} for r in parse_csv_record(ccn, cols, raw)]
    write(OUT / "samples" / f"{ccn}_raw.csv", raw_rows, ["sample_id", "record", "column", "value"])
    norm_cols = ["sample_id", "ccn", "description", "code", "code_type", "setting", "billing_class", "modifiers",
                 "payer_name", "plan_name", "price_type", "amount", "percentage", "algorithm", "methodology",
                 "flags", "canonical_payer", "plan_type", "methodology_label", "headline_ok", "drop_reason",
                 "check_flag", "gross_charge", "found_in_pipeline_output"]
    f4p = RAW / "normalized" / f"{ccn}_f4.parquet"
    matched, n_parsed = [], len(parsed)
    if parsed and f4p.exists():
        key = ITEM + ["payer_name", "plan_name", "price_type", "amount", "percentage", "algorithm"]
        pdf = pl.DataFrame(parsed, infer_schema_length=None).with_columns(pl.col(ITEM).fill_null(""))
        f4 = (pl.scan_parquet(f4p).filter(pl.col("description").is_in(pdf["description"].unique().to_list()))
              .collect(engine="streaming").with_columns(pl.col(ITEM).fill_null("")).drop("_no_item_gross"))
        pdf = pdf.select([pl.col(c).cast(f4.schema[c]) for c in key] + [pl.col("sample_id")])
        # identical parsed rows (same item key and price) are stored once per occurrence; keep one of each
        j = pdf.unique().join(f4.unique(subset=key), on=key, how="left", nulls_equal=True)
        # every pipeline output row carries a methodology label, so a null label means "not found"
        matched = j.with_columns(pl.col("methodology_label").is_not_null().alias("found_in_pipeline_output"))
        matched = matched.sort("sample_id", "price_type", "payer_name", "plan_name", nulls_last=True).to_dicts()
    write(OUT / "samples" / f"{ccn}_normalized.csv", matched, norm_cols)
    found = sum(1 for r in matched if r["found_in_pipeline_output"])
    return {"ccn": ccn, "hospital": p["hospital"], "format": p["format"], "raw_records_sampled": len(picked),
            "parsed_rows": n_parsed, "normalized_rows_shown": len(matched), "found_in_pipeline_output": found,
            "seed": f"{SEED}-{ccn}", "raw_file_sha256": p["sha256"], "retrieved_at": now_utc()}


# ---------------------------------------------------------------- main

def main() -> None:
    args = sys.argv[1:]
    prof = {r["ccn"]: r for r in read("h1_file_profile.csv")}
    files = file_map()
    only = args[args.index("--samples-only") + 1:] if "--samples-only" in args else None
    if only is None:
        for old in OUT.glob("*") if OUT.exists() else []:   # samples/ is kept: the Mayo pass alone takes long
            if old.name != "samples":
                shutil.rmtree(old) if old.is_dir() else old.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "research" / "advisor_pack_README.md", OUT / "README.md")
        counts = {}
        counts["hospitals.csv"] = write(OUT / "hospitals.csv", hospitals_table(prof))
        counts["source_files.csv"] = write(OUT / "source_files.csv", source_files_table(prof, files))
        prices = prices_table(prof, files)
        prices.write_csv(OUT / "prices_launch_procedures.csv")
        counts["prices_launch_procedures.csv"] = prices.height
        shutil.copy(PROCESSED / "payer_aliases.csv", OUT / "payer_aliases.csv")
        counts["payer_aliases.csv"] = len(read("payer_aliases.csv"))
        for sub, names, base in (("h1_tables", H1_TABLES, PROCESSED), ("h2_tables", H2_TABLES, PROCESSED),
                                 ("h2_tables", H2_RESEARCH, ROOT / "research" / "h2"),
                                 ("h1_tables", H1_RESEARCH, ROOT / "research" / "h1")):
            (OUT / sub).mkdir(parents=True, exist_ok=True)
            for n in names:
                shutil.copy(base / n, OUT / sub / n)
        for n in ("REPORT.md",):
            shutil.copy(ROOT / "research" / "h1" / n, OUT / "h1_tables" / "H1_REPORT.md")
            shutil.copy(ROOT / "research" / "h2" / n, OUT / "h2_tables" / "H2_REPORT.md")
        (OUT / "counts.json").write_text(json.dumps(counts, indent=1))
    summary = []
    if "--no-samples" not in args:
        for ccn, p in prof.items():
            if only and ccn not in only:
                continue
            path = files.get(ccn, {}).get("path", "")
            if not path or not (ROOT / path).exists():
                summary.append({"ccn": ccn, "hospital": p["hospital"], "format": p["format"],
                                "raw_records_sampled": 0, "note": f"raw file not found locally ({path})"})
                continue
            row = sample_hospital(ccn, p, str(ROOT / path))
            print(row, flush=True)
            summary.append(row)
        old = []
        idx = OUT / "samples" / "index.csv"
        if only and idx.exists():
            with open(idx, newline="") as f:
                old = [r for r in csv.DictReader(f) if r["ccn"] not in only]
        write(idx, sorted(old + summary, key=lambda r: r["ccn"]),
              ["ccn", "hospital", "format", "raw_records_sampled", "parsed_rows", "normalized_rows_shown",
               "found_in_pipeline_output", "seed", "raw_file_sha256", "retrieved_at", "note"])
    if "--zip" in args:
        ZIP.unlink(missing_ok=True)
        with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for f in sorted(OUT.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(OUT.parent))
        print(f"{ZIP.relative_to(ROOT)}: {ZIP.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
