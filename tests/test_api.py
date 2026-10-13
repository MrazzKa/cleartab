import psycopg
import pytest

from api.main import EXPLAINER, completeness_label, miles
from pipeline.common import DATABASE_URL


def test_miles_phoenix_to_tucson():
    assert 100 < miles((33.4484, -112.0740), (32.2226, -110.9747)) < 112


def test_labels():
    assert completeness_label(None, "published") == "not checked yet"
    assert completeness_label(0, "not published") == "not published"
    assert completeness_label(96.0, "published") == "complete"
    assert completeness_label(55.0, "published") == "partial"


def test_explainer_rules():
    words = EXPLAINER.split()
    assert len(words) < 120
    assert "facility charge" in EXPLAINER and "doctor's fee" in EXPLAINER


def _has_data() -> bool:
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as c:
            return c.execute("SELECT count(*) FROM prices").fetchone()[0] > 0
    except Exception:
        return False


@pytest.mark.skipif(not _has_data(), reason="needs a database loaded by the ETL")
def test_search_end_to_end():
    from fastapi.testclient import TestClient

    from api.main import app
    with TestClient(app) as c:
        r = c.get("/search", params={"q": "knee mri", "plan": "cash", "zip": "85006"})
        assert r.status_code == 200
        d = r.json()
        assert d["procedure"]["code"] == "73721" and len(d["results"]) <= 10
        prices = [x["applicable_price"] for x in d["results"] if x["applicable_price"] is not None]
        assert prices == sorted(prices)
        assert all(x["provenance"]["source_url"].startswith("http") for x in d["results"])
        assert c.get("/search", params={"q": "knee mri", "plan": "Not A Plan"}).status_code == 422
