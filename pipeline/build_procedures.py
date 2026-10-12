"""Phase 3: build data/processed/procedures.csv from the selection and the team-written plain text, load it."""
import csv

import psycopg

from pipeline.cms70 import SOURCE_URL as CMS70_URL
from pipeline.common import DATABASE_URL, PROCESSED, now_utc

UPSERT = """
INSERT INTO procedures (code, code_type, plain_name, synonyms, description, category, setting, is_launch,
                        source_url, retrieved_at)
VALUES (%(code)s, %(code_type)s, %(plain_name)s, %(synonyms)s, %(description)s, %(category)s, %(setting)s, true,
        %(source_url)s, %(retrieved_at)s)
ON CONFLICT (code, code_type) DO UPDATE SET plain_name = EXCLUDED.plain_name, synonyms = EXCLUDED.synonyms,
    description = EXCLUDED.description, category = EXCLUDED.category, setting = EXCLUDED.setting,
    is_launch = true, source_url = EXCLUDED.source_url, retrieved_at = EXCLUDED.retrieved_at
"""


def main() -> None:
    with open(PROCESSED / "procedure_selection.csv", newline="") as f:
        sel = list(csv.DictReader(f))
    with open(PROCESSED / "procedure_text.csv", newline="") as f:
        text = {r["code"]: r for r in csv.DictReader(f)}
    missing = [s["code"] for s in sel if s["code"] not in text]
    assert not missing, f"no plain text for {missing}"
    rows = []
    for s in sel:
        t = text[s["code"]]
        rows.append({"code": s["code"], "code_type": "CPT", "setting": s["setting"], "category": s["category"],
                     "plain_name": t["plain_name"], "synonyms": t["synonyms"], "description": t["description"],
                     "cms_shoppable": s["cms70"], "selection_step": s["step"], "hospitals_publishing": s["hospitals"],
                     "hospitals_with_cash": s["with_cash"], "hospital_ccns": s["ccns"],
                     "source_url": CMS70_URL if s["cms70"] == "true" else "data/processed/code_frequency.csv",
                     "retrieved_at": now_utc()})
    assert len(rows) == 50, len(rows)
    with open(PROCESSED / "procedures.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.executemany(UPSERT, rows)
        cur.execute("UPDATE procedures SET is_launch = false WHERE is_launch AND NOT (code = ANY(%s))",
                    ([r["code"] for r in rows],))
    print(f"wrote and loaded {len(rows)} launch procedures")


if __name__ == "__main__":
    main()
