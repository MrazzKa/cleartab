"""Medicare amounts for Arizona as a yardstick (plan items P3 and P12), from data/processed/medicare_pfs_az_2026.csv
(built by pipeline.medicare_pfs from the CMS Physician Fee Schedule). Medicare is not the patient's plan: the amount
is a public reference point that says how a price compares, never what the patient owes.
"""
import csv
from functools import lru_cache

from pipeline.common import PROCESSED


@lru_cache(maxsize=1)
def table() -> dict[tuple[str, str], dict]:
    path = PROCESSED / "medicare_pfs_az_2026.csv"
    if not path.exists():
        return {}
    with open(path, newline="") as f:
        return {(r["code"], r["modifier"]): r for r in csv.DictReader(f)}


def amount(code: str | None, modifier: str = "", facility: bool = False) -> float | None:
    """Arizona Medicare amount for one unit; the office (non-facility) amount unless the service was in a facility
    or CMS prices it only in a facility."""
    r = table().get(((code or "").upper(), modifier or ""))
    if not r:
        return None
    v = r["az_facility"] if facility or not r["az_nonfacility"] else r["az_nonfacility"]
    return float(v) if v else None


def global_days(code: str | None) -> str | None:
    r = table().get(((code or "").upper(), ""))
    return r["global_days"] if r else None
