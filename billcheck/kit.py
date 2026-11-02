"""Dispute kit (Feature 8): a letter and a phone script assembled from the findings by template.

The letter is written in the patient's voice. Placeholders in square brackets ([Your name], [Account number]) are
filled in the browser, so personal details never reach the server.
"""
from billcheck.models import CheckRequest, CheckResult, Finding

ASK = {
    "balance_over_eob": "match the bill to my explanation of benefits (EOB) and correct the balance",
    "bill_line_not_on_eob": "submit the charges that are not on my EOB to my insurance before billing me",
    "duplicate_line": "remove the duplicate charge or explain why the service was billed more than once",
    "mue_units": "confirm the number of units billed and correct them if they are wrong",
    "ncci_pair": "explain why these codes were billed separately on the same day",
    "allowed_vs_published": "confirm which contract rate was applied to this service",
    "self_pay_over_cash": "apply your published discounted cash price to this service",
    "gfe_dispute": "review the charges above your good faith estimate",
    "eob_denied": "correct and resubmit the denied claim, or tell me what information is missing",
}


def m(x) -> str:
    return f"${x:,.2f}"


def statement(f: Finding) -> str:
    """One factual sentence per finding, in the patient's voice."""
    e = f.evidence
    if f.rule == "balance_over_eob":
        paid = f", and I have already paid {m(e['already_paid'])}" if e.get("already_paid") else ""
        return (f"My EOB for this claim shows that I owe {m(e['eob_you_owe'])}{paid}. Your bill asks for "
                f"{m(e['bill_balance'])}, which is {m(f.amount_at_stake)} more.")
    if f.rule == "bill_line_not_on_eob":
        return (f"The charges for {', '.join(e['codes'])} ({m(f.amount_at_stake)}) do not appear on my EOB, so they "
                "may not have been sent to my insurance.")
    if f.rule == "duplicate_line":
        return (f"The bill lists {e['service']} {e['times']} times on the same date for {m(e['amount'])} each.")
    if f.rule == "mue_units":
        return (f"{e['code']} is billed with {e['units']} units; the CMS medically unlikely edit for this code is "
                f"{e['limit']}.")
    if f.rule == "ncci_pair":
        return (f"{e['column_1']} and {e['column_2']} are billed on the same day; the CMS National Correct Coding "
                f"Initiative edits treat {e['column_2']} as part of {e['column_1']}.")
    if f.rule == "allowed_vs_published":
        return (f"For {e['code']}, my EOB shows an allowed amount of {m(e['allowed_per_unit'])}, but {e['hospital']} "
                f"published rates for my plan between {m(e['published_min'])} and {m(e['published_max'])}.")
    if f.rule == "self_pay_over_cash":
        return (f"For {e['code']}, I was billed {m(e['billed_per_unit'])}; {e['hospital']} publishes a discounted "
                f"cash price of {m(e['published_cash'])} for this service.")
    if f.rule == "gfe_dispute":
        return (f"My good faith estimate was {m(e['good_faith_estimate'])}, and the bill totals "
                f"{m(e['billed_total'])}, {m(f.amount_at_stake)} more.")
    if f.rule == "eob_denied":
        return "My insurer denied this claim."
    return f.title + "."


def build_kit(req: CheckRequest, res: CheckResult) -> tuple[str, list[str]]:
    issues = [f for f in res.findings if f.severity in ("error", "warning") and f.rule in ASK]
    if not issues:
        return "", []
    to_insurer = all(f.rule in ("allowed_vs_published", "eob_denied") for f in issues)
    claim = req.eob.claim_number if req.eob and req.eob.claim_number else "[Claim number]"
    lines = [
        "[Your name]", "[Your address]", "[Date]", "",
        "To: " + ("[Insurance company] member services" if to_insurer else "[Provider name] billing office"),
        f"Re: Account [Account number], claim {claim}, date of service [Date of service]", "",
        "Hello,", "",
        ("I compared my bill with your published prices and my good faith estimate"
         if req.context.coverage == "self_pay" else "I compared my bill with my explanation of benefits")
        + " and have questions about the charges below. "
        "Please put this account on hold while you review it, and do not send it to collections.", "",
    ]
    for n, f in enumerate(issues, 1):
        lines.append(f"{n}. {statement(f)} Please {ASK[f.rule]}.")
    lines += ["", "Please also send me an itemized bill with the CPT or HCPCS code, revenue code, date and units for "
              "each charge.", "",
              "Thank you. You can reach me at [Phone or email].", "", "[Your name]"]
    script = [
        "Have ready: the bill, the EOB, your insurance card, a pen.",
        "Ask first: 'Is this a hospital (facility) charge or a doctor (professional) charge?' Make sure you are "
        "talking to the right billing office.",
        "Say: 'I'm calling about account [Account number]. I compared the bill with my explanation of benefits "
        "and some amounts don't match.'",
    ]
    for f in issues:
        script.append(f"Say: '{statement(f)}' Ask: 'Can you {ASK[f.rule]}?'")
    script += [
        "Ask: 'Can you put the account on hold while this is reviewed?'",
        "Write down: the date, the name of the person, and a reference number for the call.",
        "If they will not fix it: ask how to file a formal dispute, and call your insurer with the same questions.",
    ]
    return "\n".join(lines), script
