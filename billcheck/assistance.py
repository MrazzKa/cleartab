"""Financial assistance finder (Feature 9).

Household income and size never leave the request: they are not logged or stored. Policies come from
data/processed/assistance_policies.json, read by hand from each health system's own documents.
"""
import json
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from pipeline.common import PROCESSED

POLICIES = PROCESSED / "assistance_policies.json"


class AssistanceRequest(BaseModel):
    household_size: int = Field(..., ge=1, le=20)
    annual_income: float = Field(..., ge=0, le=10_000_000)
    coverage: Literal["insured", "self_pay"] = "self_pay"
    hospital_system: str | None = Field(None, max_length=80, description="registry health_system, shown first")


@lru_cache(maxsize=1)
def policies() -> dict:
    return json.loads(POLICIES.read_text())


def poverty_line(household_size: int) -> float:
    g = policies()["poverty_guidelines"]
    return g["base"] + g["per_additional_person"] * (household_size - 1)


def fpl_percent(income: float, household_size: int) -> float:
    return round(100 * income / poverty_line(household_size), 1)


def match_tier(tiers: list[dict], pct: float) -> dict | None:
    """Bands read as (previous band's maximum, this band's maximum], and never below a band's own stated minimum.
    Banner's "< 200%" (stored as max 199.99) leaves 200% to the next band; CommonSpirit's "at or above 201%" leaves
    200.5% between the bands, as its policy is written (answered as "call and ask")."""
    ordered = sorted(tiers, key=lambda t: t["max_fpl"])
    for i, t in enumerate(ordered):
        if i == 0 and t.get("min_fpl", 0) <= pct <= t["max_fpl"]:
            return t
        if i > 0 and ordered[i - 1]["max_fpl"] < pct <= t["max_fpl"] and pct >= t.get("min_fpl", 0):
            return t
    return None


def evaluate(req: AssistanceRequest) -> dict:
    pct = fpl_percent(req.annual_income, req.household_size)
    g = policies()["poverty_guidelines"]
    out = []
    for s in policies()["systems"]:
        tiers = s["tiers"]
        key = "insured" if req.coverage == "insured" else "uninsured"
        if not tiers:
            status, label = "unknown", "Income limits are not published. Call and ask."
        elif req.coverage == "insured" and s.get("insured_eligible") is False:
            status, label = "not_eligible", "This policy does not cover insured patients."
        else:
            t = match_tier(tiers, pct)
            top = max(x["max_fpl"] for x in tiers)
            bottom = min(x.get("min_fpl", 0) for x in tiers)
            if t:
                status = "free" if t.get("discount_pct") == 100 else "discount"
                label = t[key]
            elif pct < bottom:
                status, label = "unknown", s.get("below_min", "Below the published bands. Call and ask.")
            elif pct > top:
                status, label = "above", s.get("above_max", "Above the published income limit.")
            else:
                status, label = "unknown", "Between published bands. Call and ask."
        out.append({"system": s["system"], "registry_systems": s["registry_systems"], "status": status,
                    "result": label, "nonprofit_501r": s["nonprofit_501r"], "covers": s["covers"],
                    "window": s["window"], "how_to_apply": s["how_to_apply"], "phone": s["phone"],
                    "application_url": s.get("application_url"), "documents": s.get("documents", []),
                    "send_to": s.get("send_to", ""), "policy": s["policy"],
                    "assets_test": s["assets_test"], "notes": s.get("notes", ""),
                    "source_url": s["source_url"], "page_url": s["page_url"], "retrieved_at": s["retrieved_at"]})
    rank = {"free": 0, "discount": 1, "above": 2, "unknown": 3, "not_eligible": 4}
    out.sort(key=lambda r: (req.hospital_system not in r["registry_systems"], rank[r["status"]], r["system"]))
    return {"fpl_percent": pct, "poverty_line": poverty_line(req.household_size),
            "guidelines": {"year": g["year"], "source_url": g["source_url"]}, "results": out,
            "note": ("Hospitals decide eligibility from your application and documents. These results come from "
                     "each hospital's published policy and are a guide, not a decision.")}
