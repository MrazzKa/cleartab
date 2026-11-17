"""'I got a collection letter': rights and next steps for a medical debt in collections in Arizona.

Fixed rules, each with a source:
- Federal debt collection rule (Regulation F): the collector must send validation information; a written dispute
  within the validation period (until 30 days after the person receives it) makes the collector stop collecting
  until it sends verification. 12 CFR 1006.34 and 1006.38.
- Arizona Proposition 209 (Predatory Debt Collection Protection Act, effective December 5, 2022): interest on
  medical debt is capped at 3% a year, or the weekly average one-year Treasury yield if lower, for debts that arose
  after it took effect; upheld by the Arizona Court of Appeals in 2024.
- Credit reports: the CFPB rule that removed medical debt from credit reports was vacated by a federal court in
  Texas in July 2025. Equifax, Experian and TransUnion still say, voluntarily, that they do not report medical
  collections under $500, wait one year before reporting larger unpaid ones, and remove paid ones.
- Nonprofit hospitals (IRS 501(r)): financial assistance applications are accepted for at least 240 days after the
  first bill, and a complete application pauses extraordinary collection actions (selling the debt, credit
  reporting, lawsuits).
Nothing here is legal advice; the person sends every letter and is pointed to free legal aid for court papers.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

PROP_209_EFFECTIVE = date(2022, 12, 5)
MEDICAL_INTEREST_CAP = 3.0

SOURCES = {
    "regf_notice": ("CFPB, Regulation F 12 CFR 1006.34 (validation notice)",
                    "https://www.consumerfinance.gov/rules-policy/regulations/1006/34/"),
    "regf_dispute": ("CFPB, Regulation F 12 CFR 1006.38 (disputes and verification)",
                     "https://www.consumerfinance.gov/rules-policy/regulations/1006/38/"),
    "cfpb_letter": ("CFPB, What a debt collector has to tell you about the debt",
                    "https://www.consumerfinance.gov/ask-cfpb/what-information-does-a-debt-collector-have-to-give-me-"
                    "about-the-debt-en-331/"),
    "prop209": ("Arizona Proposition 209 (2022), Ballotpedia summary",
                "https://ballotpedia.org/Arizona_Proposition_209,_Healthcare_Debt_Interest_Rate_Limit_and_Debt_"
                "Collection_Exemptions_Initiative_(2022)"),
    "prop209_court": ("Husch Blackwell, Arizona Court of Appeals affirms the Predatory Debt Collection Act (2024)",
                      "https://www.huschblackwell.com/newsandinsights/arizona-court-of-appeals-affirms-"
                      "constitutionality-of-new-predatory-debt-collection-act"),
    "credit": ("Consumers' Checkbook, Federal judge kills CFPB rule that banned medical debt in credit reports (2025)",
               "https://www.checkbook.org/national/consumers-notebook/articles/Federal-Judge-Kills-CFPB-Rule-that-"
               "Banned-Medical-Debt-in-Credit-Reports-7678"),
    "credit_report": ("AnnualCreditReport.com (free credit reports)", "https://www.annualcreditreport.com/"),
    "irs_501r": ("IRS, Billing and collections, section 501(r)(6)",
                 "https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6"),
    "legal_pima": ("Step Up to Justice (free civil legal help, Pima County)", "https://www.stepuptojustice.org/"),
    "legal_az": ("AZLawHelp.org (find legal help in Arizona)", "https://www.azlawhelp.org/"),
}


@dataclass
class Item:
    key: str
    level: str          # "urgent" | "warning" | "info" | "ok"
    title: str
    text: str
    action: str
    sources: list[str]
    date: str | None = None


@dataclass
class CollectionResult:
    items: list[Item]
    letter: str
    sources: list[tuple[str, str]] = field(default_factory=list)


def assess(sender: str, first_notice: date | None = None, service_date: date | None = None,
           interest_rate: float | None = None, amount: float | None = None, nonprofit: str = "unknown",
           insured: str = "unknown", today: date | None = None) -> CollectionResult:
    """sender: 'collector' | 'hospital' | 'court'; nonprofit and insured: 'yes' | 'no' | 'unknown'."""
    today = today or date.today()
    items: list[Item] = []
    if sender == "court":
        items.append(Item("court", "urgent", "Court papers have a deadline",
                          "A lawsuit gives you a short time to respond, and the date is on the papers. If you do not "
                          "respond, the court can decide against you without hearing your side.",
                          "Contact free legal aid today and bring the papers. Do not ignore them, even if you think "
                          "you do not owe the debt.", ["legal_pima", "legal_az"]))
    if sender in ("collector", "court"):
        if first_notice:
            end = first_notice + timedelta(days=30)
            if today <= end:
                items.append(Item("dispute_window", "warning", "Dispute in writing before your window closes",
                                  "A collector must send you the details of the debt. If you dispute it in writing "
                                  "within the period on that notice (30 days after you got it), the collector must "
                                  "stop collecting until it sends you proof.",
                                  "Send the letter below by mail with tracking, or through the collector's website "
                                  "if the notice offers it. Keep a copy.", ["regf_notice", "regf_dispute"],
                                  end.isoformat()))
            else:
                items.append(Item("dispute_late", "info", "The 30-day window has likely passed",
                                  "You can still dispute the debt and ask for proof, but the collector no longer has "
                                  "to pause collection while it answers. Check the exact end date printed on the "
                                  "first notice.",
                                  "Send the letter below anyway, and ask the hospital directly about financial "
                                  "assistance and whether insurance was billed.", ["regf_dispute"]))
        else:
            items.append(Item("dispute", "warning", "Ask for proof before you pay",
                              "A collector must send you the details of the debt: whom it is owed to, an itemization "
                              "of interest, fees and payments, and the date your dispute window ends. A written "
                              "dispute in that window makes it stop collecting until it sends proof.",
                              "Find the end date on the first notice and send the letter below before it.",
                              ["regf_notice", "regf_dispute"]))
    if interest_rate is not None and interest_rate > 0:
        if service_date and service_date >= PROP_209_EFFECTIVE:
            if interest_rate > MEDICAL_INTEREST_CAP:
                items.append(Item("interest_over_cap", "warning",
                                  "The interest is above Arizona's 3% cap for medical debt",
                                  "Since December 5, 2022, Arizona law caps interest on medical debt at 3% a year, "
                                  "or the one-year Treasury yield if that is lower.",
                                  "Ask the collector, in writing, to remove the interest above the legal limit and "
                                  "send a corrected balance.", ["prop209", "prop209_court"]))
            else:
                items.append(Item("interest_ok", "ok", "The interest is within Arizona's 3% cap",
                                  "Arizona caps interest on medical debt from care after December 5, 2022 at 3% a "
                                  "year, or the one-year Treasury yield if lower.", "", ["prop209"]))
        elif service_date:
            items.append(Item("interest_old_debt", "info", "Arizona's 3% cap may not apply to this older debt",
                              "The 3% cap on medical debt interest applies to debts that arose after December 5, "
                              "2022. Older debts follow the earlier rules.",
                              "Ask the collector for the interest rate and how it was calculated.", ["prop209"]))
    if amount is not None and 0 < amount < 500:
        items.append(Item("credit_small", "info", "Medical collections under $500 should not be on your credit report",
                          "The three credit bureaus say they do not report medical collections under $500, wait a "
                          "year before reporting larger unpaid ones, and remove them once paid. A federal rule that "
                          "would have gone further was struck down in 2025.",
                          "Check your free credit reports. If a medical debt under $500 shows up, dispute it with the "
                          "bureau.", ["credit", "credit_report"]))
    elif amount is not None and amount >= 500:
        items.append(Item("credit", "info", "It should not reach your credit report for a year",
                          "The credit bureaus say they wait one year before reporting unpaid medical collections, and "
                          "remove them once paid.",
                          "Use that time to dispute errors and ask for financial assistance. Check your free credit "
                          "reports.", ["credit", "credit_report"]))
    if nonprofit in ("yes", "unknown"):
        items.append(Item("assistance", "warning" if nonprofit == "yes" else "info",
                          "You may still qualify for the hospital's financial assistance",
                          "Nonprofit hospitals must take financial assistance applications for at least 240 days after "
                          "the first bill. Once you send a complete application, they must pause collection actions "
                          "such as selling the debt, credit reporting and lawsuits, and refund what you overpaid if "
                          "you qualify.",
                          "Apply to the hospital directly and tell the collector you have applied.", ["irs_501r"]))
    if insured in ("yes", "unknown"):
        items.append(Item("insurance", "warning" if insured == "yes" else "info",
                          "Make sure your insurance was billed",
                          "Bills that go to collections are sometimes never sent to the patient's insurance, or sent "
                          "with an error. Your explanation of benefits (EOB) shows what you really owe.",
                          "Find the EOB for this visit, or ask your insurer for it, and check the bill against it.",
                          []))
    items.append(Item("safety", "info", "Keep it in writing",
                      "You can ask for anything in writing, and you do not have to decide on the phone.",
                      "Do not give a collector access to your bank account. Pay only after you have checked the "
                      "itemization, and get any settlement in writing first.", ["cfpb_letter"]))
    used = {s for i in items for s in i.sources}
    return CollectionResult(items=items, letter=letter(service_date, interest_rate),
                            sources=[SOURCES[k] for k in SOURCES if k in used])


def letter(service_date: date | None = None, interest_rate: float | None = None) -> str:
    over = bool(service_date and service_date >= PROP_209_EFFECTIVE and interest_rate
                and interest_rate > MEDICAL_INTEREST_CAP)
    lines = ["[Your name]", "[Your address]", "[Date]", "", "To: [Collection agency name and address]",
             "Re: Account [account number], original creditor [hospital or provider], amount [amount]", "",
             "I am responding to your contact about this debt. I dispute this debt and request verification. Until "
             "you provide it, please stop collection, including any credit reporting. Please send me:", "",
             "1. The name and address of the original creditor and the date of service.",
             "2. An itemized statement of the amount you are trying to collect, including any interest and fees.",
             "3. Proof that my health insurance was billed, and the explanation of benefits for this claim.",
             "4. Whether the hospital screened this account under its financial assistance policy before sending it "
             "to you.",
             "5. A copy of any document that shows I agreed to pay this amount.", ""]
    if over:
        lines += ["This is medical debt for care after December 5, 2022. Arizona law caps the interest on it at 3% a "
                  "year (Proposition 209). Please remove any interest above that limit and send a corrected "
                  "balance.", ""]
    lines += ["Please communicate with me in writing at the address above.", "", "Sincerely,", "[Your name]"]
    return "\n".join(lines)
