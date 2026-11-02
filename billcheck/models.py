"""Input and output of a bill check (Feature 7).

The input is what a patient holds: the insurer's explanation of benefits (EOB) and the provider's bill, plus a
few facts about the visit. Nothing here identifies the patient; names and account numbers are filled into the
dispute letter in the browser and never sent to the server.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Money = float


class EobLine(BaseModel):
    line: int | None = None
    service_date: date | None = None
    description: str = ""
    code: str | None = Field(None, max_length=8, description="CPT or HCPCS code, if the EOB shows it")
    units: int = Field(1, ge=1, le=999)
    billed: Money | None = Field(None, ge=0, description="provider charges")
    allowed: Money | None = Field(None, ge=0, description="allowed charges, the insurer's contracted amount")
    copay: Money = Field(0, ge=0)
    deductible: Money = Field(0, ge=0)
    coinsurance: Money = Field(0, ge=0)
    not_covered: Money = Field(0, ge=0)
    plan_paid: Money | None = Field(None, ge=0)
    you_owe: Money | None = Field(None, ge=0)
    status: Literal["paid", "denied", "pending", "adjusted", "unknown"] = "unknown"
    remark: str = ""


class Eob(BaseModel):
    claim_number: str | None = Field(None, max_length=40)
    lines: list[EobLine] = Field(default_factory=list, max_length=200)
    you_owe_total: Money | None = Field(None, ge=0, description="the EOB's own total, if printed")


class BillLine(BaseModel):
    service_date: date | None = None
    description: str = ""
    code: str | None = Field(None, max_length=8)
    revenue_code: str | None = Field(None, max_length=4)
    units: int = Field(1, ge=1, le=999)
    amount: Money = Field(..., ge=0)


class Bill(BaseModel):
    provider_type: Literal["facility", "professional", "ambulance", "unknown"] = "unknown"
    statement_date: date | None = None
    lines: list[BillLine] = Field(default_factory=list, max_length=500)
    insurance_paid: Money = Field(0, ge=0)
    adjustments: Money = Field(0, ge=0)
    patient_payments: Money = Field(0, ge=0, description="what the patient already paid this provider")
    balance_due: Money | None = Field(None, ge=0)


class Context(BaseModel):
    coverage: Literal["insured", "self_pay"] = "insured"
    hospital_ccn: str | None = Field(None, max_length=10)
    insurer: str | None = Field(None, max_length=80, description="canonical insurer name from GET /plans")
    network: Literal["in", "out", "unknown"] = "unknown"
    emergency: bool = False
    ambulance: Literal["none", "ground", "air"] = "none"
    ambulance_con: str | None = Field(None, max_length=10, description="ADHS certificate of necessity number")
    ambulance_level: Literal["als", "bls", "ccs", "unknown"] = "unknown"
    ambulance_miles: float | None = Field(None, ge=0, le=1000)
    transported: bool | None = None
    good_faith_estimate: Money | None = Field(None, ge=0, description="self-pay: the provider's estimate total")
    gfe_received: bool = False
    today: date | None = None
    lang: Literal["en", "es"] = "en"


class CheckRequest(BaseModel):
    context: Context = Field(default_factory=Context)
    eob: Eob | None = None
    bill: Bill | None = None


Severity = Literal["error", "warning", "info", "ok"]


class Source(BaseModel):
    name: str
    url: str | None = None
    as_of: str | None = None


class Finding(BaseModel):
    rule: str
    severity: Severity
    title: str
    explanation: str
    action: str = ""
    lines: list[int] = Field(default_factory=list, description="bill or EOB line numbers involved (1-based)")
    evidence: dict = Field(default_factory=dict)
    amount_at_stake: Money | None = None
    sources: list[Source] = Field(default_factory=list)


class Summary(BaseModel):
    verdict: Literal["looks_right", "questions", "likely_errors", "not_enough_data"]
    headline: str
    eob_you_owe: Money | None = None
    bill_balance: Money | None = None
    difference: Money | None = None
    amount_at_stake: Money = 0
    counts: dict[str, int] = Field(default_factory=dict)


class CheckResult(BaseModel):
    summary: Summary
    findings: list[Finding]
    checks_run: list[str]
    checks_skipped: dict[str, str] = Field(default_factory=dict)
    letter: str = ""
    call_script: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "ClearTab compares the numbers you entered with published rules and prices. It is not legal or medical "
        "advice, and a flag means 'ask about this', not 'this is wrong'.")
