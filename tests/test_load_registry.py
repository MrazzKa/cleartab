import csv

from pipeline.common import REGISTRY_CSV
from pipeline.load_registry import to_row


def _read():
    with open(REGISTRY_CSV, newline="") as f:
        return list(csv.DictReader(f))


def test_registry_counts_match_audit():
    rows = _read()
    assert len(rows) == 46
    assert sum(r["metro"] == "Tucson" for r in rows) == 8
    assert sum(r["health_system"] == "Banner Health" for r in rows) == 15
    assert all(r["source_url"] and r["retrieved_at"] for r in rows)


def test_blocked_row_status():
    rows = {r["ccn"]: to_row(r) for r in _read()}
    assert rows["030085"]["status"] == "blocked"        # Northwest, robots.txt disallows /Uploads/
    assert rows["030006"]["mrf_url"] is None            # TMC, not checked
    assert rows["030153"]["discovery_method"] == "price transparency page"
