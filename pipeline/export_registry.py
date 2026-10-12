"""One-off: export the 'Registry and audit' sheet of the audit XLSX to data/processed/hospital_registry.csv.

The master prompt expected hospital_registry.csv as an input; only the XLSX was available, so the CSV is
derived from it column for column. No values are changed.
"""
import csv

import openpyxl

from pipeline.common import REGISTRY_CSV, REGISTRY_SOURCE, ROOT

XLSX = ROOT / "docs" / "source" / "ClearTab_Hospital_Registry_and_Data_Use_Audit.xlsx"
COLUMNS = [
    "ccn", "name", "city", "metro", "county", "health_system", "listed_in_cms_hpt", "mrf_url", "format",
    "robots_blocks_mrf", "login_or_clickthrough", "terms_restrict_reproduction", "terms_ban_automated",
    "freshness_signal", "notes", "cms_hpt_url", "retrieved_at",
]


def main() -> None:
    ws = openpyxl.load_workbook(XLSX, read_only=True)["Registry and audit"]
    rows = list(ws.iter_rows(values_only=True))
    assert len(rows[0]) == len(COLUMNS), rows[0]
    with open(REGISTRY_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS + ["source_url"])
        for r in rows[1:]:
            if r[0] is None:
                continue
            w.writerow(["" if v is None else str(v) for v in r] + [REGISTRY_SOURCE])
    print(f"wrote {len(rows) - 1} hospitals to {REGISTRY_CSV}")


if __name__ == "__main__":
    main()
