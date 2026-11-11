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
    "ambulance_over_rate": "correct the charges to the rates approved by the Arizona Department of Health Services",
    "ambulance_no_transport": "explain what care I was billed for, or treat the call as gratuitous under A.R.S. 36-2239(K)",
    "er_rate_over": "confirm which contract rate and visit level were applied to my emergency visit",
    "oop_met_still_owe": "reprocess this claim against my out-of-pocket limit, which my plan balances show as reached",
    "global_period_visit": ("remove the charge for the follow-up visit, which falls inside the global period of the "
                            "procedure, or explain why it was billed separately"),
    "plan_balance_math": "send me a statement of the amounts counted toward my deductible and out-of-pocket limit",
    "plan_balance_over": "send me a statement of the amounts counted toward my deductible and out-of-pocket limit",
}
TO_INSURER = {"allowed_vs_published", "eob_denied", "er_rate_over", "oop_met_still_owe", "plan_balance_math",
              "plan_balance_over"}


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
    if f.rule == "ambulance_over_rate":
        return f.explanation.split(" Arizona law")[0].split(" Supplies")[0]
    if f.rule == "ambulance_no_transport":
        return "I was not transported to a hospital."
    if f.rule == "eob_denied":
        return "My insurer denied this claim."
    if f.rule == "er_rate_over":
        return (f"My EOB shows an allowed amount of {m(e['allowed'])} for my emergency visit at {e['hospital']}, but "
                f"the hospital's published emergency visit rates for my insurer are {m(e['published_min'])} to "
                f"{m(e['published_max'])}.")
    if f.rule == "oop_met_still_owe":
        return (f"My plan balances show that my out-of-pocket limit is reached, but this claim says I owe "
                f"{m(e['you_owe'])}.")
    if f.rule == "global_period_visit":
        return (f"The visit {e['visit']} on {e['visit_date']} falls inside the {e['global_days']}-day global period of "
                f"procedure {e['procedure']} on {e['procedure_date']}.")
    if f.rule in ("plan_balance_math", "plan_balance_over"):
        return f.explanation
    return f.title + "."


def itemized_request(req: CheckRequest) -> tuple[str, list[str]]:
    """The first step when nothing is clearly wrong yet: ask for the itemized bill, which shows each code and is
    what every other check needs. Asking is free, and the account can be put on hold meanwhile."""
    letter = "\n".join([
        "[Your name]", "[Your address]", "[Date]", "",
        "To: [Provider name] billing office",
        "Re: Account [Account number], date of service [Date of service]", "",
        "Hello,", "",
        "Before I pay this bill, I would like to review the charges. Please send me an itemized bill that lists, "
        "for each charge, the CPT or HCPCS code, the revenue code, the date of service, the units and the amount.",
        "",
        "Please also tell me whether this bill was sent to my insurance, and whether you screened this account for "
        "your financial assistance policy.", "",
        "Please put this account on hold until I receive the itemized bill, and do not send it to collections "
        "while I review it.", "",
        "Thank you. You can reach me at [Phone or email].", "", "[Your name]"])
    script = [
        "Have ready: the bill, your insurance card, a pen.",
        "Say: 'I'm calling about account [Account number]. Before I pay, I'd like an itemized bill with the CPT "
        "codes, revenue codes, dates and units for each charge.'",
        "Ask: 'Was this bill sent to my insurance?'",
        "Ask: 'Can you put the account on hold until I get the itemized bill?'",
        "Ask: 'Do you have a financial assistance program, and can you screen my account for it?'",
        "Write down: the date, the name of the person, and a reference number for the call.",
    ]
    return letter, script


def build_kit(req: CheckRequest, res: CheckResult) -> tuple[str, list[str]]:
    issues = [f for f in res.findings if f.severity in ("error", "warning") and f.rule in ASK]
    if not issues:
        # Nothing to dispute yet. If the bill could not be confirmed (no EOB to match, no codes), the first step
        # is to ask for the itemized bill; a bill that matches the EOB needs no letter.
        owes = req.bill is not None and (req.bill.balance_due or 0) > 0
        coded = req.bill is not None and any(bl.code for bl in req.bill.lines)
        confirmed = any(f.rule in ("balance_matches_eob", "balance_under_eob", "self_pay_at_cash", "gfe_within",
                                   "ambulance_within_rate")
                        for f in res.findings)
        if owes and not coded and not confirmed and req.bill.provider_type != "ambulance":
            return itemized_request(req)
        return "", []
    to_insurer = all(f.rule in TO_INSURER for f in issues)
    claim = req.eob.claim_number if req.eob and req.eob.claim_number else "[Claim number]"
    lines = [
        "[Your name]", "[Your address]", "[Date]", "",
        "To: " + ("[Insurance company] member services" if to_insurer else "[Provider name] billing office"),
        f"Re: Account [Account number], claim {claim}, date of service [Date of service]", "",
        "Hello,", "",
        ("I compared my bill with your published prices and my good faith estimate"
         if req.context.coverage == "self_pay" else "I compared my bill with my explanation of benefits"
         if req.eob else "I reviewed my bill against the rates that apply to it")
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
