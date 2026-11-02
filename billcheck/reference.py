"""Reference data for the bill check: CMS edit tables and the hospital prices already in the database.

CMS NCCI tables carry CPT codes under the AMA license, so they are read from data/raw (gitignored), never
committed:
- MUE (medically unlikely edits): data/raw/reference/medicare-ncci-<year>-q<q>-*-mue-table.zip, downloaded by
  `python -m billcheck.fetch_reference`.
- PTP (procedure-to-procedure edits): behind the AMA license click-through on cms.gov, so a team member downloads
  them by hand into data/raw/manual/ncci_ptp/ (see MANUAL_DOWNLOADS.md). Without them the pair check is skipped
  and the result says so.
"""
import csv
import glob
import io
import re
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache

from pipeline.common import RAW

REFERENCE = RAW / "reference"
PTP_DIR = RAW / "manual" / "ncci_ptp"

SOURCES = {
    "cms_eob": ("CMS Coverage to Care, Reading your explanation of benefits (EOB)",
                "https://www.cms.gov/files/document/11819-sample-explanation-benefits-508.pdf"),
    "mue": ("CMS NCCI medically unlikely edits (MUE)",
            "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/"
            "medicare-ncci-medically-unlikely-edits"),
    "ptp": ("CMS NCCI procedure-to-procedure (PTP) edits",
            "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/"
            "medicare-ncci-procedure-procedure-ptp-edits"),
    "nsa_insured": ("CMS, Know your medical bill rights when using insurance",
                    "https://www.cms.gov/initiatives/your-patient-rights/medical-bill-rights/know-your-rights/insurance"),
    "nsa_dispute": ("CMS, Dispute a bill (uninsured or self-pay)",
                    "https://www.cms.gov/medical-bill-rights/help/dispute-a-bill"),
    "nsa_ground": ("CMS, Action plan: ground ambulance bill",
                   "https://www.cms.gov/medical-bill-rights/help/plan/insurance-ground-ambulance-bill"),
    "hpt": ("Hospital standard charges file (45 CFR 180.50)", None),
}


@dataclass(frozen=True)
class MueEdit:
    value: int
    indicator: str      # "1 Line Edit", "2 Date of Service Edit: Policy", "3 Date of Service Edit: Clinical"
    table: str          # "facility outpatient" | "practitioner"
    as_of: str


def _mue_rows(path: str) -> tuple[str, list[list[str]]]:
    z = zipfile.ZipFile(path)
    name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    as_of = re.search(r"Eff_(\d\d-\d\d-\d{4})", name)
    text = z.read(name).decode("latin-1")
    rows = list(csv.reader(io.StringIO(text)))
    start = next(i for i, r in enumerate(rows) if r and r[0].replace("\n", " ").startswith("HCPCS/"))
    return (as_of.group(1) if as_of else ""), rows[start + 1:]


@lru_cache(maxsize=1)
def load_mue() -> dict[str, dict[str, MueEdit]]:
    """{"facility outpatient" | "practitioner": {code: MueEdit}}; empty when the tables were not downloaded."""
    out: dict[str, dict[str, MueEdit]] = {}
    for table, pattern in (("facility outpatient", "*facility-outpatient-hospital-services-mue-table.zip"),
                           ("practitioner", "*practitioner-services-mue-table.zip")):
        files = sorted(glob.glob(str(REFERENCE / pattern)))
        if not files:
            continue
        as_of, rows = _mue_rows(files[-1])
        out[table] = {r[0].strip(): MueEdit(int(r[1]), r[2].strip(), table, as_of)
                      for r in rows if len(r) >= 3 and r[0].strip() and r[1].strip().isdigit()}
    return out


@dataclass
class PtpTable:
    pairs: dict[str, dict[str, str]] = field(default_factory=dict)   # column 1 code -> {column 2 code: modifier}
    files: list[str] = field(default_factory=list)


def _ptp_lines(path: str):
    if path.lower().endswith(".zip"):
        z = zipfile.ZipFile(path)
        for n in z.namelist():
            if n.lower().endswith((".txt", ".csv")):
                yield from io.TextIOWrapper(z.open(n), encoding="latin-1")
    else:
        with open(path, encoding="latin-1") as f:
            yield from f


@lru_cache(maxsize=1)
def load_ptp() -> PtpTable:
    """Active PTP pairs from whatever CMS files are in data/raw/manual/ncci_ptp/ (zip, txt or csv).

    CMS text files are tab separated with columns Column 1, Column 2, *, Effective Date, Deletion Date,
    Modifier (0 = never together, 1 = allowed with an appropriate modifier, 9 = not applicable), Rationale.
    """
    t = PtpTable()
    for path in sorted(glob.glob(str(PTP_DIR / "*"))):
        if not path.lower().endswith((".zip", ".txt", ".csv")):
            continue
        t.files.append(path)
        for line in _ptp_lines(path):
            parts = [p.strip() for p in re.split(r"\t|,", line.rstrip("\n"))]
            if len(parts) < 6 or not re.fullmatch(r"[0-9A-Z]{5}", parts[0] or "") \
                    or not re.fullmatch(r"[0-9A-Z]{5}", parts[1] or ""):
                continue
            deletion, modifier = parts[4], parts[5]
            if deletion not in ("*", "", "99991231") or modifier not in ("0", "1"):
                continue
            t.pairs.setdefault(parts[0], {})[parts[1]] = modifier
    return t


PRICE_SQL = """
SELECT pr.code, h.name AS hospital, h.ccn,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'cash') AS cash,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'gross') AS gross,
  min(p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
                        AND py.canonical_name = %(insurer)s) AS neg_min,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar'
                        AND p.methodology = 'fixed dollar' AND py.canonical_name = %(insurer)s) AS neg_median,
  max(p.amount) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
                        AND py.canonical_name = %(insurer)s) AS neg_max,
  count(*) FILTER (WHERE p.price_type = 'negotiated_dollar' AND p.methodology = 'fixed dollar'
                   AND py.canonical_name = %(insurer)s) AS neg_n,
  min(p.source_url) AS source_url, min(p.retrieved_at)::text AS retrieved_at
FROM prices p
JOIN hospitals h ON h.id = p.hospital_id
JOIN procedures pr ON pr.id = p.procedure_id
LEFT JOIN payers py ON py.id = p.payer_id
WHERE h.ccn = %(ccn)s AND pr.code = ANY(%(codes)s) AND p.setting IN ('outpatient', 'both')
  AND NOT EXISTS (SELECT 1 FROM unnest(p.flags) f WHERE f LIKE 'dropped:%%')
GROUP BY pr.code, h.name, h.ccn
"""


def published_prices(conn, ccn: str, codes: list[str], insurer: str | None) -> dict[str, dict]:
    """Published cash, gross and the insurer's fixed dollar rates per code at one hospital (launch procedures)."""
    if not ccn or not codes:
        return {}
    rows = conn.execute(PRICE_SQL, {"ccn": ccn, "codes": codes, "insurer": insurer or ""}).fetchall()
    out = {}
    for r in rows:
        r = dict(r)
        for k in ("cash", "gross", "neg_min", "neg_median", "neg_max"):
            r[k] = None if r[k] is None else round(float(r[k]), 2)
        out[r["code"]] = r
    return out
