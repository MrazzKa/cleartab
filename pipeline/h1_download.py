"""Phase 2 step 3: download the H1 sample, one worker per domain so per-domain rate limits hold."""
import csv
import sys
import threading
from collections import defaultdict
from urllib.parse import urlsplit

from pipeline.common import REGISTRY_CSV
from pipeline.download import download, load_manifest, save_manifest
from pipeline.http import PoliteSession, RobotsDisallowed

# Default sample from the master prompt. Northwest Medical Center and Oro Valley are blocked by robots.txt
# (Phase 1) and are replaced by two non-Banner hospitals from systems not otherwise in the sample.
SAMPLE = ["030010", "030011", "030092", "030038", "030024", "030036", "030030", "030022", "030103", "030107",
          "030064", "030065", "030152", "030153", "030108"]
# Valleywise (030022) closed the connection on two GET attempts on 2026-10-12 (HEAD worked: 539,835,870 bytes)
# and is replaced by The CORE Institute Specialty Hospital, another system not otherwise in the sample.
REPLACED = {"030085": "030152", "030114": "030153", "030022": "030108"}

lock = threading.Lock()


def worker(urls, manifest):
    s = PoliteSession()
    for ccn, url in urls:
        try:
            row = download(s, ccn, url, manifest)
        except RobotsDisallowed:
            row = {"ccn": ccn, "url": url, "status": "robots.txt disallows", "source_url": url}
        except Exception as e:  # report, never skip silently
            row = {"ccn": ccn, "url": url, "status": f"error: {str(e)[:200]}", "source_url": url}
        with lock:
            manifest[(ccn, url)] = {**{k: "" for k in ("final_url", "path", "sha256", "size_bytes")}, **row}
            save_manifest(manifest)
        print(ccn, row.get("status"), row.get("size_bytes"), row.get("note", ""), flush=True)


def main() -> None:
    only = set(sys.argv[1:])
    with open(REGISTRY_CSV, newline="") as f:
        reg = {r["ccn"]: r for r in csv.DictReader(f)}
    by_host = defaultdict(list)
    for ccn in SAMPLE:
        if only and ccn not in only:
            continue
        url = reg[ccn]["mrf_url"]
        by_host[urlsplit(url).netloc].append((ccn, url))
    manifest = load_manifest()
    threads = [threading.Thread(target=worker, args=(u, manifest)) for u in by_host.values()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
