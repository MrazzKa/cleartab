"""R2 benchmark: synthetic EOB and bill pairs with planted billing errors (known answers, no personal data).

Each case is an in-network outpatient visit at Banner - University Medical Center Tucson (CCN 030064) with Blue
Cross Blue Shield of Arizona. Allowed amounts are drawn inside the hospital's published BCBS rates for the code
(data/processed/assistance_policies.json is not used here; rates are fixed below from the prices table, retrieved
2026-10-12). One error type is planted per case, or none.

Usage: python -m research.r2.cases          -> research/r2/data/cases.json (seed 20261102, pilot)
       R2_DATA=data_confirm python -m research.r2.cases --seed 20261111   (confirmatory set, see REPORT.md)
"""
import argparse
import json
import os
import pathlib
import random

SEED = 20261102
OUT = pathlib.Path(__file__).with_name(os.environ.get("R2_DATA", "data"))

# code: (description on bill, gross charge, published BCBS AZ fixed dollar rate min, max) at CCN 030064
SERVICES = {
    "73721": ("MRI JOINT LWR EXTREM W/O DYE", 3706.00, 712.68, 950.22),
    "71046": ("XR CHEST 2 VIEWS", 669.00, 83.62, 111.49),
    "80053": ("COMPREHENSIVE METABOLIC PANEL", 428.00, 10.56, 42.06),
    "85025": ("CBC W/AUTO DIFF", 42.50, 7.77, 30.93),
}
EXTRA = {"36415": ("VENIPUNCTURE", 25.00)}            # blood draw, used for "not on EOB"
ERRORS = ["none", "payment_not_subtracted", "balance_billing", "duplicate_line", "line_not_on_eob",
          "mue_units", "ncci_pair", "eob_math", "allowed_above_published"]
# rule ids a correct checker should raise for each planted error (the main one first)
EXPECTED = {
    "none": [],
    "payment_not_subtracted": ["balance_over_eob"],
    "balance_billing": ["balance_over_eob"],
    "duplicate_line": ["duplicate_line", "balance_over_eob"],
    "line_not_on_eob": ["bill_line_not_on_eob", "balance_over_eob"],
    "mue_units": ["mue_units"],
    "ncci_pair": ["ncci_pair"],
    "eob_math": ["eob_line_sum"],
    "allowed_above_published": ["allowed_vs_published"],
}
# plain-language error categories offered to language models (same mapping as EXPECTED main rule)
CATEGORIES = {
    "payment_not_subtracted": "a payment the patient already made is not subtracted",
    "balance_billing": "the bill asks for more than the EOB's patient responsibility (balance billing)",
    "duplicate_line": "a duplicate charge",
    "line_not_on_eob": "a charge on the bill that is not on the EOB",
    "mue_units": "too many units billed for a service",
    "ncci_pair": "two procedure codes billed together that should not be billed separately",
    "eob_math": "the EOB's own numbers do not add up",
    "allowed_above_published": "the allowed amount is above the hospital's published rate for this insurer",
}


def r2(x: float) -> float:
    return round(x + 0.0, 2)


def make_case(rng: random.Random, i: int, error: str) -> dict:
    codes = rng.sample(sorted(SERVICES), rng.randint(2, 3))
    if error == "mue_units" and "73721" not in codes:
        codes[0] = "73721"
    date = f"2026-{rng.randint(5, 9):02d}-{rng.randint(1, 28):02d}"
    deductible_left = rng.choice([0, 0, 250, 500, 1500])
    coins_rate = rng.choice([0.1, 0.2, 0.3])
    copay = rng.choice([0, 0, 25, 40])
    if error == "payment_not_subtracted":
        copay, deductible_left = 40, 0
        if codes[0] not in ("73721", "71046"):
            codes[0] = rng.choice([c for c in ("73721", "71046") if c not in codes] or ["73721"])
    eob_lines, bill_lines = [], []
    for n, code in enumerate(codes, 1):
        desc, gross, lo, hi = SERVICES[code]
        allowed = r2(rng.uniform(lo, hi))
        if error == "allowed_above_published" and n == 1:
            allowed = r2(hi * rng.uniform(1.15, 1.6))
        ded = r2(min(deductible_left, allowed))
        deductible_left -= ded
        cp = r2(min(copay, allowed - ded)) if n == 1 else 0
        coins = r2((allowed - ded - cp) * coins_rate) if allowed - ded - cp > 0 else 0.0
        paid = r2(allowed - ded - cp - coins)
        line = {"line": n, "service_date": date, "description": desc.title(), "code": code, "units": 1,
                "billed": gross, "allowed": allowed, "copay": float(cp), "deductible": ded, "coinsurance": coins,
                "not_covered": 0.0, "plan_paid": paid, "you_owe": r2(ded + cp + coins), "status": "paid"}
        eob_lines.append(line)
        bill_lines.append({"service_date": date, "description": desc, "code": code, "units": 1, "amount": gross})
    if error == "eob_math":
        eob_lines[0]["plan_paid"] = r2(eob_lines[0]["plan_paid"] + rng.choice([10, 25, 50]))
    if error == "ncci_pair":
        # facility outpatient PTP edit 45380 / 45378, modifier indicator 0 (CMS v323r0)
        for code, desc, gross, allowed in (("45380", "COLONOSCOPY W/BIOPSY", 4120.0, 1310.0),
                                           ("45378", "COLONOSCOPY DIAGNOSTIC", 3480.0, 0.0)):
            eob_lines.append({"line": len(eob_lines) + 1, "service_date": date, "description": desc.title(), "code": code,
                              "units": 1, "billed": gross, "allowed": allowed, "copay": 0.0, "deductible": 0.0,
                              "coinsurance": r2(allowed * coins_rate), "not_covered": 0.0,
                              "plan_paid": r2(allowed - allowed * coins_rate), "you_owe": r2(allowed * coins_rate),
                              "status": "paid"})
            bill_lines.append({"service_date": date, "description": desc, "code": code, "units": 1, "amount": gross})
    owed = r2(sum(x["you_owe"] for x in eob_lines))
    payments = float(copay) if copay and error == "payment_not_subtracted" else 0.0
    if copay and error != "payment_not_subtracted" and rng.random() < 0.5:
        payments = float(copay)
    correct_balance = r2(max(owed - payments, 0))
    balance = correct_balance
    if error == "payment_not_subtracted":
        correct_balance = r2(max(owed - payments, 0))
        balance = owed
    elif error == "balance_billing":
        balance = r2(correct_balance + (eob_lines[0]["billed"] - eob_lines[0]["allowed"]))
    elif error == "duplicate_line":
        dup = dict(bill_lines[-1])
        bill_lines.append(dup)
        balance = r2(correct_balance + dup["amount"])
    elif error == "line_not_on_eob":
        desc, amt = EXTRA["36415"]
        bill_lines.append({"service_date": date, "description": desc, "code": "36415", "units": 1, "amount": amt})
        balance = r2(correct_balance + amt)
    elif error == "mue_units":
        j = next(k for k, b in enumerate(bill_lines) if b["code"] == "73721")
        bill_lines[j]["units"] = 4
    # contractual adjustment = charges the hospital wrote off under its contract, so the statement adds up
    insurance_paid = r2(sum(x["plan_paid"] for x in eob_lines))
    adjustments = r2(sum(x["amount"] for x in bill_lines) - insurance_paid - payments - balance)
    request = {
        "context": {"coverage": "insured", "network": "in", "hospital_ccn": "030064",
                    "insurer": "Blue Cross Blue Shield of Arizona"},
        "eob": {"claim_number": f"R2-{i:04d}", "lines": eob_lines, "you_owe_total": owed},
        "bill": {"provider_type": "facility", "statement_date": "2026-10-15", "lines": bill_lines,
                 "insurance_paid": insurance_paid, "adjustments": adjustments,
                 "patient_payments": payments, "balance_due": balance},
    }
    return {"id": f"R2-{i:04d}", "error": error, "expected_rules": EXPECTED[error],
            "correct_balance": correct_balance, "request": request}


def as_text(case: dict) -> str:
    """The two documents as a patient would read them, in plain text."""
    rq = case["request"]
    e, b = rq["eob"], rq["bill"]
    out = ["EXPLANATION OF BENEFITS - THIS IS NOT A BILL", "Blue Cross Blue Shield of Arizona",
           f"Claim {e['claim_number']}  Provider: Banner - University Medical Center Tucson (in network)", "",
           "Line | Date | Service | Code | Provider charges | Allowed | Copay | Deductible | Coinsurance | "
           "Paid by insurer | What you owe"]
    for x in e["lines"]:
        out.append(f"{x['line']} | {x['service_date']} | {x['description']} | {x['code']} | {x['billed']:.2f} | "
                   f"{x['allowed']:.2f} | {x['copay']:.2f} | {x['deductible']:.2f} | {x['coinsurance']:.2f} | "
                   f"{x['plan_paid']:.2f} | {x['you_owe']:.2f}")
    out += [f"Total you owe: {e['you_owe_total']:.2f}", "", "HOSPITAL BILL - Banner - University Medical Center Tucson",
            f"Statement date {b['statement_date']}", "Date | Description | Code | Units | Charge"]
    for x in b["lines"]:
        out.append(f"{x['service_date']} | {x['description']} | {x['code']} | {x['units']} | {x['amount']:.2f}")
    out += [f"Insurance payments: -{b['insurance_paid']:.2f}",
            f"Contractual adjustments: -{b['adjustments']:.2f}",
            f"Patient payments received: -{b['patient_payments']:.2f}",
            f"AMOUNT DUE: {b['balance_due']:.2f}"]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    seed = ap.parse_args().seed
    rng = random.Random(seed)
    plan = ["none"] * 20 + [e for e in ERRORS[1:] for _ in range(10)]
    rng.shuffle(plan)
    cases = [make_case(rng, i + 1, err) for i, err in enumerate(plan)]
    for c in cases:
        c["text"] = as_text(c)
    OUT.mkdir(exist_ok=True)
    (OUT / "cases.json").write_text(json.dumps({"seed": seed, "categories": CATEGORIES, "cases": cases}, indent=1))
    print(len(cases), "cases;", {e: plan.count(e) for e in ERRORS})


if __name__ == "__main__":
    main()
