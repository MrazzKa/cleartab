"""Download hospital MRFs once per run: streamed to disk, sha256 computed while streaming.

A file is skipped when the manifest already holds it with the same Last-Modified (or, if the server sends
none, the same Content-Length) and the local file still matches the recorded sha256.
"""
import csv
import hashlib
import pathlib
import re
from urllib.parse import unquote, urlsplit

from pipeline.common import PROCESSED, RAW, now_utc
from pipeline.http import PoliteSession

MANIFEST = PROCESSED / "downloads.csv"
FIELDS = ["ccn", "url", "final_url", "path", "sha256", "size_bytes", "http_last_modified", "http_content_length",
          "status", "note", "source_url", "retrieved_at"]
CHUNK = 1 << 20


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> dict[tuple[str, str], dict]:
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, newline="") as f:
        return {(r["ccn"], r["url"]): r for r in csv.DictReader(f)}


def save_manifest(rows: dict[tuple[str, str], dict]) -> None:
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows.values())


def local_name(ccn: str, url: str, final_url: str) -> str:
    base = unquote(urlsplit(final_url or url).path.rstrip("/").rsplit("/", 1)[-1]) or "file"
    if "Download.aspx" in base or "." not in base:
        base = unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]) or "file"
    return f"{ccn}_{re.sub(r'[^A-Za-z0-9._-]+', '_', base)}"


def download(s: PoliteSession, ccn: str, url: str, manifest: dict, force: bool = False) -> dict:
    prev = manifest.get((ccn, url))
    head = s.head(url)
    lm, cl = head.headers.get("Last-Modified", ""), head.headers.get("Content-Length", "")
    if prev and not force and prev["status"] == "ok":
        same_version = (lm and lm == prev["http_last_modified"]) or (not lm and cl and cl == prev["http_content_length"])
        p = pathlib.Path(prev["path"])
        if same_version and p.exists() and sha256_file(p) == prev["sha256"]:
            prev["note"] = f"unchanged, skipped on {now_utc()}"
            return prev
    row = {"ccn": ccn, "url": url, "http_last_modified": lm, "http_content_length": cl, "source_url": url,
           "retrieved_at": now_utc(), "note": ""}
    # Resume a broken transfer of the same file version (If-Range on ETag or Last-Modified) instead of
    # starting again; the whole file is hashed once complete.
    partial = RAW / local_name(ccn, url, url)
    headers = {}
    validator = head.headers.get("ETag") or lm
    if prev and prev.get("status", "").startswith("error") and partial.exists() and validator:
        headers = {"Range": f"bytes={partial.stat().st_size}-", "If-Range": validator}
    with s.get(url, stream=True, timeout=(30, 300), headers=headers) as r:
        row["final_url"] = r.url
        if r.status_code not in (200, 206):
            row.update(status=f"HTTP {r.status_code}", path="", sha256="", size_bytes=0)
            return row
        resumed = r.status_code == 206
        path = partial if resumed else RAW / local_name(ccn, url, r.url)
        with open(path, "ab" if resumed else "wb") as f:
            for block in r.iter_content(CHUNK):
                f.write(block)
        if resumed:
            row["note"] = f"resumed from byte {headers['Range'][6:-1]}"
    size = path.stat().st_size
    row.update(path=str(path), sha256=sha256_file(path), size_bytes=size, status="ok")
    if cl and cl.isdigit() and int(cl) != size and "gzip" not in r.headers.get("Content-Encoding", ""):
        row["note"] = f"size {size} differs from Content-Length {cl}"
    return row
