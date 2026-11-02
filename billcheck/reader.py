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
MAX_BYTES = 8 * 1024 * 1024
TYPES = {"image/jpeg", "image/png", "image/webp"}

PROMPT = """You read photos of US medical billing documents. Copy what is printed; do not calculate or guess.
The photos may show an explanation of benefits (EOB) from an insurer, a bill from a provider, or both. Fill every
section for every document you see: EOB values go in you_owe_total and eob_lines, bill values go in balance_due,
patient_payments and bill_lines.
Return one JSON object with exactly these keys:
{"document_type": "eob" | "bill" | "both" | "other",
 "provider_type": "facility" | "professional" | "ambulance" | "unknown",
 "statement_date": "YYYY-MM-DD" or null,
 "claim_number": string or null,
 "balance_due": number or null,            // bill: amount due / balance / pay this amount
 "patient_payments": number or null,       // bill: payments the patient already made
 "you_owe_total": number or null,          // EOB: total patient responsibility / what you owe
 "eob_lines": [{"service_date": "YYYY-MM-DD" or null, "description": string, "code": string or null,
                "billed": number or null, "allowed": number or null, "copay": number or null,
                "deductible": number or null, "coinsurance": number or null, "not_covered": number or null,
                "plan_paid": number or null, "you_owe": number or null,
                "status": "paid" | "denied" | "pending" | "unknown"}],
 "bill_lines": [{"service_date": "YYYY-MM-DD" or null, "description": string, "code": string or null,
                 "units": integer or null, "amount": number or null}],
 "unreadable": [string]                    // fields you could not read clearly
}
Rules: numbers without $ or commas. Use null when a value is not printed or not legible. CPT/HCPCS codes are 5
characters (for example 73721, J1885). Leave out patient names, addresses, dates of birth, member IDs and account
numbers entirely. If the image is not an EOB or a medical bill, set document_type to "other" and leave the rest
empty."""


class ReadLine(BaseModel):
    service_date: str | None = None
    description: str = ""
    code: str | None = Field(None, max_length=8)
    billed: float | None = None
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
    statement_date: str | None = None
    claim_number: str | None = None
    balance_due: float | None = None
    patient_payments: float | None = None
    you_owe_total: float | None = None
    eob_lines: list[ReadLine] = Field(default_factory=list)
    bill_lines: list[ReadLine] = Field(default_factory=list)
    unreadable: list[str] = Field(default_factory=list)
    model: str = MODEL
    note: str = "Read by a language model. Check every number against your paper before running the check."


class ReaderError(Exception):
    pass


def available() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def read_document(images: list[tuple[bytes, str]], session=requests) -> ReadResult:
    """images: [(bytes, content_type)], at most 3 (the model's limit)."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ReaderError("Photo reading is not set up on this server. Enter the numbers by hand.")
    if not 1 <= len(images) <= 3:
        raise ReaderError("Send one to three photos.")
    content = [{"type": "text", "text": PROMPT}]
    for data, ctype in images:
        if ctype not in TYPES:
            raise ReaderError("Use a JPEG, PNG or WebP photo.")
        if len(data) > MAX_BYTES:
            raise ReaderError("Each photo must be under 8 MB.")
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:{ctype};base64,{base64.b64encode(data).decode()}"}})
    body = {"model": MODEL, "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": content}]}
    if MODEL.startswith("qwen/"):
        body["reasoning_effort"] = "none"
        body["max_completion_tokens"] = 900    # Groq free tier caps this model at 1,000 output tokens per minute
    try:
        r = session.post(GROQ_URL, json=body, timeout=60, headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise ReaderError("The photo reader did not respond. Try again or enter the numbers by hand.") from e
    if r.status_code == 429:
        raise ReaderError("The photo reader is busy (429). Wait a minute and try again.")
    if r.status_code != 200:
        raise ReaderError(f"The photo reader returned an error ({r.status_code}). Enter the numbers by hand.")
    try:
        raw = json.loads(r.json()["choices"][0]["message"]["content"])
        return ReadResult(**{k: v for k, v in raw.items() if k in ReadResult.model_fields and k != "model"})
    except (KeyError, IndexError, json.JSONDecodeError, ValidationError, TypeError) as e:
        raise ReaderError("The photo could not be read. Try a sharper photo or enter the numbers by hand.") from e
