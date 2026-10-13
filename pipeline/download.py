"""Download hospital MRFs once per run: streamed to disk, sha256 computed while streaming.

A file is skipped when the manifest already holds it with the same Last-Modified (or, if the server sends
none, the same Content-Length) and the local file still matches the recorded sha256.
"""
import csv
import hashlib
import pathlib
import re
from urllib.parse import unquote, urlsplit

from pipeline.common import PROCESSED, RAW, ROOT, now_utc
from pipeline.http import PoliteSession

MANIFEST = PROCESSED / "downloads.csv"
FIELDS = ["ccn", "url", "final_url", "path", "sha256", "size_bytes", "http_last_modified", "http_content_length",
          "http_etag", "status", "note", "source_url", "retrieved_at"]
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
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows.values())


def local_name(ccn: str, url: str, final_url: str) -> str:
    base = unquote(urlsplit(final_url or url).path.rstrip("/").rsplit("/", 1)[-1]) or "file"
    if "Download.aspx" in base or "." not in base:
        base = unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]) or "file"
    return f"{ccn}_{re.sub(r'[^A-Za-z0-9._-]+', '_', base)}"


def download(s: PoliteSession, ccn: str, url: str, manifest: dict, force: bool = False) -> dict:
    """One GET per file per run (F3: at most 1 request per hospital per run, plus robots.txt per host).

    Unchanged files are detected with a conditional GET (If-None-Match / If-Modified-Since -> 304). If the
    server ignores those headers and answers 200 with the same Last-Modified and Content-Length as last time,
    the connection is closed before the body is read and the local copy is re-hashed instead.
    """
    prev = manifest.get((ccn, url))
    have = None
    if prev and prev.get("status") == "ok" and prev.get("path") and (ROOT / prev["path"]).exists():
        have = prev
    partial = RAW / local_name(ccn, url, url)
    headers = {}
    if have and not force:
        if have.get("http_etag"):
            headers["If-None-Match"] = have["http_etag"]
        if have.get("http_last_modified"):
            headers["If-Modified-Since"] = have["http_last_modified"]
    elif prev and prev.get("status", "").startswith("error") and partial.exists() and prev.get("http_etag"):
        # Resume a broken transfer of the same version instead of starting again.
        headers = {"Range": f"bytes={partial.stat().st_size}-", "If-Range": prev["http_etag"]}
    row = {"ccn": ccn, "url": url, "source_url": url, "retrieved_at": now_utc(), "note": ""}
    with s.get(url, stream=True, timeout=(30, 300), headers=headers) as r:
        lm, cl = r.headers.get("Last-Modified", ""), r.headers.get("Content-Length", "")
        etag = r.headers.get("ETag", "")
        row.update(final_url=r.url, http_last_modified=lm or (have or {}).get("http_last_modified", ""),
                   http_content_length=cl, http_etag=etag or (have or {}).get("http_etag", ""))
        same = have and r.status_code == 200 and lm and lm == have.get("http_last_modified") and (
            not cl or cl == have.get("http_content_length") or cl == str(have.get("size_bytes")))
        # Some servers (the Valleywise portal) send neither Last-Modified nor ETag. Then the only signal without
        # downloading is the size; it is used and the note says so.
        size_only = (have and r.status_code == 200 and not lm and not etag and cl
                     and cl == str(have.get("size_bytes")))
        if have and (r.status_code == 304 or same or size_only):
            p = ROOT / have["path"]
            if sha256_file(p) == have["sha256"]:
                how = "same size, server sends no Last-Modified or ETag" if size_only else f"HTTP {r.status_code}"
                return {**have, "http_etag": row["http_etag"], "status": "ok",
                        "note": f"unchanged ({how}), download skipped {now_utc()}"}
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
    # Paths are stored relative to the repository root so the manifest is portable.
    row.update(path=str(path.relative_to(ROOT)), sha256=sha256_file(path), size_bytes=size, status="ok")
    if not resumed and cl and cl.isdigit() and int(cl) != size and "gzip" not in r.headers.get("Content-Encoding", ""):
        row["note"] = f"size {size} differs from Content-Length {cl}"
    return row
