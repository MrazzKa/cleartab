"""Usage log for the Jetstream2 allocation (Greg Chism reports usage at the end of the allocation).

One JSON line per request: time, provider, model, purpose and token counts. Never the prompt, the answer or any
document. File: data/raw/usage/jetstream_usage.jsonl (gitignored). Summary: python -m billcheck.usage
"""
import json
import time
from collections import defaultdict

from pipeline.common import RAW

LOG = RAW / "usage" / "jetstream_usage.jsonl"


def log(provider: str, model: str, response_json: dict, purpose: str) -> None:
    if provider != "jetstream":
        return
    try:
        u = response_json.get("usage") or {}
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "provider": provider,
                                "model": model, "purpose": purpose, "prompt_tokens": u.get("prompt_tokens"),
                                "completion_tokens": u.get("completion_tokens")}) + "\n")
    except OSError:
        pass                                    # a read-only server must still answer


def summary() -> dict:
    out = defaultdict(lambda: {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0})
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            r = json.loads(line)
            s = out[(r["time"][:7], r["model"])]
            s["requests"] += 1
            s["prompt_tokens"] += r.get("prompt_tokens") or 0
            s["completion_tokens"] += r.get("completion_tokens") or 0
    return {f"{m} {k}": v for (m, k), v in sorted(out.items())}


if __name__ == "__main__":
    for k, v in summary().items():
        print(k, v)
