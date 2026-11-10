"""Published emergency department visit rates (plan item P10), from data/processed/er_rates.csv.

The table is built by pipeline.er_rates from each hospital's machine-readable file: CPT 99281-99285 (ED visit
levels 1-5), negotiated dollar rates per insurer and plan, and the cash and gross charges. EOBs often print an ER
line without a code ("Emergency room services"), so an ER line is recognized by its code or by its description.
"""
import csv
import re
from functools import lru_cache

from pipeline.common import PROCESSED

LEVELS = ("99281", "99282", "99283", "99284", "99285")
ER_WORDS = re.compile(r"\b(emergency|emerg|er|ed)\b", re.I)


@lru_cache(maxsize=1)
def table() -> list[dict]:
    path = PROCESSED / "er_rates.csv"
    if not path.exists():
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["amount"] = float(r["amount"])
    return rows


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def find_hospital(name: str | None) -> str | None:
    """CCN of the hospital whose published name is contained in (or contains) the name printed on the paper."""
    n = _norm(name or "")
    if len(n) < 6:
        return None
    names = {r["ccn"]: _norm(r["hospital"]) for r in table()}
    hits = [ccn for ccn, h in names.items() if h and (h in n or n in h)]
    return hits[0] if len(hits) == 1 else None


def is_er_line(code: str | None, description: str) -> bool:
    return (code or "") in LEVELS or bool(ER_WORDS.search(description or ""))


def rates(ccn: str, payer: str) -> list[dict]:
    """Negotiated ED visit rates of one insurer at one hospital."""
    return [r for r in table() if r["ccn"] == ccn and r["price_type"] == "negotiated_dollar"
            and r["canonical_payer"] == payer]


def hospital_name(ccn: str) -> str | None:
    return next((r["hospital"] for r in table() if r["ccn"] == ccn), None)
