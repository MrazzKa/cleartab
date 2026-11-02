"""ClearTab bill check (v2 Features 7 and 8): rule engine, reference data and dispute kit."""
import json
import pathlib

from billcheck.models import CheckRequest, CheckResult
from billcheck.reference import load_mue, load_ptp, published_prices
from billcheck.rules import check

CASES = pathlib.Path(__file__).with_name("cases.json")


def demo_cases() -> list[dict]:
    return json.loads(CASES.read_text())


def run_check(req: CheckRequest, conn=None) -> CheckResult:
    """Check one request; `conn` (psycopg, dict rows) enables the published price checks."""
    prices = {}
    if conn is not None and req.context.hospital_ccn:
        codes = sorted({ln.code for ln in (req.eob.lines if req.eob else []) if ln.code}
                       | {bl.code for bl in (req.bill.lines if req.bill else []) if bl.code})
        prices = published_prices(conn, req.context.hospital_ccn, codes, req.context.insurer)
    return check(req, prices=prices, mue=load_mue(), ptp=load_ptp())
