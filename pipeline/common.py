"""Shared constants and helpers for the ClearTab pipeline."""
import os
import pathlib
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANUAL = RAW / "manual"
PROCESSED = ROOT / "data" / "processed"

# Local settings (DATABASE_URL) may live in an untracked .env file at the repo root.
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

USER_AGENT = "ClearTab-capstone/0.1 (University of Arizona; contact kamarayev@arizona.edu)"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://cleartab:cleartab@localhost:5432/cleartab")
REGISTRY_CSV = PROCESSED / "hospital_registry.csv"
# Base list used to build the registry (audit XLSX, "Method" sheet).
REGISTRY_SOURCE = "https://data.cms.gov/provider-data/dataset/xubh-q36u"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
