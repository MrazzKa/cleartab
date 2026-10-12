"""p95 latency benchmark for GET /search (target: under 500 ms on the full dataset, proposal Table 6).

Usage: python -m api.bench [N] [--url http://localhost:8000]
Without --url the app runs in-process (FastAPI TestClient, database round trips included, no network).
Requests cycle through all 50 launch procedures (by plain name), every plan choice and 6 ZIP codes in both
metros, with a fixed seed. Writes data/processed/bench_search.csv.
"""
import csv
import random
import statistics
import sys
import time

from pipeline.common import PROCESSED, now_utc

ZIPS = ["85006", "85013", "85251", "85224", "85719", "85745"]


def main() -> None:
    args = sys.argv[1:]
    n = int(next((a for a in args if a.isdigit()), "500"))
    url = args[args.index("--url") + 1] if "--url" in args else None
    if url:
        import httpx
        client = httpx.Client(base_url=url, timeout=30)
    else:
        from fastapi.testclient import TestClient

        from api.main import app
        client = TestClient(app)
        client.__enter__()
    with open(PROCESSED / "procedures.csv", newline="") as f:
        names = [r["plain_name"] for r in csv.DictReader(f)]
    plans = client.get("/plans").json()["plans"]
    rng = random.Random(42)
    for _ in range(10):  # warm-up
        client.get("/search", params={"q": names[0], "plan": "cash", "zip": "85006"})
    times, errors = [], 0
    for i in range(n):
        params = {"q": names[i % len(names)], "plan": rng.choice(plans), "zip": rng.choice(ZIPS)}
        t = time.perf_counter()
        r = client.get("/search", params=params)
        times.append((time.perf_counter() - t) * 1000)
        errors += r.status_code != 200
    times.sort()
    p50, p95, p99 = (times[int(len(times) * q) - 1] for q in (0.5, 0.95, 0.99))
    sug = []
    for i in range(200):
        t = time.perf_counter()
        client.get("/procedures/suggest", params={"q": names[i % len(names)][:4]})
        sug.append((time.perf_counter() - t) * 1000)
    sug.sort()
    sug95 = sug[int(len(sug) * 0.95) - 1]
    row = {"mode": url or "in-process", "requests": n, "errors": errors, "p50_ms": round(p50, 1),
           "p95_ms": round(p95, 1), "p99_ms": round(p99, 1), "mean_ms": round(statistics.mean(times), 1),
           "suggest_p95_ms": round(sug95, 1), "target_search_p95_ms": 500, "target_suggest_ms": 150,
           "source_url": "api/bench.py", "retrieved_at": now_utc()}
    out = PROCESSED / "bench_search.csv"
    new = not out.exists()
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(row)


if __name__ == "__main__":
    main()
