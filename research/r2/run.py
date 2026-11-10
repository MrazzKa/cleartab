"""R2: can a language model check a medical bill? Rules vs language models vs hybrid on the synthetic cases.

Conditions
- A  rules: the ClearTab rule engine on the exact structured case (upper bound for reading).
- B  model: a language model reads both documents as text and answers in JSON (error? which kinds? correct
     amount due?). Models: open-weights models on Groq.
- C  hybrid: a vision model reads rendered images of the two documents into fields (billcheck.reader), then the
     rule engine checks them. Needs research/r2/data/images/ (python -m research.r2.render).
- D  local: ClearTab's local reader (text recognition on this machine + fixed rules, no language model, no
     outside service) reads the two images, then the rule engine checks them. All cases.

Scoring per case: detection (any error vs none), main error category found, correct amount due within $1.
Model answers are cached in research/r2/data/responses/<condition>__<model>.jsonl so a rerun resumes.

Usage: python -m research.r2.run [--conditions A,B,C,D] [--models openai/gpt-oss-120b,...] [--limit N]
"""
import argparse
import json
import os
import pathlib
import time

import requests

from billcheck import run_check
from billcheck.models import CheckRequest
from billcheck.reader import ReaderError, read_document
from pipeline import common  # loads .env

DATA = pathlib.Path(__file__).with_name("data")
RESP = DATA / "responses"
GROQ = "https://api.groq.com/openai/v1/chat/completions"
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
MAIN_RULE = {"payment_not_subtracted": "balance_over_eob", "balance_billing": "balance_over_eob",
             "duplicate_line": "duplicate_line", "line_not_on_eob": "bill_line_not_on_eob", "mue_units": "mue_units",
             "ncci_pair": "ncci_pair", "eob_math": "eob_line_sum", "allowed_above_published": "allowed_vs_published"}

PROMPT = """You help a patient check a US hospital bill against the insurer's explanation of benefits (EOB).
The provider is in network. Published information you may use: the hospital's published Blue Cross Blue Shield of
Arizona rates for these services are: 73721 $712.68-$950.22; 71046 $83.62-$111.49; 80053 $10.56-$42.06;
85025 $7.77-$30.93. Medicare's medically unlikely edit for 73721 is 3 units per day.

Possible problems (use these keys):
{cats}

Documents:
{doc}

Answer with one JSON object: {{"has_error": true|false, "problems": [keys from the list, empty if none],
"correct_amount_due": number (what the patient should actually owe this hospital now), "explanation": short text}}"""


def load_cases() -> tuple[list[dict], dict]:
    d = json.loads((DATA / "cases.json").read_text())
    return d["cases"], d["categories"]


def cached(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def wait_for(r: requests.Response, attempt: int) -> float:
    h = r.headers.get("retry-after")
    if h:
        return float(h) + 0.5
    return min(60.0, 3 * 2 ** attempt)


def groq(model: str, prompt: str) -> str:
    key = os.environ["GROQ_API_KEY"]
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}]}
    if model.startswith("qwen/"):
        body["reasoning_effort"] = "none"       # keeps responses inside the free-tier token rate
        body["max_completion_tokens"] = 600     # free tier: 1,000 output tokens per minute for this model
    for attempt in range(10):
        r = requests.post(GROQ, json=body, timeout=180, headers={"Authorization": f"Bearer {key}"})
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(wait_for(r, attempt))
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError(f"{model}: still rate limited")


def score(case: dict, has_error: bool, rules_or_keys: set[str], amount: float | None, by_rule: bool) -> dict:
    err = case["error"]
    main = (MAIN_RULE.get(err) if by_rule else err) if err != "none" else None
    return {"detected": has_error == (err != "none"),
            "category": (main in rules_or_keys) if main else (not rules_or_keys),
            "amount": amount is not None and abs(amount - case["correct_balance"]) <= 1.0}


def db():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(common.DATABASE_URL, row_factory=dict_row)


def condition_a(cases: list[dict]) -> list[dict]:
    out = []
    conn = db()
    for c in cases:
        res = run_check(CheckRequest(**c["request"]), conn)
        flagged = {f.rule for f in res.findings if f.severity in ("error", "warning")}
        amount = res.summary.eob_you_owe
        amount = None if amount is None else max(amount - c["request"]["bill"]["patient_payments"], 0)
        out.append({"id": c["id"], "error": c["error"], "rules": sorted(flagged),
                    **score(c, bool(flagged), flagged, amount, by_rule=True)})
    return out


def condition_b(cases: list[dict], cats: dict, model: str) -> list[dict]:
    path = RESP / f"B__{model.replace('/', '_')}.jsonl"
    done = cached(path)
    cat_text = "\n".join(f"- {k}: {v}" for k, v in cats.items())
    with path.open("a") as f:
        for c in cases:
            if c["id"] in done:
                continue
            try:
                raw = groq(model, PROMPT.format(cats=cat_text, doc=c["text"]))
            except requests.HTTPError as e:
                raw = json.dumps({"error": str(e)[:200]})
            rec = {"id": c["id"], "model": model, "raw": raw}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done[c["id"]] = rec
    out = []
    for c in cases:
        try:
            j = json.loads(done[c["id"]]["raw"])
            keys = {k for k in j.get("problems", []) if k in cats}
            amt = j.get("correct_amount_due")
            amt = float(amt) if isinstance(amt, (int, float, str)) and str(amt).replace(".", "", 1).isdigit() else None
            out.append({"id": c["id"], "error": c["error"], "problems": sorted(keys), "parsed": True,
                        **score(c, bool(j.get("has_error")), keys, amt, by_rule=False)})
        except (json.JSONDecodeError, AttributeError, TypeError):
            out.append({"id": c["id"], "error": c["error"], "parsed": False,
                        "detected": False, "category": False, "amount": False})
    return out


def condition_c(cases: list[dict]) -> list[dict]:
    path = RESP / "C__qwen_qwen3.8-27b.jsonl"
    done = cached(path)
    with path.open("a") as f:
        for c in cases:
            if c["id"] in done:
                continue
            imgs = [((DATA / "images" / f"{c['id']}_{k}.png").read_bytes(), "image/png") for k in ("eob", "bill")]
            rec = None
            for attempt in range(15):
                try:
                    r = read_document(imgs)
                    rec = {"id": c["id"], "read": r.model_dump()}
                    break
                except ReaderError as e:
                    if "429" in str(e):          # rate limit, not a reading failure: wait, never record it
                        time.sleep(min(90, 10 * (attempt + 1)))
                        continue
                    rec = {"id": c["id"], "error": str(e)}
                    break
            if rec is None:
                continue
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done[c["id"]] = rec
    return evaluate_reads(cases, done, "C")


def evaluate_reads(cases: list[dict], done: dict, label: str) -> list[dict]:
    """Run the rule engine on what a reader copied from the two images of each case, and score it."""
    out = []
    conn = db()
    for c in cases:
        rec = done.get(c["id"])
        if rec is None:
            print(f"{label}: {c['id']} not read yet; rerun to complete")
            continue
        if "read" not in rec:
            out.append({"id": c["id"], "error": c["error"], "parsed": False, "detected": False, "category": False,
                        "amount": False, "read_totals": False})
            continue
        rd = rec["read"]
        req = {"context": c["request"]["context"],
               "eob": {"lines": [{k: v for k, v in ln.items() if k not in ("units", "amount") and v is not None}
                                 for ln in rd["eob_lines"]], "you_owe_total": rd["you_owe_total"]},
               "bill": {"provider_type": "facility", "balance_due": rd["balance_due"],
                        "patient_payments": rd["patient_payments"] or 0,
                        "lines": [{"service_date": ln.get("service_date"), "description": ln.get("description", ""),
                                   "code": ln.get("code"), "units": ln.get("units") or 1, "amount": ln.get("amount") or 0}
                                  for ln in rd["bill_lines"]]}}
        try:
            res = run_check(CheckRequest(**req), conn)
        except Exception:  # noqa: BLE001  a misread field the request model rejects counts as a failed read
            out.append({"id": c["id"], "error": c["error"], "parsed": False, "detected": False, "category": False,
                        "amount": False, "read_totals": False})
            continue
        flagged = {f.rule for f in res.findings if f.severity in ("error", "warning")} - {"no_eob_yet"}
        b = c["request"]["bill"]
        totals_ok = (rd["balance_due"] == b["balance_due"] and rd["you_owe_total"] == c["request"]["eob"]["you_owe_total"])
        amount = None if rd["you_owe_total"] is None else max(rd["you_owe_total"] - (rd["patient_payments"] or 0), 0)
        out.append({"id": c["id"], "error": c["error"], "parsed": True, "rules": sorted(flagged),
                    "read_totals": totals_ok, **score(c, bool(flagged), flagged, amount, by_rule=True)})
    return out


def condition_d(cases: list[dict]) -> list[dict]:
    """D: ClearTab's local reader (text recognition on this machine + fixed rules, no language model) reads the
    EOB image and the bill image separately; the rule engine checks what it copied."""
    from billcheck.local_reader import read_local
    path = RESP / "D__local_ocr.jsonl"
    done = cached(path)
    with path.open("a") as f:
        for c in cases:
            if c["id"] in done:
                continue
            try:
                eob = read_local([((DATA / "images" / f"{c['id']}_eob.png").read_bytes(), "image/png")])
                bill = read_local([((DATA / "images" / f"{c['id']}_bill.png").read_bytes(), "image/png")])
                rd = eob.model_dump()
                rd.update(balance_due=bill.balance_due, patient_payments=bill.patient_payments,
                          bill_lines=bill.model_dump()["bill_lines"])
                rec = {"id": c["id"], "read": rd}
            except ReaderError as e:
                rec = {"id": c["id"], "error": str(e)}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done[c["id"]] = rec
    return evaluate_reads(cases, done, "D")


def summarize(name: str, rows: list[dict]) -> dict:
    n = len(rows)
    errs = [r for r in rows if r["error"] != "none"]
    clean = [r for r in rows if r["error"] == "none"]
    s = {"condition": name, "cases": n,
         "detection_accuracy": round(sum(r["detected"] for r in rows) / n, 3),
         "sensitivity": round(sum(r["detected"] for r in errs) / len(errs), 3) if errs else None,
         "specificity": round(sum(r["detected"] for r in clean) / len(clean), 3) if clean else None,
         "category_accuracy": round(sum(r["category"] for r in rows) / n, 3),
         "amount_accuracy": round(sum(r["amount"] for r in rows) / n, 3),
         "unparsed": sum(1 for r in rows if r.get("parsed") is False)}
    if any("read_totals" in r for r in rows):
        s["read_totals_exact"] = round(sum(r.get("read_totals", False) for r in rows) / n, 3)
    by = {}
    for r in rows:
        by.setdefault(r["error"], []).append(r["detected"] and r["category"])
    s["by_error"] = {k: f"{sum(v)}/{len(v)}" for k, v in sorted(by.items())}
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="A,B")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--c-per-type", type=int, default=4, help="condition C: cases per error type (none: twice)")
    args = ap.parse_args()
    cases, cats = load_cases()
    if args.limit:
        cases = cases[:args.limit]
    RESP.mkdir(parents=True, exist_ok=True)
    results, summaries = {}, []
    conds = args.conditions.split(",")
    if "A" in conds:
        results["A rules"] = condition_a(cases)
    if "B" in conds:
        for m in args.models.split(","):
            results[f"B {m}"] = condition_b(cases, cats, m)
    if "C" in conds:
        sub, seen = [], {}
        for c in cases:      # stratified: the first N cases of each error type in file order, 2N clean cases
            k = 2 * args.c_per_type if c["error"] == "none" else args.c_per_type
            if seen.get(c["error"], 0) < k:
                sub.append(c)
                seen[c["error"]] = seen.get(c["error"], 0) + 1
        results["C qwen/qwen3.8-27b reads + rules"] = condition_c(sub)
        results["A rules, same cases as C"] = [r for r in results.get("A rules", condition_a(sub))
                                               if r["id"] in {c["id"] for c in sub}]
    if "D" in conds:
        results["D local text recognition + rules"] = condition_d(cases)
    for name, rows in results.items():
        summaries.append(summarize(name, rows))
        print(json.dumps(summaries[-1]))
    out = DATA / "results.json"       # keep earlier conditions; replace only the ones run now
    old = json.loads(out.read_text()) if out.exists() else {"summaries": [], "rows": {}}
    rows = {**old.get("rows", {}), **results}
    keep = [x for x in old.get("summaries", []) if x["condition"] not in results]
    out.write_text(json.dumps({"summaries": keep + summaries, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
