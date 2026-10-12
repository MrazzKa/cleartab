"""Streaming parser for CMS hospital price transparency files (template v2.x/v3.x, JSON, CSV tall, CSV wide).

Every supported file becomes one normalized long table: one row per hospital, code, setting, payer, plan and
price type. Nothing is loaded whole: JSON is read with ijson, CSV with the csv module line by line.

price_type values: gross, cash, negotiated_dollar, negotiated_percent, negotiated_algorithm,
allowed_median, allowed_p10, allowed_p90, allowed_count.
Bad values are never fixed here: an amount that cannot be parsed becomes None with a flag.
"""
import csv
import io
import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

import ijson

USABLE_CODE_TYPES = {"CPT", "HCPCS", "MS-DRG"}
ALLOWED_KEYS = {"median_amount": "allowed_median", "10th_percentile": "allowed_p10",
                "90th_percentile": "allowed_p90", "count": "allowed_count"}
ELEMENTS_2026 = ["org_npi", "attester_name", "attestation_statement", "median_amount", "10th_percentile",
                 "90th_percentile", "count"]
ATTESTATION_PREFIX = "to the best of its knowledge"
csv.field_size_limit(1 << 30)


def norm_key(name: str) -> str:
    """Header names vary in case, spacing and BOMs ("standard_charge | methodology")."""
    return re.sub(r"\s*\|\s*", "|", (name or "").replace("\ufeff", "").strip()).lower()


def parse_amount(value) -> tuple[float | None, bool]:
    """Return (number, ok). Empty is (None, True); garbage is (None, False)."""
    if value is None:
        return None, True
    if isinstance(value, int | float):
        return float(value), True
    s = str(value).strip().replace(",", "").replace("$", "")
    if not s:
        return None, True
    try:
        return float(s), True
    except ValueError:
        return None, False


@dataclass
class Item:
    description: str
    codes: list[tuple[str, str]]          # (code, type)
    setting: str
    billing_class: str
    modifiers: str
    gross: object = None
    cash: object = None
    payers: list[dict] = field(default_factory=list)


@dataclass
class Profile:
    """Per-file counters filled while streaming."""
    format: str = ""
    schema_version: str = ""
    last_updated_on: str = ""
    hospital_name: str = ""
    org_npi: str = ""
    attester_name: str = ""
    attestation_statement: str = ""     # present | missing | present but empty
    attestation_confirmed: str = ""
    source_items: int = 0
    rows: int = 0
    usable_rows: int = 0
    priced_usable_rows: int = 0
    codes: dict = field(default_factory=lambda: defaultdict(set))
    negotiated: Counter = field(default_factory=Counter)        # dollar | percent | algorithm | none
    pct_algo_with_median: int = 0
    pct_algo_total: int = 0
    element_seen: Counter = field(default_factory=Counter)      # key present in structure or header
    element_filled: Counter = field(default_factory=Counter)    # key carries a non-empty value
    flags: Counter = field(default_factory=Counter)
    payer_strings: Counter = field(default_factory=Counter)

    def element_status(self, key: str) -> str:
        if key in ("org_npi", "attester_name"):
            v = getattr(self, key)
            return "present" if v else ("present but empty" if self.element_seen[key] else "missing")
        if key == "attestation_statement":
            return self.attestation_statement or "missing"
        if not self.element_seen[key]:
            # JSON omits allowed-amount keys entirely; they are only required for percent or algorithm rates.
            return "not applicable (no percent or algorithm rates)" if self.pct_algo_total == 0 else "missing"
        if self.element_filled[key]:
            return "present"
        if self.pct_algo_total == 0:
            return "not applicable (column present but empty; no percent or algorithm rates)"
        return "present but empty"


def _emit(ccn: str, item: Item, prof: Profile, seen_base: set | None) -> Iterator[dict]:
    usable = [(c, t) for c, t in item.codes if t in USABLE_CODE_TYPES and c]
    targets = usable or [item.codes[0] if item.codes else ("", "")]
    is_usable = bool(usable)
    for code, ctype in targets:
        base = {"ccn": ccn, "description": item.description, "code": code, "code_type": ctype,
                "setting": item.setting, "billing_class": item.billing_class, "modifiers": item.modifiers,
                "usable_code": is_usable}
        if is_usable:
            prof.codes[ctype].add(code)
        else:
            prof.codes[f"(not usable) {ctype or 'none'}"].add(code)
        rows = []
        key = (code, ctype, item.setting, item.billing_class, item.modifiers, item.description)
        if seen_base is None or hash(key) not in seen_base:
            if seen_base is not None:
                seen_base.add(hash(key))
            for ptype, raw in (("gross", item.gross), ("cash", item.cash)):
                amt, ok = parse_amount(raw)
                if amt is not None or not ok:
                    rows.append({"price_type": ptype, "amount": amt, "flags": "" if ok else "unparseable_amount"})
        for p in item.payers:
            payer, plan = p.get("payer_name") or "", p.get("plan_name") or ""
            prof.payer_strings[(payer, plan)] += 1
            meth = (p.get("methodology") or "").strip().lower()
            d, d_ok = parse_amount(p.get("dollar"))
            pc, pc_ok = parse_amount(p.get("percentage"))
            algo = (p.get("algorithm") or "").strip()
            common = {"payer_name": payer, "plan_name": plan, "methodology": meth}
            if d is not None or not d_ok:
                rows.append({**common, "price_type": "negotiated_dollar", "amount": d,
                             "flags": "" if d_ok else "unparseable_amount"})
            if pc is not None or not pc_ok:
                rows.append({**common, "price_type": "negotiated_percent", "percentage": pc,
                             "flags": "" if pc_ok else "unparseable_percentage"})
            if algo:
                rows.append({**common, "price_type": "negotiated_algorithm", "algorithm": algo[:2000]})
            kind = "dollar" if d is not None else "percent" if pc is not None else "algorithm" if algo else "none"
            prof.negotiated[kind] += 1
            has_median = False
            for src, ptype in ALLOWED_KEYS.items():
                if src in p:
                    prof.element_seen[src] += 1
                v, ok = parse_amount(p.get(src))
                flag = "" if ok else "unparseable_amount"
                if src == "count" and str(p.get(src)).strip().lower() == "1 through 10":
                    flag = "count_1_through_10"   # CMS-permitted range for small counts, not an error
                if v is not None or not ok:
                    prof.element_filled[src] += 1
                    has_median |= src == "median_amount" and v is not None
                    rows.append({**common, "price_type": ptype, "amount": v, "flags": flag})
            if kind in ("percent", "algorithm"):
                prof.pct_algo_total += 1
                prof.pct_algo_with_median += has_median
        for r in rows:
            out = {**base, "payer_name": None, "plan_name": None, "amount": None, "percentage": None,
                   "algorithm": None, "methodology": None, "flags": "", **r}
            prof.rows += 1
            if is_usable:
                prof.usable_rows += 1
                if out["amount"] is not None or out["percentage"] is not None:
                    prof.priced_usable_rows += 1
            if out["flags"]:
                prof.flags[out["flags"]] += 1
            yield out


# ---------------------------------------------------------------- JSON

def _json_header(path: str, prof: Profile) -> None:
    """First pass: top-level metadata, skipping the large arrays."""
    skip = ("standard_charge_information", "modifier_information")
    meta: dict = {}
    with open(path, "rb") as f:
        for prefix, event, value in ijson.parse(f, use_float=True):
            if prefix.startswith(skip):
                continue
            if event in ("string", "number", "boolean", "null") and prefix:
                meta.setdefault(prefix, []).append(value)
    prof.hospital_name = str((meta.get("hospital_name") or [""])[0])
    prof.last_updated_on = str((meta.get("last_updated_on") or [""])[0])
    prof.schema_version = str((meta.get("version") or [""])[0])
    npis = meta.get("type_2_npi.item") or meta.get("type_2_npi") or []
    prof.element_seen["org_npi"] = int(any(k.startswith("type_2_npi") for k in meta))
    prof.org_npi = "|".join(str(n) for n in npis if n)
    att = (meta.get("attestation.attestation") or [None])[0]
    prof.attestation_statement = ("present" if att else "present but empty") if "attestation.attestation" in meta \
        else "missing"
    prof.attestation_confirmed = str((meta.get("attestation.confirm_attestation") or [""])[0])
    prof.element_seen["attester_name"] = int("attestation.attester_name" in meta)
    prof.attester_name = str((meta.get("attestation.attester_name") or [""])[0] or "")


def iter_json(path: str, ccn: str, prof: Profile) -> Iterator[dict]:
    prof.format = "CMS JSON"
    _json_header(path, prof)
    with open(path, "rb") as f:
        for obj in ijson.items(f, "standard_charge_information.item", use_float=True):
            codes = [(str(c.get("code", "")).strip(), str(c.get("type", "")).strip().upper())
                     for c in obj.get("code_information") or []]
            for sc in obj.get("standard_charges") or []:
                prof.source_items += 1
                payers = [{"payer_name": p.get("payer_name"), "plan_name": p.get("plan_name"),
                           "dollar": p.get("standard_charge_dollar"),
                           "percentage": p.get("standard_charge_percentage"),
                           "algorithm": p.get("standard_charge_algorithm"), "methodology": p.get("methodology"),
                           **{k: p[k] for k in ALLOWED_KEYS if k in p}}
                          for p in sc.get("payers_information") or []]
                mods = sc.get("modifier_code") or obj.get("modifier_code") or ""
                item = Item(description=str(obj.get("description") or ""), codes=codes,
                            setting=str(sc.get("setting") or "").lower(),
                            billing_class=str(sc.get("billing_class") or "").lower(),
                            modifiers="|".join(mods) if isinstance(mods, list) else str(mods),
                            gross=sc.get("gross_charge"), cash=sc.get("discounted_cash"), payers=payers)
                yield from _emit(ccn, item, prof, None)


# ---------------------------------------------------------------- CSV

def _csv_meta(head: list[str], values: list[str], prof: Profile) -> None:
    keys = [norm_key(h) for h in head]
    meta = dict(zip(keys, values, strict=False))
    prof.hospital_name = meta.get("hospital_name", "")
    prof.last_updated_on = meta.get("last_updated_on", "")
    prof.schema_version = meta.get("version", "")
    prof.element_seen["org_npi"] = int("type_2_npi" in meta)
    prof.org_npi = (meta.get("type_2_npi") or "").strip()
    prof.element_seen["attester_name"] = int("attester_name" in meta)
    prof.attester_name = (meta.get("attester_name") or "").strip()
    att = [k for k in keys if k.startswith(ATTESTATION_PREFIX)]
    if att:
        prof.attestation_statement = "present"
        prof.attestation_confirmed = (meta.get(att[0]) or "").strip()
    else:
        prof.attestation_statement = "missing"


def _codes(row: dict) -> list[tuple[str, str]]:
    out = []
    for i in range(1, 20):
        c = row.get(f"code|{i}")
        if c is None:
            break
        t = (row.get(f"code|{i}|type") or "").strip().upper()
        if c.strip():
            out.append((c.strip(), t))
    return out


def iter_csv(path: str, ccn: str, prof: Profile) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        head, values, cols = next(reader), next(reader), next(reader)
        _csv_meta(head, values, prof)
        keys = [norm_key(c) for c in cols]
        wide_payers: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
        for i, k in enumerate(keys):
            parts = k.split("|")
            raw_parts = re.sub(r"\s*\|\s*", "|", cols[i].replace("\ufeff", "").strip()).split("|")
            if parts[0] == "standard_charge" and len(parts) == 4:
                wide_payers[(raw_parts[1], raw_parts[2])][parts[3]] = i
            elif len(parts) == 3 and parts[0] in (*ALLOWED_KEYS, "estimated_amount", "additional_payer_notes"):
                wide_payers[(raw_parts[1], raw_parts[2])][parts[0]] = i
        wide = bool(wide_payers)
        prof.format = "CMS CSV wide" if wide else "CMS CSV tall"
        if not wide:
            for k in ALLOWED_KEYS:
                if k in keys:
                    prof.element_seen[k] = 1
        seen_base: set = set()
        for raw in reader:
            if not any(raw):
                continue
            prof.source_items += 1
            row = dict(zip(keys, raw, strict=False))
            item = Item(description=row.get("description", ""), codes=_codes(row),
                        setting=(row.get("setting") or "").strip().lower(),
                        billing_class=(row.get("billing_class") or "").strip().lower(),
                        modifiers=(row.get("modifiers") or "").strip(),
                        gross=row.get("standard_charge|gross"), cash=row.get("standard_charge|discounted_cash"))
            if wide:
                for (payer, plan), idx in wide_payers.items():
                    p = {"payer_name": payer, "plan_name": plan}
                    for src, dst in (("negotiated_dollar", "dollar"), ("negotiated_percentage", "percentage"),
                                     ("negotiated_algorithm", "algorithm"), ("methodology", "methodology")):
                        if src in idx:
                            p[dst] = raw[idx[src]] if idx[src] < len(raw) else ""
                    for k in ALLOWED_KEYS:
                        if k in idx:
                            prof.element_seen[k] = 1
                            p[k] = raw[idx[k]] if idx[k] < len(raw) else ""
                    if any((p.get(x) or "").strip() for x in ("dollar", "percentage", "algorithm")):
                        item.payers.append(p)
                yield from _emit(ccn, item, prof, None)
            else:
                if (row.get("payer_name") or "").strip():
                    p = {"payer_name": row.get("payer_name", "").strip(), "plan_name": row.get("plan_name", "").strip(),
                         "dollar": row.get("standard_charge|negotiated_dollar"),
                         "percentage": row.get("standard_charge|negotiated_percentage"),
                         "algorithm": row.get("standard_charge|negotiated_algorithm"),
                         "methodology": row.get("standard_charge|methodology")}
                    for k in ALLOWED_KEYS:
                        if k in row:
                            p[k] = row[k]
                    item.payers.append(p)
                yield from _emit(ccn, item, prof, seen_base)


def detect_format(path: str) -> str:
    with open(path, "rb") as f:
        start = f.read(4096).lstrip(b"\xef\xbb\xbf \r\n\t")
    if start.startswith((b"{", b"[")):
        return "json"
    try:
        text = start.decode("utf-8", errors="replace")
        first = next(csv.reader(io.StringIO(text)))
    except (StopIteration, csv.Error):
        return "unknown"
    # A CMS template CSV opens with the hospital_name header; anything else is a non-standard layout.
    return "csv" if first and norm_key(first[0]) == "hospital_name" else "non-standard csv"


def parse_file(path: str, ccn: str) -> tuple[Profile, Iterator[dict]]:
    prof = Profile()
    fmt = detect_format(path)
    if fmt == "json":
        return prof, iter_json(path, ccn, prof)
    if fmt == "csv":
        return prof, iter_csv(path, ccn, prof)
    prof.format = "non-standard"
    return prof, iter(())
