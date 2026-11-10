"""Read an EOB or a bill on ClearTab's own server, with no outside service (Feature 10, local mode).

Text and its position come from the PDF text layer (pdfplumber) or, for photos and scanned PDFs, from text
recognition that runs on this server (RapidOCR, ONNX models, no network after the models are installed). Fixed
rules then rebuild the table: money columns are found from the rows that carry the same number of dollar amounts,
each column's header is the text printed above it, and each amount is placed under its header with the same
column rules as the language-model reader (reader.COLUMNS). No language model is involved, so nothing is guessed:
what the rules cannot place is left empty and listed as unreadable, and the user checks every number on screen.

The document never leaves the server and is not stored or logged.
"""
import io
import re
from dataclasses import dataclass
from functools import lru_cache
from statistics import median

from billcheck.reader import ReaderError, ReadLine, ReadResult, align_columns, column_field

ENGINE = "ClearTab text recognition on our server (RapidOCR, no AI service)"
MONEY = re.compile(r"\(?(-?)\s?\$?\s?(-?)(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2})\)?")
DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b")
CODE = re.compile(r"\b(\d{5}|[A-V]\d{4})\b")
TOTAL_WORDS = ("total", "subtotal", "sum ")
EOB_WORDS = ("explanation of benefits", "this is not a bill", "plan paid", "allowed amount", "plan allowed",
             "your plan paid", "patient responsibility", "amount you owe", "you owe")
BILL_SUMMARY = ("total charges", "insurance", "adjustment", "payment", "balance", "amount due", "pay this",
                "please pay", "due date", "total due", "credit", "discount")
BALANCE_KEYS = ("balance due", "amount due", "total due", "pay this amount", "please pay", "patient balance",
                "amount you owe", "new balance", "balance")
INSURERS = [
    ("unitedhealthcare", "UnitedHealthcare"), ("united healthcare", "UnitedHealthcare"), ("uhc", "UnitedHealthcare"),
    ("blue cross", "Blue Cross Blue Shield of Arizona"), ("bcbs", "Blue Cross Blue Shield of Arizona"),
    ("banner|aetna", "Banner Aetna"), ("aetna", "Aetna"), ("cigna", "Cigna"), ("humana", "Humana"),
    ("mercy care", "Mercy Care"), ("health net", "Health Net"), ("ambetter", "Ambetter"), ("oscar", "Oscar"),
    ("ahcccs", "AHCCCS"), ("tricare", "TRICARE"), ("medicare", "Medicare"),
]
MAX_SIDE = int(__import__("os").environ.get("OCR_MAX_SIDE", "2400"))


@dataclass
class Box:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def h(self) -> float:
        return max(self.y1 - self.y0, 1)


# ---------------------------------------------------------------- text with positions

def pdf_boxes(data: bytes, max_pages: int = 8) -> list[Box]:
    """Words from the PDF text layer, joined into phrases (one table cell is usually one phrase)."""
    import pdfplumber
    out: list[Box] = []
    offset = 0.0
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages[:max_pages]:
                # Rotated text (a diagonal "SAMPLE" or "COPY" watermark) would break table rows: keep upright text.
                page = page.filter(lambda o: o.get("object_type") != "char" or _level(o))
                words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
                out += _phrases([Box(w["x0"], w["top"] + offset, w["x1"], w["bottom"] + offset, w["text"])
                                 for w in words])
                offset += float(page.height) + 40
    except Exception as e:  # pdfminer raises many kinds of errors on broken files
        raise ReaderError("This PDF could not be opened. Take a photo of the pages instead.") from e
    return out


def _level(ch: dict) -> bool:
    """A character drawn without rotation (pdfplumber's "upright" is also true for slightly turned text)."""
    m = ch.get("matrix") or (1, 0, 0, 1, 0, 0)
    return abs(m[1]) < 0.01 and abs(m[2]) < 0.01


def _phrases(words: list[Box]) -> list[Box]:
    out: list[Box] = []
    for ln in group_lines(words):
        cur = None
        for w in ln:
            if cur and w.x0 - cur.x1 < 0.6 * min(w.h, cur.h) and not (MONEY.fullmatch(w.text) and cur.text):
                cur = Box(cur.x0, min(cur.y0, w.y0), w.x1, max(cur.y1, w.y1), cur.text + " " + w.text)
            else:
                if cur:
                    out.append(cur)
                cur = w
        if cur:
            out.append(cur)
    return out


@lru_cache(maxsize=1)
def _engine():
    """PP-OCRv4 mobile detection (twice as fast as v6 on a full page, same boxes on printed documents) with the
    PP-OCRv6 small recognizer. Pages are photographed upright, so the angle classifier is not used."""
    from rapidocr import ModelType, OCRVersion, RapidOCR
    return RapidOCR(params={"Det.ocr_version": OCRVersion.PPOCRV4, "Det.model_type": ModelType.MOBILE,
                            "Global.use_cls": False, "Global.log_level": "warning"})


def image_boxes(data: bytes) -> list[Box]:
    """Text recognition on this server. Large photos are scaled down first; nothing is written to disk."""
    import numpy as np
    from PIL import Image, ImageOps
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    except Exception as e:
        raise ReaderError("This photo could not be opened. Use a JPEG or PNG.") from e
    scale = min(1.0, MAX_SIDE / max(img.size))
    if scale < 1:
        img = img.resize((round(img.width * scale), round(img.height * scale)))
    res = _engine()(np.asarray(img)[:, :, ::-1], use_cls=False)     # RGB -> BGR, as OpenCV expects
    if res is None or res.boxes is None:
        return []
    out = []
    for b, t in zip(res.boxes, res.txts, strict=False):
        xs, ys = [p[0] for p in b], [p[1] for p in b]
        out.append(Box(float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys)), str(t)))
    return out


def scanned_pdf_boxes(data: bytes, max_pages: int = 4) -> list[Box]:
    """A PDF without a text layer: render each page and recognize it like a photo."""
    import pypdfium2 as pdfium
    out: list[Box] = []
    offset = 0.0
    pdf = pdfium.PdfDocument(data)
    for i in range(min(len(pdf), max_pages)):
        img = pdf[i].render(scale=2.5).to_pil()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        for b in image_boxes(buf.getvalue()):
            out.append(Box(b.x0, b.y0 + offset, b.x1, b.y1 + offset, b.text))
        offset += img.height + 40
    return out


# ---------------------------------------------------------------- layout

def group_lines(boxes: list[Box]) -> list[list[Box]]:
    """Boxes whose vertical centers fall inside each other's height form one printed line, left to right."""
    lines: list[list[Box]] = []
    for b in sorted(boxes, key=lambda b: (b.cy, b.x0)):
        if lines:
            last = lines[-1]
            ref = median(x.cy for x in last)
            if abs(b.cy - ref) < 0.5 * median(x.h for x in last):
                last.append(b)
                continue
        lines.append([b])
    return [sorted(ln, key=lambda b: b.x0) for ln in lines]


def money_in(b: Box) -> list[tuple[float, float]]:
    """(amount, x center) for every dollar amount in a box; several amounts share the box width by position."""
    out = []
    n = max(len(b.text), 1)
    for m in MONEY.finditer(b.text):
        neg = bool(m.group(1) or m.group(2)) or (m.group(0).startswith("(") and m.group(0).endswith(")"))
        v = float(m.group(3).replace(",", "") + "." + m.group(4))
        mid = (m.start() + m.end()) / 2 / n
        out.append((-v if neg else v, b.x0 + (b.x1 - b.x0) * mid))
    return out


def _words(b: Box, centers: list[float]) -> list[tuple[str, float]]:
    """A header box that spans two money columns ("deductible Copay") is split into words placed by position."""
    spans = sum(1 for c in centers if b.x0 < c < b.x1)
    if spans < 2 or " " not in b.text.strip():
        return [(b.text, b.cx)]
    out, pos, n = [], 0, len(b.text)
    for w in b.text.split(" "):
        mid = (pos + len(w) / 2) / n
        out.append((w, b.x0 + (b.x1 - b.x0) * mid))
        pos += len(w) + 1
    return out


def line_text(ln: list[Box]) -> str:
    return " ".join(b.text for b in ln)


def iso(d: re.Match | None) -> str | None:
    if not d:
        return None
    mo, dy, yr = int(d.group(1)), int(d.group(2)), int(d.group(3))
    yr = yr + 2000 if yr < 100 else yr
    return f"{yr:04d}-{mo:02d}-{dy:02d}" if 1 <= mo <= 12 and 1 <= dy <= 31 else None


# ---------------------------------------------------------------- parsing

def parse(boxes: list[Box]) -> ReadResult:
    lines = group_lines(boxes)
    text = "\n".join(line_text(ln) for ln in lines)
    low = text.lower()
    res = ReadResult(model=ENGINE, note=("Read on ClearTab's server by text recognition; nothing was sent to an "
                                         "outside service. Check every number against your paper."))
    res.provider_name, res.insurer_name = _provider(lines), _insurer(low)
    m = re.search(r"statement date[:\s]*" + DATE.pattern, low)
    res.statement_date = iso(DATE.search(m.group(0))) if m else None
    m = re.search(r"claim (?:number|no\.?|#)[:\s]*([A-Z0-9-]{4,})", text, re.I)
    res.claim_number = m.group(1) if m else None
    oop = re.search(r"out[- ]of[- ]pocket[^.\n]{0,20}(?:maximum|max|limit)[^.\n]{0,40}?\b(?:met|reached)\b", low)
    res.oop_max_met = bool(oop) and not re.search(r"\b(?:not|n't)\b", oop.group(0))

    _eob_table(lines, res)
    _balances(lines, res)
    _bill(lines, res)
    is_eob = bool(res.eob_lines) or any(w in low for w in EOB_WORDS[:2])
    is_bill = res.balance_due is not None
    res.document_type = "both" if is_eob and is_bill else "eob" if is_eob else "bill" if is_bill else "other"
    if res.document_type == "other":
        res.unreadable.append("no EOB table or amount due was found")
    return res


def _provider(lines: list[list[Box]]) -> str | None:
    from billcheck import er
    for ln in lines:
        t = line_text(ln)
        ccn = er.find_hospital(t)
        if ccn:
            return er.hospital_name(ccn)
    for ln in lines:
        m = re.search(r"\b(?:provider|facility|hospital|billed by)\s*(?:name)?\s*:\s*([^:]{4,80}?)(?:\s{2,}|\s+\w+:|$)",
                      line_text(ln), re.I)
        if m:
            return m.group(1).strip()
    return None


def _insurer(low: str) -> str | None:
    for key, name in INSURERS:
        if key in low:
            return name
    return None


def _table(lines: list[list[Box]], counted: list, n: int) -> dict | None:
    """The table whose rows carry n dollar amounts: rows, totals, money column centers and headers."""
    rows = [(i, a) for i, a in counted if len(a) == n and not any(w in line_text(lines[i]).lower() for w in TOTAL_WORDS)]
    totals = [(i, a) for i, a in counted if len(a) == n and any(w in line_text(lines[i]).lower() for w in TOTAL_WORDS)]
    if not rows:
        return None
    centers = [median(sorted(a, key=lambda t: t[1])[k][1] for _, a in rows) for k in range(n)]
    gap = min((centers[k + 1] - centers[k] for k in range(n - 1)), default=200)

    # Header: the block of lines right above the first row (stops at a blank gap or a "Label: value" line). Each
    # word goes under the nearest money column; multi-line headers stack.
    first = rows[0][0]
    block: list[list[Box]] = []
    top = min(b.y0 for b in lines[first])
    for ln in reversed(lines[max(0, first - 8):first]):
        h = median(b.h for b in ln)
        if top - max(b.y1 for b in ln) > 1.6 * h or any(money_in(b) for b in ln) \
                or re.search(r"\w:\s", line_text(ln)):
            break
        block.insert(0, ln)
        top = min(b.y0 for b in ln)
    parts: list[list[str]] = [[] for _ in range(n)]
    for ln in block:
        line_parts = ["" for _ in range(n)]
        for b in ln:
            for word, cx in _words(b, centers):
                k = min(range(n), key=lambda k: abs(centers[k] - cx))
                if abs(centers[k] - cx) <= 0.6 * gap:
                    line_parts[k] = (line_parts[k] + " " + word).strip()
        for k, t in enumerate(line_parts):
            if t:
                parts[k].append(t)
    return {"rows": rows, "totals": totals, "centers": centers, "gap": gap, "head": [_header(p) for p in parts]}


def _header(parts: list[str]) -> str:
    """The shortest bottom part of a stacked header that names a known column: a group title printed above
    ("Total you owe" over "Coinsurance") must not decide the column."""
    for j in range(len(parts) - 1, -1, -1):
        h = " ".join(parts[j:])
        if column_field(h) != "?":
            return parts[-1] if column_field(parts[-1]) == column_field(h) else h
    return " ".join(parts) or "?"


def _eob_table(lines: list[list[Box]], res: ReadResult) -> None:
    counted = [(i, [a for b in ln for a in money_in(b)]) for i, ln in enumerate(lines)]
    counts = [len(a) for _, a in counted if len(a) >= 3]
    if not counts:
        return
    # The claim table is the widest table whose headers name what the patient owes or what the plan allowed;
    # a plan balances box (maximum, so far, remaining) also has rows of amounts but is not the claim.
    tables = {k: _table(lines, counted, k) for k in sorted(set(counts), reverse=True)}
    pick = next((k for k, t in tables.items() if t and {"you_owe", "allowed"} & {column_field(h) for h in t["head"]}),
                max(set(counts), key=lambda k: (counts.count(k), k)))
    t = tables[pick]
    if not t:
        return
    rows, totals, centers, gap = t["rows"], t["totals"], t["centers"], t["gap"]
    res.eob_columns = t["head"]

    for i, amounts in rows:
        ln = lines[i]
        left = [b for b in ln if b.x1 < centers[0] - 0.5 * gap and not money_in(b)]
        desc = " ".join(b.text for b in left)
        date = DATE.search(desc)
        code = CODE.search(DATE.sub("", desc))
        desc = DATE.sub("", desc).strip(" -:")
        res.eob_lines.append(ReadLine(amounts=[a for a, _ in sorted(amounts, key=lambda t: t[1])],
                                      service_date=iso(date), description=desc[:200],
                                      code=code.group(1) if code else None))
    align_columns(res)
    fields = [column_field(h) for h in res.eob_columns]
    if "?" in fields:
        res.unreadable.append("column headers")
    if "you_owe" in fields:
        k = fields.index("you_owe")
        if totals:
            res.you_owe_total = sorted(totals[-1][1], key=lambda t: t[1])[k][0]
        elif all(ln.you_owe is not None for ln in res.eob_lines):
            res.you_owe_total = round(sum(ln.you_owe for ln in res.eob_lines), 2)


def _balances(lines: list[list[Box]], res: ReadResult) -> None:
    """Plan balances box: rows named deductible or out-of-pocket with the limit, the amount used so far and what
    remains, left to right. Network and family/individual come from the row or the lines just above it."""
    from billcheck.models import PlanBalance
    network, level = "unknown", "unknown"
    for ln in lines:
        t = line_text(ln).lower()
        amounts = sorted((a for b in ln for a in money_in(b)), key=lambda x: x[1])
        if "out-of-network" in t or "out of network" in t or "non-network" in t:
            network = "out"
        elif re.search(r"\b(?:in[- ])?network\b", t):
            network = "in"
        if "family" in t:
            level = "family"
        elif "individual" in t or "member" in t and "balances" in t:
            level = "individual"
        kind = "deductible" if "deductible" in t else "out_of_pocket" if re.search(
            r"out[- ]of[- ]pocket|oop", t) else None
        if not kind or not 2 <= len(amounts) <= 3 or any(a < 0 for a, _ in amounts):
            continue
        if len(amounts) == 2 and not re.search(r"remaining|left|met|so far|applied|used", t):
            continue
        vals = [a for a, _ in amounts]
        limit, used, remaining = vals if len(vals) == 3 else (vals[0], vals[1], None)
        if len(vals) == 2 and re.search(r"remaining|left", t) and not re.search(r"so far|applied|used|met", t):
            limit, used, remaining = vals[0], None, vals[1]
        res.plan_balances.append(PlanBalance(kind=kind, network=network, level=level, limit=limit, used=used,
                                             remaining=remaining))
        if len(res.plan_balances) >= 12:
            break
    # A "Network" label printed once beside two rows (merged cell) lands on the second row only.
    for a, b in zip(res.plan_balances, res.plan_balances[1:], strict=False):
        if a.network == "unknown" and b.network == "in" and a.kind != b.kind:
            a.network = "in"


def _bill(lines: list[list[Box]], res: ReadResult) -> None:
    table_rows = {id(ln) for ln in lines if len([a for b in ln for a in money_in(b)]) >= 3}
    for key in BALANCE_KEYS:
        for i, ln in enumerate(lines):
            t = line_text(ln).lower()
            if key not in t or id(ln) in table_rows or (key == "amount you owe" and res.eob_lines):
                continue
            amounts = [a for b in ln for a in money_in(b)]
            if not amounts and i + 1 < len(lines):
                amounts = [a for b in lines[i + 1] for a in money_in(b)]
            if amounts:
                res.balance_due = abs(sorted(amounts, key=lambda t: t[1])[-1][0])
                break
        if res.balance_due is not None:
            break
    if res.eob_lines and res.balance_due is not None and res.you_owe_total == res.balance_due:
        res.balance_due = None          # "Amount you owe" on an EOB is not a bill balance
    for ln in lines:
        t = line_text(ln).lower()
        if "patient payment" in t or "payments received" in t or "you paid" in t or "paid by patient" in t:
            amounts = [a for b in ln for a in money_in(b)]
            if amounts:
                res.patient_payments = abs(amounts[-1][0])
    if res.balance_due is None:
        return
    for ln in lines:
        t = line_text(ln)
        amounts = [a for b in ln for a in money_in(b)]
        if len(amounts) != 1 or any(w in t.lower() for w in BILL_SUMMARY) or ":" in t:
            continue
        if not DATE.search(t) and not CODE.search(t):
            continue
        desc_boxes = [b for b in ln if not money_in(b) and not DATE.fullmatch(b.text.strip())
                      and not re.fullmatch(r"\d{3,5}|[A-V]\d{4}", b.text.strip())]
        codes = [b.text.strip() for b in ln if re.fullmatch(r"\d{4,5}|[A-V]\d{4}", b.text.strip())]
        res.bill_lines.append(ReadLine(service_date=iso(DATE.search(t)), description=" ".join(
            b.text for b in desc_boxes)[:200], code=codes[0] if codes else None, amount=amounts[0][0]))


def read_local(images: list[tuple[bytes, str]]) -> ReadResult:
    """One PDF, or one to three photos (pages of the same document)."""
    if images[0][1] == "application/pdf":
        boxes = pdf_boxes(images[0][0])
        if sum(len(b.text) for b in boxes) < 40:
            boxes = scanned_pdf_boxes(images[0][0])
    else:
        boxes, offset = [], 0.0
        for data, _ in images:
            page = image_boxes(data)
            boxes += [Box(b.x0, b.y0 + offset, b.x1, b.y1 + offset, b.text) for b in page]
            offset = max((b.y1 for b in boxes), default=0) + 40
    if not boxes:
        raise ReaderError("No text was found. Take a sharper photo in good light, or enter the numbers by hand.")
    return parse(boxes)
