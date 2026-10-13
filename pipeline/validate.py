"""Run the official CMS validator (github.com/CMSgov/hpt-validator-cli) on downloaded files.

Writes data/processed/h1_validator.csv. The validator's error list is capped by --error-limit; when the
count equals the cap the true count is at least that number and the row says so.
"""
import csv
import json
import subprocess
import sys
from collections import Counter

from pipeline.common import PROCESSED, ROOT, now_utc
from pipeline.download import load_manifest
from pipeline.parsers.cms import detect_format

CLI = ROOT / "tools" / "validator" / "dist" / "index.js"
OUT = PROCESSED / "h1_validator.csv"
LIMIT = 100000
FIELDS = ["ccn", "file", "format", "valid", "error_count", "alert_count", "error_count_capped", "top_errors",
          "validator_version", "data_dictionary_version", "note", "source_url", "retrieved_at"]


def run(ccn: str, path: str, url: str) -> dict:
    fmt = detect_format(path)
    row = {"ccn": ccn, "file": path.rsplit("/", 1)[-1], "format": fmt, "source_url": url, "retrieved_at": now_utc()}
    if fmt not in ("csv", "json"):
        return {**row, "note": "not CSV or JSON; validator not run"}
    cmd = ["node", "--max-old-space-size=4096", str(CLI), path, "v3.0", "-f", fmt, "-o", "json", "-e", str(LIMIT)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=6 * 3600)
    try:
        d = json.loads(p.stdout[p.stdout.index("{"):])
    except ValueError:
        return {**row, "note": f"validator failed: {(p.stderr or p.stdout)[-300:]}"}
    msgs = Counter(e.get("message", "")[:120] for e in d.get("errors", []))
    return {**row, "valid": d.get("valid"), "error_count": d.get("errorCount"), "alert_count": d.get("alertCount"),
            "error_count_capped": d.get("errorCount", 0) >= LIMIT,
            "top_errors": " || ".join(f"{n} x {m}" for m, n in msgs.most_common(5)),
            "validator_version": d.get("validatorVersion"), "data_dictionary_version": d.get("dataDictionaryVersion"),
            "note": ""}


def main() -> None:
    only = set(sys.argv[1:])
    existing = {}
    if OUT.exists():
        with open(OUT, newline="") as f:
            existing = {r["ccn"]: r for r in csv.DictReader(f)}
    for (ccn, url), m in load_manifest().items():
        if m["status"] != "ok" or (only and ccn not in only):
            continue
        existing[ccn] = run(ccn, str(ROOT / m["path"]), url)
        print(ccn, existing[ccn].get("valid"), existing[ccn].get("error_count"), existing[ccn].get("note"), flush=True)
        with open(OUT, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(existing.values())


if __name__ == "__main__":
    main()
