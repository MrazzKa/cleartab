"""Read an EOB or bill photo into fields (Feature 10, optional, with the user's consent).

An open-weights vision model on Groq copies the numbers it sees into JSON. It never decides anything: the user
checks every number on screen before the rule engine runs, and the rule engine, not the model, produces the
findings. Images are sent to Groq for this one request and are not stored or logged by ClearTab. The prompt asks
the model to leave out names, addresses and member or account numbers.
"""
import base64
import json
import os

import requests
from pydantic import BaseModel, Field, ValidationError

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
TEXT_MODEL = os.environ.get("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")
MAX_BYTES = 8 * 1024 * 1024
TYPES = {"image/jpeg", "image/png", "image/webp"}
PDF_MAX_PAGES = 8
PDF_MAX_CHARS = 14000

PROMPT = """You read US medical billing documents (photos or text taken from a PDF). Copy what is printed; do not
calculate or guess.
The document may show an explanation of benefits (EOB) from an insurer, a bill from a provider, or both. Fill every
section for every document you see: EOB values go in you_owe_total and eob_lines, bill values go in balance_due,
patient_payments and bill_lines.
Return one JSON object with exactly these keys:
{"document_type": "eob" | "bill" | "both" | "other",
 "provider_type": "facility" | "professional" | "ambulance" | "unknown",
 "provider_name": string or null,          // the hospital, doctor group or ambulance company that billed
 "statement_date": "YYYY-MM-DD" or null,
 "claim_number": string or null,
 "balance_due": number or null,            // bill: amount due / balance / pay this amount
 "patient_payments": number or null,       // bill: payments the patient already made
 "you_owe_total": number or null,          // EOB: total patient responsibility / what you owe
 "eob_columns": [string],                  // EOB table: the money column headers, left to right
 "eob_lines": [{"amounts": [number],       // every dollar amount in this row, left to right, as printed
                "service_date": "YYYY-MM-DD" or null, "description": string, "code": string or null,
                "billed": number or null, "discount": number or null, "allowed": number or null,
                "copay": number or null,
                "deductible": number or null, "coinsurance": number or null, "not_covered": number or null,
                "plan_paid": number or null, "you_owe": number or null,
                "status": "paid" | "denied" | "pending" | "unknown"}],
 "bill_lines": [{"service_date": "YYYY-MM-DD" or null, "description": string, "code": string or null,
                 "units": integer or null, "amount": number or null}],
 "oop_max_met": true | false,             // true only if the document says an out-of-pocket maximum was met
 "unreadable": [string]                    // fields you could not read clearly
}
EOB columns go by many names. "discount" is the network discount, plan discount or provider write-off for that
line (not "amount you saved"). "allowed" is the allowed or approved amount; leave it null if it is not printed.
"you_owe" is patient responsibility. Copy one entry per service line and skip the totals row. In "amounts" copy
every dollar figure of the row in order, including $0.00, so that it lines up with "eob_columns".
Rules: numbers without $ or commas. Use null when a value is not printed or not legible. CPT/HCPCS codes are 5
characters (for example 73721, J1885). Leave out patient names, addresses, dates of birth, member IDs and account
numbers entirely. If the image is not an EOB or a medical bill, set document_type to "other" and leave the rest
empty."""


class ReadLine(BaseModel):
    amounts: list[float] = Field(default_factory=list, max_length=20)
    service_date: str | None = None
    description: str = ""
    code: str | None = Field(None, max_length=8)
    billed: float | None = None
    discount: float | None = None
    allowed: float | None = None
    copay: float | None = None
    deductible: float | None = None
    coinsurance: float | None = None
    not_covered: float | None = None
    plan_paid: float | None = None
    you_owe: float | None = None
    status: str = "unknown"
    units: int | None = None
    amount: float | None = None


class ReadResult(BaseModel):
    document_type: str = "other"
    provider_type: str = "unknown"
    provider_name: str | None = Field(None, max_length=120)
    statement_date: str | None = None
    claim_number: str | None = None
    balance_due: float | None = None
    patient_payments: float | None = None
    you_owe_total: float | None = None
    eob_columns: list[str] = Field(default_factory=list, max_length=20)
    eob_lines: list[ReadLine] = Field(default_factory=list)
    bill_lines: list[ReadLine] = Field(default_factory=list)
    oop_max_met: bool = False
    unreadable: list[str] = Field(default_factory=list)
    model: str = MODEL
    note: str = "Read by a language model. Check every number against your paper before running the check."


# EOB column headers -> EobLine fields. Checked in order; the first match wins. None = a subtotal we skip.
COLUMNS = [
    (("another source", "other source", "other insurance", "other carrier"), "other_source"),
    (("total plan", "plan discount & payments", "discounts & payments", "you saved", "amount saved"), None),
    (("not covered", "non-covered", "noncovered", "not allowed", "ineligible"), "not_covered"),
    (("discount", "write", "adjust", "savings"), "discount"),
    (("allowed", "approved", "eligible", "negotiated", "covered amount"), "allowed"),
    (("deductible",), "deductible"),
    (("coinsurance", "co-insurance"), "coinsurance"),
    (("copay", "co-pay", "copayment"), "copay"),
    (("plan paid", "paid by", "plan pays", "insurance paid", "benefit", "we paid", "amount paid"), "plan_paid"),
    (("responsibility", "you owe", "owe", "patient pays", "your share", "what you"), "you_owe"),
    (("billed", "charge", "amount billed"), "billed"),
]


def column_field(header: str) -> str | None:
    h = " ".join(header.lower().split())
    for keys, field in COLUMNS:
        if any(k in h for k in keys):
            return field
    return "?"


def align_columns(res: "ReadResult") -> "ReadResult":
    """Put each row's amounts under the printed column headers with fixed rules, so the language model only copies
    and never decides which number is which. Rows whose count does not match the headers keep the model's fields."""
    NON_MONEY = ("service", "product", "date", "description", "code", "note", "claim", "provider", "remark")
    fields = [column_field(h) for h in res.eob_columns
              if not (column_field(h) == "?" and any(k in h.lower() for k in NON_MONEY))]
    if not fields or "?" in fields:
        return res
    for ln in res.eob_lines:
        if len(ln.amounts) != len(fields):
            continue
        vals: dict[str, float] = {}
        for f, v in zip(fields, ln.amounts, strict=True):
            if f and f != "other_source":
                vals[f] = round(vals.get(f, 0) + v, 2)
        for f in ("billed", "discount", "allowed", "plan_paid", "you_owe"):
            setattr(ln, f, vals.get(f))
        for f in ("copay", "deductible", "coinsurance", "not_covered"):
            setattr(ln, f, vals.get(f, 0))
        if "plan_paid" in vals and "other_source" in fields:
            ln.plan_paid = round(vals["plan_paid"] + ln.amounts[fields.index("other_source")], 2)
    return res


class ReaderError(Exception):
    pass


def available() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def pdf_text(data: bytes) -> str:
    """Text of the pages that show dollar amounts. A scanned PDF has no text layer and returns ''."""
    import io
    import logging

    logging.getLogger("pypdf").setLevel(logging.ERROR)     # font warnings on every page are noise here
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    try:
        pdf = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in pdf.pages[:PDF_MAX_PAGES]]
    except (PdfReadError, ValueError, KeyError) as e:
        raise ReaderError("This PDF could not be opened. Take a photo of the pages instead.") from e
    keep = [t for t in pages if "$" in t] or pages
    return "\n\n".join(t.strip() for t in keep)[:PDF_MAX_CHARS]


def read_document(images: list[tuple[bytes, str]], session=requests) -> ReadResult:
    """images: [(bytes, content_type)]: one to three photos, or one PDF."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ReaderError("Photo reading is not set up on this server. Enter the numbers by hand.")
    if not 1 <= len(images) <= 3:
        raise ReaderError("Send one to three photos.")
    if any(len(d) > MAX_BYTES for d, _ in images):
        raise ReaderError("Each file must be under 8 MB.")
    if images[0][1] == "application/pdf":
        if len(images) > 1:
            raise ReaderError("Send one PDF at a time.")
        text = pdf_text(images[0][0])
        if len(text.strip()) < 40:
            raise ReaderError("This PDF is a scan without text. Take a photo of each page instead.")
        model = TEXT_MODEL
        body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": PROMPT + "\n\nDocument text:\n" + text}]}
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"
    else:
        content = [{"type": "text", "text": PROMPT}]
        for data, ctype in images:
            if ctype not in TYPES:
                raise ReaderError("Use a JPEG, PNG or WebP photo, or a PDF.")
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:{ctype};base64,{base64.b64encode(data).decode()}"}})
        model = MODEL
        body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": content}]}
        if model.startswith("qwen/"):
            body["reasoning_effort"] = "none"
            body["max_completion_tokens"] = 900    # Groq free tier caps this model at 1,000 output tokens per minute
    try:
        r = session.post(GROQ_URL, json=body, timeout=90, headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise ReaderError("The reader did not respond. Try again or enter the numbers by hand.") from e
    if r.status_code == 429:
        raise ReaderError("The reader is busy (429). Wait a minute and try again.")
    if r.status_code != 200:
        raise ReaderError(f"The reader returned an error ({r.status_code}). Enter the numbers by hand.")
    try:
        raw = json.loads(r.json()["choices"][0]["message"]["content"])
        res = ReadResult(**{k: v for k, v in raw.items() if k in ReadResult.model_fields and k != "model"})
        res.model = model
        return align_columns(res)
    except (KeyError, IndexError, json.JSONDecodeError, ValidationError, TypeError) as e:
        raise ReaderError("The document could not be read. Try a sharper photo or enter the numbers by hand.") from e
