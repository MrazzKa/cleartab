"""Phase 1: re-check open registry rows and collect freshness signals.

For rows whose discovery is unresolved (Unknown, not found, "No - ..."):
  1. fetch <site>/cms-hpt.txt (robots.txt respected) and match location-name to the hospital;
  2. if no match, fetch the price transparency page and list candidate file links.
For every MRF URL: one HEAD request for Last-Modified and Content-Length (no download).
Writes research/registry/recheck.csv and updates data/processed/hospital_registry.csv in place.
"""
import csv
import re
from urllib.parse import urljoin

import requests

from pipeline.common import PROCESSED, REGISTRY_CSV, ROOT, now_utc
from pipeline.http import PoliteSession, RobotsDisallowed

OUT = ROOT / "research" / "registry" / "recheck.csv"
LINK_RE = re.compile(r"""href=["']([^"'#]+)["']""", re.I)
FILE_HINT = re.compile(r"standardcharges|\.csv(\?|$)|\.json(\?|$)|\.xlsx?(\?|$)|\.zip(\?|$)|MRFDownload", re.I)
STOP = {"medical", "center", "hospital", "the", "of", "and", "campus", "health", "-", "&"}

# Price transparency pages to try when cms-hpt.txt does not resolve a hospital. Taken from the audit
# XLSX notes, the hospital's own cms-hpt.txt (source-page-url) or the site root.
FALLBACK_PAGES = {
    "030037": "https://www.honorhealth.com/patients-visitors/average-pricing",
    "030153": "https://eastvalleyhospital.com/price-transparency/",
    "030108": "https://www.thecoreinstitutehospital.com/patients-visitors/billing-options/",
    "030138": "https://www.cityofhope.org/patients/billing-and-insurance/price-transparency",
    "030006": "https://www.tmcaz.com/en/price-transparency",
    "030112": "https://www.azosh.com/",
}

# When a price page lists several files, the substring that identifies this hospital's own full file.
# Chosen by reading the link list in research/registry/recheck.csv; a reviewer should confirm each one.
FILE_HINTS = {
    "030037": "honorhealthtmc_standardcharges",       # Tempe Medical Center
    "030153": "ev_standard_charges_862195601",        # East Valley, 2026-08 upload
    "030108": "SPECIALTY-HOSPITAL-STANDARDCHARGES",   # CORE, 2026-09 upload (an INPATIENT-only file also exists)
}


def tokens(name: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", name.lower().replace("st.", "st"))
    return {w for w in words if w not in STOP}


def parse_hpt(text: str) -> list[dict]:
    entries, cur = [], {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "location-name" and cur:
            entries.append(cur)
            cur = {}
        cur[k] = v
    if cur:
        entries.append(cur)
    return entries


def match_entry(name: str, entries: list[dict]) -> dict | None:
    want = tokens(name)
    best, best_score = None, 0.0
    for e in entries:
        got = tokens(e.get("location-name", ""))
        if not got:
            continue
        score = len(want & got) / len(want | got)
        if score > best_score:
            best, best_score = e, score
    return best if best_score >= 0.5 else None


def robots_reason(s: PoliteSession, url: str) -> str:
    rob = s.robots(url)
    if rob.status is None:
        return "site not reachable (robots.txt could not be fetched)"
    return f"robots.txt disallows (robots.txt HTTP {rob.status})"


def needs_recheck(r: dict) -> bool:
    fields = (r["listed_in_cms_hpt"], r["mrf_url"], r["format"], r["robots_blocks_mrf"])
    return any(f.startswith(("Unknown", "No -", "not ", "Not ")) for f in fields)


def recheck_discovery(s: PoliteSession, r: dict, hpt_cache: dict) -> dict:
    out = {"ccn": r["ccn"], "name": r["name"], "step": "", "result": "", "url_checked": "", "found_mrf_url": "",
           "evidence": "", "retrieved_at": now_utc()}
    hpt = r["cms_hpt_url"] if r["cms_hpt_url"].startswith("http") else None
    if hpt:
        out["url_checked"] = hpt
        if hpt not in hpt_cache:
            try:
                resp = s.get(hpt)
                hpt_cache[hpt] = (resp.status_code, resp.text if "text" in resp.headers.get("content-type", "") else "")
            except RobotsDisallowed:
                hpt_cache[hpt] = ("robots", "")
            except requests.RequestException as e:
                hpt_cache[hpt] = ("error", str(e)[:200])
        status, text = hpt_cache[hpt]
        entries = parse_hpt(text) if isinstance(status, int) else []
        m = match_entry(r["name"], entries)
        if m and m.get("mrf-url"):
            out.update(step="cms-hpt.txt", result=f"listed (HTTP {status})", found_mrf_url=m["mrf-url"],
                       evidence=f"location-name: {m.get('location-name')}")
            return out
        names = "; ".join(e.get("location-name", "") for e in entries)
        out.update(step="cms-hpt.txt", evidence=(f"HTTP {status}; lists: {names}" if isinstance(status, int)
                                                 else f"{status}: {text}")[:400])
        out["result"] = {"robots": robots_reason(s, hpt) + " (cms-hpt.txt)", "error": "not reachable"}.get(
            status, "not listed")
    page = FALLBACK_PAGES.get(r["ccn"])
    if not page:
        return out
    out["step"] += " -> price transparency page"
    out["url_checked"] += f" ; {page}"
    try:
        resp = s.get(page)
        links = sorted({urljoin(resp.url, h) for h in LINK_RE.findall(resp.text) if FILE_HINT.search(h)})
        out["result"] += f"; page HTTP {resp.status_code}, {len(links)} candidate file links"
        out["evidence"] += " | links: " + " ; ".join(links[:12])
        hint = FILE_HINTS.get(r["ccn"])
        mine = [u for u in links if hint and hint in u]
        if len(mine) == 1:
            out["found_mrf_url"] = mine[0]
            out["result"] += "; file found on price page"
    except RobotsDisallowed:
        out["result"] += "; " + robots_reason(s, page) + " (price transparency page)"
    except requests.RequestException as e:
        out["result"] += f"; page not reachable ({str(e)[:120]})"
    return out


def head_freshness(s: PoliteSession, url: str) -> dict:
    res = {"head_status": "", "last_modified": "", "content_length": "", "head_note": "", "head_at": now_utc()}
    try:
        resp = s.head(url)
        res.update(head_status=str(resp.status_code), last_modified=resp.headers.get("Last-Modified", ""),
                   content_length=resp.headers.get("Content-Length", ""))
        if resp.url != url:
            res["head_note"] = f"redirected to {resp.url}"
    except RobotsDisallowed:
        res["head_note"] = robots_reason(s, url) + "; not requested"
    except requests.RequestException as e:
        res["head_note"] = f"error: {str(e)[:150]}"
    return res


def main() -> None:
    with open(REGISTRY_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    s = PoliteSession()
    hpt_cache: dict = {}
    findings = []
    for r in rows:
        if needs_recheck(r):
            f = recheck_discovery(s, r, hpt_cache)
            findings.append(f)
            print(f["ccn"], f["name"], "|", f["result"], "|", f["found_mrf_url"])
            r["recheck_result"] = f"{f['step']}: {f['result']}"
            r["recheck_at"] = f["retrieved_at"]
            if f["found_mrf_url"] and f["found_mrf_url"] != r["mrf_url"]:
                r["audit_mrf_url"] = r["mrf_url"]
                r["mrf_url"] = f["found_mrf_url"]
            if f["found_mrf_url"]:
                r["discovery_method"] = "cms-hpt.txt" if f["step"] == "cms-hpt.txt" else "price transparency page"
            elif "disallows" in f["result"] or "not reachable" in f["result"] or "HTTP 403" in f["result"]:
                r["discovery_method"] = "manual"
                r["status"] = "blocked"
    for r in rows:
        if r["mrf_url"].startswith("http"):
            h = head_freshness(s, r["mrf_url"])
            r.update(h)
            if "disallows" in h["head_note"]:
                r["status"] = "blocked"
            print("HEAD", r["ccn"], h["head_status"], h["last_modified"], h["content_length"], h["head_note"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0]))
        w.writeheader()
        w.writerows(findings)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(REGISTRY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    robots = PROCESSED / "robots_snapshots.csv"
    with open(robots, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["host", "robots_txt_excerpt", "source_url", "retrieved_at"])
        for host, text in s.robots_text.items():
            w.writerow([host, text[:2000], f"https://{host}/robots.txt", now_utc()])


if __name__ == "__main__":
    main()
