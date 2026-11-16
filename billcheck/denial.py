"""'My insurer said no': what a claim denial means, what to do first, and the appeal deadlines.

The reason is found by fixed rules from the words printed on the EOB or denial letter and from claim adjustment
reason code numbers (CARC, maintained by X12; only the numbers are used here, the plain-language explanations are
ours). Deadlines come from official pages:
- Job, Marketplace and student plans (ACA rules): internal appeal within 180 days of the denial notice; external
  review within 4 months of the final internal denial; the insurer must follow the external reviewer's decision.
  https://www.healthcare.gov/appeal-insurance-company-decision/internal-appeals/ and .../external-review/
  Arizona (state-regulated plans): Department of Insurance and Financial Institutions, four months to ask for an
  external independent review (DIFI consumer guide, rev. 01/2025).
- AHCCCS (Arizona Medicaid) health plans: appeal within 60 days of the decision (AHCCCS Contractor Operations
  Manual, policy 444).
- Medicare: the deadline is printed on the notice; five levels of appeal (medicare.gov).
Nothing here is legal advice; every letter is sent by the person.
"""
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

SOURCES = {
    "internal": ("HealthCare.gov, Internal appeals",
                 "https://www.healthcare.gov/appeal-insurance-company-decision/internal-appeals/"),
    "external": ("HealthCare.gov, External review",
                 "https://www.healthcare.gov/appeal-insurance-company-decision/external-review/"),
    "difi": ("Arizona Department of Insurance and Financial Institutions, consumer guide (rev. 01/2025)",
             "https://difi.az.gov/sites/default/files/Final%202025%20Consumer%20Brochure%20Rev.%2001.21.25.pdf"),
    "ahcccs": ("AHCCCS Contractor Operations Manual, policy 444 (member appeals)",
               "https://www.azahcccs.gov/shared/Downloads/ACOM/PolicyFiles/400/444.pdf"),
    "medicare": ("Medicare.gov, Filing an appeal",
                 "https://www.medicare.gov/providers-services/claims-appeals-complaints/appeals"),
    "nsa": ("CMS, Know your medical bill rights when using insurance",
            "https://www.cms.gov/initiatives/your-patient-rights/medical-bill-rights/know-your-rights/insurance"),
    "carc": ("X12, Claim Adjustment Reason Codes (code numbers only)",
             "https://x12.org/codes/claim-adjustment-reason-codes"),
}


@dataclass(frozen=True)
class Reason:
    key: str
    title: str
    means: str
    first_step: str
    steps: tuple[str, ...]
    appeal_point: str           # the sentence for the appeal letter
    words: str                  # regex on the printed reason
    codes: tuple[str, ...] = ()  # CARC numbers
    appeal_first: bool = True   # False: a phone call usually fixes it faster than an appeal


REASONS = [
    Reason("billing_error", "The claim was sent with missing or wrong information",
           "The insurer could not process the claim as it was sent: a code, a modifier, a diagnosis or other details "
           "were missing or did not match. This is usually the provider's paperwork, not your coverage.",
           "Call the provider's billing office and ask them to correct the claim and send it again.",
           ("Ask the billing office which detail the insurer rejected and when they will resubmit.",
            "Ask them not to bill you while the corrected claim is processed.",
            "If they say the claim is correct, call the insurer and ask exactly what is missing."),
           "The denial says the claim lacked information or had a coding error. This is a billing matter between the "
           "provider and the plan, and I ask that the corrected claim be processed under my benefits.",
           r"lack(s|ed|ing)? information|missing information|incomplete|billing error|submission error|invalid "
           r"(code|procedure|diagnosis)|inconsistent with the (modifier|procedure|diagnosis)|coding",
           ("4", "11", "16"), appeal_first=False),
    Reason("prior_auth", "The insurer says approval was needed before the care",
           "Your plan wanted the provider to get approval (prior authorization) first, and it says that did not happen.",
           "Ask the provider's office whether they asked for approval, and ask them to request it now "
           "(retroactive authorization) and to support your appeal.",
           ("Health plans that cover emergency care may not require prior approval for it. If this was an "
            "emergency, say so in your appeal.",
            "Ask your doctor for a short letter saying why the care was needed and why it could not wait.",
            "In-network providers are often responsible for getting approval. Ask the provider whether they will "
            "write the charge off if the appeal fails."),
           "The denial says prior authorization was missing. The care was medically necessary, and I ask that the "
           "plan review it on its merits; my provider's letter is enclosed.",
           r"prior auth|pre-?auth|precert|pre-certification|authori[sz]ation (was )?(not|absent|required|missing)|"
           r"notification (not|absent)|referral (not|required|missing)",
           ("197",)),
    Reason("medical_necessity", "The insurer says the care was not medically necessary",
           "A reviewer at the plan decided the care was not needed, or was experimental. This is a medical judgment, "
           "and medical judgments can be appealed and sent to an outside reviewer.",
           "Ask your doctor for a letter of medical necessity and your records for this visit.",
           ("Ask the insurer, in writing, for the clinical criteria and the reviewer's notes used to deny the claim. "
            "They must give them to you free of charge.",
            "Send the appeal with the doctor's letter before the deadline.",
            "If the appeal is denied, ask for an external review: an independent reviewer decides, and the insurer "
            "must follow that decision."),
           "The denial says the care was not medically necessary. My doctor's letter explains why it was, and I ask "
           "that the decision be reviewed by a clinician in the same specialty.",
           r"medical(ly)? necess|not necessary|experimental|investigational|not deemed",
           ("50",)),
    Reason("out_of_network", "The insurer says the provider is out of network",
           "Your plan pays less, or nothing, for providers outside its network.",
           "Check whether the No Surprises Act protects you before you pay anything.",
           ("Emergency care, and care from an out-of-network doctor at an in-network hospital or clinic, must be "
            "charged as if in network. The provider may not bill you more than your in-network share.",
            "If you chose this provider and no in-network one was available in time or nearby, ask the plan for a "
            "network exception.",
            "If the plan's online directory listed the provider as in network when you got care, the plan must "
            "charge you your in-network share. A screenshot of the listing helps."),
           "The denial says the provider was out of network. Under the No Surprises Act this care must be covered "
           "at my in-network cost sharing, and I ask that the claim be reprocessed on that basis.",
           r"out[- ]of[- ]network|non[- ]?participating|not (a )?(network|participating)|network provider",
           ("242",)),
    Reason("not_covered", "The insurer says this service is not covered by your plan",
           "Your plan's documents may exclude this service, or limit it.",
           "Look up the service in your plan's Summary of Benefits and Coverage (SBC) or ask the insurer which exact "
           "plan rule they used.",
           ("If the plan wording is unclear, or another rule in the plan covers it, appeal and quote that wording.",
            "Ask the provider whether a different, covered code describes the care correctly.",
            "If it is truly not covered, ask the hospital about its financial assistance policy."),
           "The denial says the service is not covered. I ask the plan to identify the exact provision it relied on "
           "and to reconsider, because the care falls under the covered benefits described in my plan documents.",
           r"not covered|non-?covered|excluded|exclusion|not a covered|benefit plan does not|plan does not cover",
           ("96", "204")),
    Reason("other_insurance", "The insurer thinks another insurance should pay first",
           "This is called coordination of benefits. The plan wants to know whether you have other coverage.",
           "Call the insurer and answer their coordination of benefits questions (often a short form). "
           "Then ask them to reprocess the claim.",
           ("If you have no other insurance, say so; the claim is usually reprocessed in a few weeks.",
            "If you do have other insurance, give the provider both cards so they bill the right one first."),
           "The denial says another plan may be primary. I have completed the coordination of benefits information "
           "and ask that the claim be reprocessed.",
           r"coordination of benefits|other (insurance|coverage|payer)|primary (insurance|payer)|\bCOB\b",
           ("22",), appeal_first=False),
    Reason("eligibility", "The insurer says you were not covered on that date",
           "The plan has no active coverage for you on the date of service, or could not match your ID.",
           "Check that the provider used the right member ID and date, then call the insurer to confirm your "
           "coverage dates.",
           ("If the ID was wrong, ask the provider to resubmit with the correct one.",
            "If your coverage really ended, ask whether another plan (a new job, Medicaid/AHCCCS, a parent's plan) "
            "covered that date, and ask the hospital about financial assistance."),
           "The denial says I was not covered on the date of service. My coverage was active then, and I ask that "
           "the claim be reprocessed.",
           r"coverage (terminated|ended|not (in effect|active))|not eligible|ineligible|member not found|no coverage|"
           r"terminated",
           ("27", "109"), appeal_first=False),
    Reason("late_filing", "The provider sent the claim too late",
           "The plan has a deadline for providers to submit claims, and this one missed it. That is the provider's "
           "delay, not yours.",
           "Ask the provider's billing office to write the charge off.",
           ("In-network providers' contracts usually do not let them bill you for a claim they filed late. Ask "
            "them to confirm in writing.",
            "Keep the EOB showing the late-filing reason."),
           "The denial says the claim was filed late. The delay was the provider's, and I ask that I not be held "
           "responsible for it.",
           r"timely filing|filing (limit|deadline)|time limit for filing|filed late|untimely",
           ("29",), appeal_first=False),
    Reason("duplicate", "The insurer says this is a duplicate of another claim",
           "The plan thinks it already processed the same service.",
           "Find the other EOB for the same date and service; usually it shows how the claim was actually paid.",
           ("If there is no other EOB, call the insurer and ask for the claim number of the original.",
            "Make sure the provider's bill does not charge you twice for the same service."),
           "The denial says the claim is a duplicate. I ask the plan to confirm the original claim number and how "
           "it was processed.",
           r"duplicate", ("18",), appeal_first=False),
    Reason("bundled", "The insurer says this service is included in another one",
           "Some services are paid as part of another service on the same day (bundling).",
           "Check that the provider's bill does not charge you separately for the bundled service.",
           ("In network, a bundled service usually cannot be billed to you on its own. Ask the provider to remove it.",
            "If the services were truly separate, the provider can resubmit with the right modifier."),
           "The denial says this service was included in another payment. I ask that the provider not bill me "
           "separately for it, or that the plan reconsider if the services were distinct.",
           r"included in (the )?(payment|allowance)|bundl|incidental|inclusive|part of another",
           ("97",), appeal_first=False),
    Reason("benefit_limit", "The insurer says you used up this benefit",
           "Your plan has a limit (visits, days or dollars) for this service, and it says you reached it.",
           "Ask the insurer how many visits or dollars it counted, and check them against your own records.",
           ("If the count is wrong, appeal with your dates.",
            "If more care was medically necessary, ask your doctor for a letter and appeal the limit."),
           "The denial says the benefit limit was reached. I ask the plan to show the visits it counted and to "
           "reconsider, because further care was medically necessary.",
           r"benefit max|maximum (benefit|visits|reached)|limit (reached|exceeded)|visits? (limit|exceeded)|"
           r"exceeds (the )?(benefit|limit)",
           ("119",)),
]
BY_KEY = {r.key: r for r in REASONS}
GROUP_CODE = re.compile(r"\b(?:CO|PR|OA|PI|CR)[- ]?(\d{1,3}|B\d{1,2})\b", re.I)   # e.g. "CO-197", "PR 50"

PLANS = ("job", "marketplace", "student", "ahcccs", "medicare", "unknown")


@dataclass
class Deadline:
    label: str
    date: str | None          # ISO date, or None when it depends on a later notice
    note: str
    source: str


@dataclass
class DenialResult:
    reasons: list[str]                       # keys, best first
    deadlines: list[Deadline] = field(default_factory=list)
    emergency_note: bool = False
    letter: str = ""
    call_script: list[str] = field(default_factory=list)
    sources: list[tuple[str, str]] = field(default_factory=list)


def classify(text: str, codes: list[str] | None = None) -> list[str]:
    """Reason keys found in the printed reason text and the codes, most specific first; [] when nothing matches."""
    text = text or ""
    found: list[str] = []
    nums = {c.upper().lstrip("0") or "0" for c in (codes or [])}
    nums |= {m.group(1).upper().lstrip("0") or "0" for m in GROUP_CODE.finditer(text)}
    for r in REASONS:
        if any(c in nums for c in r.codes) and r.key not in found:
            found.append(r.key)
    for r in REASONS:
        if re.search(r.words, text, re.I) and r.key not in found:
            found.append(r.key)
    return found


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(y, m, day)
        except ValueError:
            continue
    raise ValueError(d)


def deadlines(plan: str, notice: date | None) -> list[Deadline]:
    iso = lambda d: d.isoformat() if d else None  # noqa: E731
    if plan == "ahcccs":
        return [Deadline("Appeal to your AHCCCS health plan", iso(notice + timedelta(days=60)) if notice else None,
                         "Within 60 days of the decision. If a service you are getting now is being cut, appeal before "
                         "the date it stops so it can continue during the appeal.", "ahcccs")]
    if plan == "medicare":
        return [Deadline("First Medicare appeal", None,
                         "The deadline is printed on your notice (Medicare Summary Notice or your plan's denial "
                         "letter). Follow the steps it lists.", "medicare")]
    out = [Deadline("Internal appeal to your insurer", iso(notice + timedelta(days=180)) if notice else None,
                    "Within 180 days of the denial notice. The insurer must decide within 30 days for care you have "
                    "not had yet and 60 days for care you already had.", "internal"),
           Deadline("External review (if the appeal is denied)", None,
                    "Within 4 months of the final denial of your appeal. An independent reviewer decides and the "
                    "insurer must follow the decision. It is free or costs at most $25.", "external")]
    if plan in ("marketplace", "student", "unknown"):
        out[1].note += (" For Arizona state-regulated plans, the Department of Insurance and Financial Institutions "
                        "runs it.")
        out[1].source = "difi"
    return out


def letter(reason_keys: list[str], plan: str, emergency: bool) -> str:
    points = [BY_KEY[k].appeal_point for k in reason_keys[:2]] or [
        "I disagree with the decision to deny this claim and ask for a full and fair review."]
    if emergency and "prior_auth" not in reason_keys[:2]:
        points.append("This was emergency care, which does not need prior authorization and must be covered at "
                      "in-network cost sharing under federal law.")
    who = "Appeals Department, [Health plan name]"
    if plan == "ahcccs":
        who = "Member Appeals, [AHCCCS health plan name]"
    lines = ["[Your name]", "[Date]", "", f"To: {who}",
             "Re: Appeal of claim denial. Member ID [member ID], claim number [claim number], "
             "date of service [date], provider [provider name]", "",
             "Hello,", "",
             "I am appealing the denial of the claim above. The reason given was: [reason printed on the EOB or "
             "letter].", ""]
    lines += [p for pt in points for p in (pt, "")]
    lines += ["Please send me, free of charge, copies of all documents, records and other information relevant to "
              "my claim, including any clinical criteria or guidelines used to deny it.", "",
              "I am enclosing: the EOB or denial letter, [the doctor's letter], [medical records], [receipts].", "",
              "Please reprocess the claim and send me your decision in writing. If the denial is upheld, please tell "
              "me how to request an external review.", "",
              "Thank you,", "[Your name]", "[Phone or email]"]
    return "\n".join(lines)


def call_script(reason_keys: list[str]) -> list[str]:
    """Phone steps with the insurer; a reason fixed by a call adds its fix, others keep the appeal questions."""
    r = BY_KEY[reason_keys[0]] if reason_keys else None
    first = r.first_step if r and not r.appeal_first else "Ask the insurer to explain the reason in plain words."
    return ["Have your insurance card, the EOB or denial letter and a pen ready. Write down the date, the name of "
            "the person and a reference number for the call.",
            "Say: \"I'm calling about claim number [claim number] for [date of service]. It was denied and I'd like to "
            "understand why and how to fix it.\"",
            "Ask: \"What exactly was the reason, and what would make this claim payable?\"",
            first,
            "Ask: \"Can this be reprocessed without a formal appeal? If not, where do I send my appeal and what is the "
            "deadline?\"",
            "Ask: \"Please note on my account that I am disputing this claim.\""]


def explain(text: str, codes: list[str] | None = None, plan: str = "unknown", notice_date: date | None = None,
            emergency: bool = False) -> DenialResult:
    plan = plan if plan in PLANS else "unknown"
    keys = classify(text, codes)
    if emergency and "out_of_network" in keys:
        keys.remove("out_of_network")
        keys.insert(0, "out_of_network")
    dl = deadlines(plan, notice_date)
    used = {d.source for d in dl} | ({"nsa"} if emergency or "out_of_network" in keys else set())
    if codes or GROUP_CODE.search(text or ""):
        used.add("carc")
    return DenialResult(reasons=keys, deadlines=dl, emergency_note=emergency, letter=letter(keys, plan, emergency),
                        call_script=call_script(keys), sources=[SOURCES[s] for s in SOURCES if s in used])


def reason_info(keys: list[str] | None = None) -> list[dict]:
    """Plain-language text of the reasons (all reasons when keys is None), for the page."""
    rs = REASONS if keys is None else [BY_KEY[k] for k in keys]
    return [{"key": r.key, "title": r.title, "means": r.means, "first_step": r.first_step, "steps": list(r.steps),
             "appeal_first": r.appeal_first} for r in rs]
