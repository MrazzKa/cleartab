"""Deterministic bill check rules (Feature 7). No language model is involved: each finding comes from arithmetic,
a published CMS table or a published hospital price, and names its source.

Severity: "error" = the numbers or a published rule say the patient is asked for more than they should be;
"warning" = something to ask about; "info" = a right or a fact the patient should know; "ok" = a check passed.
"""
from collections import Counter, defaultdict
from datetime import date, timedelta

from billcheck.models import CheckRequest, CheckResult, Finding, Source, Summary
from billcheck.reference import SOURCES, MueEdit, PtpTable

TOL = 0.02          # cents of rounding allowed in EOB arithmetic
PRICE_TOL = 0.01    # 1% around a published price before flagging
GFE_THRESHOLD = 400.0
GFE_DAYS = 120


def src(key: str, as_of: str | None = None, url: str | None = None) -> Source:
    name, default_url = SOURCES[key]
    return Source(name=name, url=url or default_url, as_of=as_of)


def money(x: float | None) -> str:
    return "n/a" if x is None else f"${x:,.2f}"


def span(lo: float, hi: float) -> str:
    return money(lo) if hi - lo <= TOL else f"{money(lo)} to {money(hi)}"


def c(x: float) -> float:
    return round(x + 0.0, 2)


class Checker:
    def __init__(self, req: CheckRequest, prices: dict[str, dict] | None, mue: dict[str, dict[str, MueEdit]],
                 ptp: PtpTable | None):
        self.req, self.ctx, self.eob, self.bill = req, req.context, req.eob, req.bill
        self.prices = prices or {}
        self.mue, self.ptp = mue, ptp
        self.findings: list[Finding] = []
        self.lines_checked = 0
        self.run: list[str] = []
        self.skipped: dict[str, str] = {}

    def add(self, **kw) -> None:
        self.findings.append(Finding(**kw))

    # ------------------------------------------------------------------ EOB on its own
    def eob_arithmetic(self) -> None:
        if not self.eob or not self.eob.lines:
            self.skipped["eob_arithmetic"] = "no EOB lines entered"
            return
        self.run.append("eob_arithmetic")
        zero_lines = []
        for i, ln in enumerate(self.eob.lines, 1):
            share = ln.copay + ln.deductible + ln.coinsurance
            allowed = self.allowed(ln)
            if allowed is not None and ln.plan_paid is not None and ln.status != "denied":
                self.lines_checked += 1
            if allowed is not None and ln.plan_paid is not None and ln.status != "denied" \
                    and abs(allowed - ln.plan_paid - share) > TOL:
                self.add(rule="eob_line_sum", severity="warning", lines=[i],
                         evidence={"allowed": allowed, "plan_paid": ln.plan_paid, "patient_share": c(share)},
                         title=f"EOB line {i} does not add up",
                         explanation=(f"The allowed amount ({money(allowed)}) should equal what the plan paid "
                                      f"({money(ln.plan_paid)}) plus your copay, deductible and coinsurance "
                                      f"({money(c(share))}). It is off by {money(c(allowed - ln.plan_paid - share))}."),
                         action="Check that you copied the line correctly. If you did, ask the insurer to explain "
                                "the difference.",
                         sources=[src("cms_eob")])
            owe_line = ln.you_owe if ln.you_owe is not None else share + ln.not_covered
            if ln.status != "denied" and (ln.billed or 0) > 0 and allowed is not None and abs(allowed) <= TOL \
                    and abs(owe_line) <= TOL and not ln.plan_paid:
                zero_lines.append(i)
            if ln.you_owe is not None and abs(ln.you_owe - (share + ln.not_covered)) > TOL:
                self.add(rule="eob_owe_sum", severity="warning", lines=[i],
                         title=f"EOB line {i}: 'what you owe' does not match its parts",
                         explanation=(f"What you owe ({money(ln.you_owe)}) should be your copay, deductible, "
                                      f"coinsurance and any amount not covered ({money(c(share + ln.not_covered))})."),
                         action="Ask the insurer which amount is right before you pay.",
                         sources=[src("cms_eob")])
            if ln.allowed is not None and ln.billed is not None and ln.allowed > ln.billed + TOL:
                self.add(rule="eob_allowed_over_billed", severity="info", lines=[i],
                         title=f"EOB line {i}: allowed amount is higher than the charge",
                         explanation="Normally the insurer allows the same or less than the provider charged.",
                         action="Usually harmless, but worth a question if your share is large.",
                         sources=[src("cms_eob")])
        if zero_lines:
            self.add(rule="eob_zero_allowed", severity="info", lines=zero_lines,
                     title=f"Line(s) {', '.join(map(str, zero_lines))}: the insurer allowed $0",
                     explanation=("The insurer allowed nothing for this service but did not deny it, and you owe "
                                  "nothing for it. Usually this means the service is included (bundled) in the "
                                  "payment for another service on the same claim, such as a blood draw included in "
                                  "an emergency visit."),
                     action="You owe nothing for this line. If a bill lists it separately with a balance, ask why.",
                     sources=[src("cms_eob")])
        self.eob_explain()
        owed = self.eob_owe()
        if self.eob.you_owe_total is not None and owed is not None and abs(self.eob.you_owe_total - owed) > TOL:
            self.add(rule="eob_total", severity="warning",
                     title="The EOB total does not match its lines",
                     explanation=(f"The lines add up to {money(owed)} but the EOB total says "
                                  f"{money(self.eob.you_owe_total)}."),
                     action="Ask the insurer which total is correct.", sources=[src("cms_eob")])
        denied = [i for i, ln in enumerate(self.eob.lines, 1) if ln.status == "denied"]
        if denied:
            amt = c(sum(self.eob.lines[i - 1].billed or 0 for i in denied))
            self.add(rule="eob_denied", severity="warning", lines=denied,
                     title=f"{len(denied)} line(s) were denied by your insurer",
                     explanation=("A denial is a decision you can appeal. The denial notice must say why the claim "
                                  "was denied and how to appeal. Denials are often caused by missing information, "
                                  "such as a referral, a prior authorization or your insurance details."),
                     action=("Call the insurer and ask for the denial reason in writing, then ask the provider to "
                             "fix and resubmit the claim if information was missing. Do not pay the denied amount "
                             "until this is settled."),
                     amount_at_stake=amt or None, sources=[src("nsa_insured")])
        pending = [i for i, ln in enumerate(self.eob.lines, 1) if ln.status == "pending"]
        if pending:
            self.add(rule="eob_pending", severity="info", lines=pending,
                     title="Some lines are still being processed",
                     explanation="Until the insurer finishes processing the claim, nobody knows your final share.",
                     action="Wait for the final EOB before paying a bill for these services.",
                     sources=[src("cms_eob")])

    @staticmethod
    def allowed(ln) -> float | None:
        """The allowed amount as printed, or billed minus the network discount and any amount not covered."""
        if ln.allowed is not None:
            return ln.allowed
        if ln.billed is not None and ln.discount is not None:
            return c(ln.billed - ln.discount - ln.not_covered)
        return None

    def eob_explain(self) -> None:
        """What the EOB means for the patient: the network discount and the out-of-pocket maximum."""
        lines = self.eob.lines
        billed = c(sum(ln.billed or 0 for ln in lines))
        disc = c(sum(ln.discount if ln.discount is not None else
                     (ln.billed - ln.allowed if ln.billed is not None and ln.allowed is not None else 0)
                     for ln in lines if ln.status != "denied"))
        if disc > TOL and billed > 0:
            self.add(rule="network_discount", severity="info", evidence={"billed": billed, "discount": disc},
                     title=f"The provider wrote off {money(disc)} of its {money(billed)} charge",
                     explanation=("This is the discount your insurer negotiated. A provider in your network has "
                                  "agreed to accept the allowed amount, so it may not bill you for the discount "
                                  "(this is called balance billing)."),
                     action=("If a bill from this provider asks for more than the EOB says you owe, do not pay the "
                             "difference; call the billing office with the EOB."),
                     sources=[src("cms_eob"), src("nsa_insured")])
        if self.eob.oop_max_met:
            self.add(rule="oop_max_met", severity="info",
                     title="You reached your out-of-pocket maximum",
                     explanation=("The EOB says your out-of-pocket maximum for this plan year is met. After that, "
                                  "your plan pays 100% of covered, in-network care until the plan year ends: no more "
                                  "deductible, copays or coinsurance."),
                     action=("Check every later bill and EOB from this plan year. If you are asked for a copay, "
                             "deductible or coinsurance for covered in-network care, ask the insurer why."),
                     sources=[src("oop_max")])

    def eob_owe(self) -> float | None:
        if not self.eob or not self.eob.lines:
            return self.eob.you_owe_total if self.eob else None
        vals = [ln.you_owe if ln.you_owe is not None else ln.copay + ln.deductible + ln.coinsurance + ln.not_covered
                for ln in self.eob.lines]
        return c(sum(vals))

    # ------------------------------------------------------------------ bill against EOB
    def bill_vs_eob(self) -> None:
        if not self.bill:
            self.skipped["bill_vs_eob"] = "no bill entered"
            return
        if not self.eob or self.ctx.coverage == "self_pay":
            self.skipped["bill_vs_eob"] = "no EOB (self-pay or not entered)"
            if self.ctx.coverage == "insured":
                self.add(rule="no_eob_yet", severity="warning",
                         title="Wait for your explanation of benefits before paying",
                         explanation=("Your insurer sends an explanation of benefits (EOB) after it processes the "
                                      "claim. It says how much you owe. Until then, the bill may not include what "
                                      "your insurance will pay."),
                         action=("Check your insurer's app or website for the EOB, or call the number on your "
                                 "insurance card. If the provider never billed your insurance, give them your "
                                 "insurance card details."),
                         sources=[src("cms_eob")])
            return
        owed, balance = self.eob_owe(), self.bill.balance_due
        if owed is None or balance is None:
            self.skipped["bill_vs_eob"] = "EOB amount owed or bill balance missing"
            return
        self.run.append("bill_vs_eob")
        expected = c(max(owed - self.bill.patient_payments, 0))
        diff = c(balance - expected)
        protected = self.nsa_applies()
        if diff > TOL:
            paid_not_subtracted = self.bill.patient_payments > 0 and abs(diff - self.bill.patient_payments) <= TOL
            if paid_not_subtracted:
                title = "Your earlier payment may not be subtracted"
                paid = money(self.bill.patient_payments)
                expl = (f"Your EOB says you owe {money(owed)} in total. You already paid {paid}, "
                        f"so the bill should show {money(expected)}, but it asks for {money(balance)}.")
            else:
                title = f"The bill asks for {money(diff)} more than your EOB says you owe"
                expl = (f"Your EOB says you owe {money(owed)}"
                        + (f", minus {money(self.bill.patient_payments)} you already paid"
                           if self.bill.patient_payments else "")
                        + f". The bill asks for {money(balance)}.")
            action = ("Do not pay the difference yet. Call the provider's billing office with your EOB, ask them "
                      "to match the bill to the EOB, and ask for an itemized bill.")
            if paid_not_subtracted:
                sev = "error"
                action = ("Do not pay again. Call the billing office, give the date and amount of your payment (a "
                          "receipt or card statement helps), and ask them to apply it to this account.")
            elif self.ctx.network == "in" or protected:
                sev = "error"
                expl += (" An in-network provider has agreed to accept the allowed amount, so it may not bill you "
                         "for the difference between its charge and the allowed amount (balance billing)."
                         if self.ctx.network == "in" else
                         " The No Surprises Act protects this visit, so you should pay no more than your "
                         "in-network share.")
            else:
                sev = "warning"
                expl += (" If the provider is out of network, it may bill you the difference between its charge "
                         "and what your plan allowed, unless a protection applies.")
            self.add(rule="balance_over_eob", severity=sev, title=title, explanation=expl, action=action,
                     evidence={"eob_you_owe": owed, "already_paid": self.bill.patient_payments,
                               "bill_balance": balance},
                     amount_at_stake=diff, sources=[src("cms_eob"), src("nsa_insured")])
        elif diff < -TOL:
            self.add(rule="balance_under_eob", severity="info",
                     title="The bill is lower than your EOB share",
                     explanation=(f"The bill asks for {money(balance)}, less than the {money(expected)} the EOB "
                                  "suggests. A later bill may follow, or an adjustment was applied."),
                     action="Keep the EOB and pay what the bill asks; check the next statement.",
                     sources=[src("cms_eob")])
        else:
            self.add(rule="balance_matches_eob", severity="ok",
                     title="The bill matches your EOB",
                     explanation=f"Both say you owe {money(expected)}.", sources=[src("cms_eob")])

        # bill lines the insurer never saw
        eob_dates = defaultdict(set)
        for ln in self.eob.lines:
            if ln.code:
                eob_dates[ln.code].add(ln.service_date)
        if eob_dates and self.bill.lines:
            def on_eob(code: str, d) -> bool:
                dates = eob_dates.get(code)
                return bool(dates) and (d is None or None in dates or d in dates)
            missing = [i for i, bl in enumerate(self.bill.lines, 1) if bl.code and not on_eob(bl.code, bl.service_date)]
            if missing:
                amt = c(sum(self.bill.lines[i - 1].amount for i in missing))
                self.add(rule="bill_line_not_on_eob", severity="warning", lines=missing,
                         title=f"{len(missing)} bill line(s) are not on your EOB",
                         explanation=("These services do not appear on the EOB, so the insurer may never have "
                                      "received them, or they went on a separate claim."),
                         action=("Ask the provider whether these were billed to your insurance. If not, give them "
                                 "your insurance card details and ask them to submit the claim before you pay."),
                         evidence={"codes": [self.bill.lines[i - 1].code for i in missing]},
                         amount_at_stake=amt, sources=[src("cms_eob")])

    # ------------------------------------------------------------------ bill on its own
    def duplicates(self) -> None:
        lines = self.bill.lines if self.bill and self.bill.lines else []
        if not lines:
            self.skipped["duplicates"] = "no itemized bill lines"
            return
        self.run.append("duplicates")
        key = lambda bl: (bl.service_date, (bl.code or bl.description.strip().lower()), bl.units, bl.amount)  # noqa: E731
        groups = defaultdict(list)
        for i, bl in enumerate(lines, 1):
            groups[key(bl)].append(i)
        for k, idx in groups.items():
            if len(idx) > 1 and k[1]:
                self.add(rule="duplicate_line", severity="warning", lines=idx,
                         title=f"Possible duplicate charge: {k[1]} listed {len(idx)} times",
                         explanation=(f"The same service, date and amount ({money(k[3])}) appears {len(idx)} times. "
                                      "Sometimes this is correct (for example two separate tests), often it is a "
                                      "billing error."),
                         action="Ask the billing office whether you received this service more than once.",
                         evidence={"service": k[1], "times": len(idx), "amount": k[3]},
                         amount_at_stake=c(k[3] * (len(idx) - 1)))

    def units_mue(self) -> None:
        lines = [(bl.service_date, bl.code, bl.units) for bl in (self.bill.lines if self.bill else []) if bl.code]
        if not lines and self.eob:
            lines = [(ln.service_date, ln.code, ln.units) for ln in self.eob.lines if ln.code]
        if not lines:
            self.skipped["mue_units"] = "no procedure codes entered"
            return
        ptype = self.bill.provider_type if self.bill else "unknown"
        table = "practitioner" if ptype == "professional" else "facility outpatient"
        edits = self.mue.get(table)
        if not edits:
            self.skipped["mue_units"] = "CMS MUE table not loaded"
            return
        self.run.append("mue_units")
        per_day = Counter()
        for d, code, units in lines:
            per_day[(d, code)] += units
            e = edits.get(code)
            if e and e.indicator.startswith("1") and units > e.value:
                self.mue_finding(code, units, e, "on one line")
        for (_d, code), units in per_day.items():
            e = edits.get(code)
            if e and not e.indicator.startswith("1") and units > e.value:
                self.mue_finding(code, units, e, "on one day")

    def mue_finding(self, code: str, units: int, e: MueEdit, scope: str) -> None:
        self.add(rule="mue_units", severity="error" if e.indicator.startswith("2") else "warning",
                 title=f"{code}: {units} units {scope}, Medicare's limit is {e.value}",
                 explanation=(f"CMS sets a maximum number of units for this code ({e.value}, {e.table} table, "
                              f"'{e.indicator}'). Charges above it are usually not paid and often mean a "
                              "data entry error. The limit is a Medicare rule; private insurers often use the same "
                              "edits."),
                 action="Ask the billing office to confirm the number of units and correct the bill if needed.",
                 evidence={"code": code, "units": units, "limit": e.value, "indicator": e.indicator},
                 sources=[src("mue", as_of=e.as_of)])

    def code_pairs(self) -> None:
        if self.ptp is None:
            self.skipped["ncci_ptp"] = "CMS procedure-to-procedure table not loaded (manual download)"
            return
        rows = [(bl.service_date, bl.code, i) for i, bl in enumerate(self.bill.lines if self.bill else [], 1) if bl.code]
        if not rows:
            self.skipped["ncci_ptp"] = "no procedure codes entered"
            return
        self.run.append("ncci_ptp")
        by_day = defaultdict(dict)
        for d, code, i in rows:
            by_day[d].setdefault(code, i)
        for codes in by_day.values():
            for a, ia in codes.items():
                for b, ib in codes.items():
                    mod = self.ptp.pairs.get(a, {}).get(b)
                    if mod is None:
                        continue
                    self.add(rule="ncci_pair", severity="error" if mod == "0" else "warning", lines=[ia, ib],
                             title=f"{a} and {b} are not normally billed together",
                             explanation=(f"CMS lists {b} as part of {a} when both are done on the same day"
                                          + (", and never allows them to be paid separately."
                                             if mod == "0" else
                                             ", unless a modifier shows they were separate services.")),
                             action=f"Ask the billing office why {b} is billed separately from {a}.",
                             evidence={"column_1": a, "column_2": b, "modifier_indicator": mod},
                             sources=[src("ptp", as_of=f"{self.ptp.table} {self.ptp.as_of}".strip())])

    # ------------------------------------------------------------------ against published prices
    def published(self) -> None:
        if not self.ctx.hospital_ccn:
            self.skipped["published_prices"] = "no hospital selected"
            return
        if not self.prices:
            self.skipped["published_prices"] = "no published prices for these codes at this hospital in our data"
            return
        self.run.append("published_prices")
        if self.ctx.coverage == "insured" and self.eob:
            for i, ln in enumerate(self.eob.lines, 1):
                p = self.prices.get(ln.code or "")
                if not p or ln.allowed is None:
                    continue
                if not p["neg_n"]:
                    continue
                per_unit = ln.allowed / ln.units
                lo, hi = p["neg_min"] * (1 - PRICE_TOL), p["neg_max"] * (1 + PRICE_TOL)
                ev = {"code": ln.code, "allowed_per_unit": c(per_unit), "published_min": p["neg_min"],
                      "published_median": p["neg_median"], "published_max": p["neg_max"], "rates": p["neg_n"],
                      "hospital": p["hospital"]}
                s = [src("hpt", as_of=p["retrieved_at"], url=p["source_url"])]
                if lo <= per_unit <= hi:
                    self.add(rule="allowed_matches_published", severity="ok", lines=[i], evidence=ev, sources=s,
                             title=f"{ln.code}: allowed amount is within the hospital's published rates",
                             explanation=(f"{p['hospital']} published {p['neg_n']} rate(s) for "
                                          f"{self.ctx.insurer} from {money(p['neg_min'])} to {money(p['neg_max'])}; "
                                          f"your EOB allowed {money(c(per_unit))}."))
                else:
                    self.add(rule="allowed_vs_published", severity="warning", lines=[i], evidence=ev, sources=s,
                             title=f"{ln.code}: allowed amount differs from the hospital's published rates",
                             explanation=(f"{p['hospital']} published rates for {self.ctx.insurer} from "
                                          f"{money(p['neg_min'])} to {money(p['neg_max'])} for this service; your "
                                          f"EOB allowed {money(c(per_unit))}. Your plan may use a different contract, "
                                          "or the claim may have been processed under the wrong rate."),
                             action="Ask the insurer which contract rate was applied to this line.",
                             amount_at_stake=c(max(per_unit - p["neg_max"], 0) * ln.units) or None)
        if self.ctx.coverage == "self_pay" and self.bill:
            for i, bl in enumerate(self.bill.lines, 1):
                p = self.prices.get(bl.code or "")
                if not p or p["cash"] is None:
                    continue
                per_unit = bl.amount / bl.units
                s = [src("hpt", as_of=p["retrieved_at"], url=p["source_url"])]
                ev = {"code": bl.code, "billed_per_unit": c(per_unit), "published_cash": p["cash"],
                      "hospital": p["hospital"]}
                if per_unit > p["cash"] * (1 + PRICE_TOL):
                    self.add(rule="self_pay_over_cash", severity="warning", lines=[i], evidence=ev, sources=s,
                             title=f"{bl.code}: billed above the hospital's published cash price",
                             explanation=(f"{p['hospital']} publishes a discounted cash price of {money(p['cash'])} "
                                          f"for this service. You were billed {money(c(per_unit))}."),
                             action="Ask the hospital to apply its published discounted cash price.",
                             amount_at_stake=c((per_unit - p["cash"]) * bl.units))
                else:
                    self.add(rule="self_pay_at_cash", severity="ok", lines=[i], evidence=ev, sources=s,
                             title=f"{bl.code}: billed at or below the published cash price",
                             explanation=f"Published cash price {money(p['cash'])}, billed {money(c(per_unit))}.")
        for i, ln in enumerate(self.eob.lines if self.eob else [], 1):
            p = self.prices.get(ln.code or "")
            if p and p["gross"] and ln.billed is not None and ln.billed / ln.units > p["gross"] * (1 + PRICE_TOL):
                self.add(rule="billed_over_gross", severity="info", lines=[i],
                         title=f"{ln.code}: charge is above the hospital's published list price",
                         explanation=(f"The published gross charge is {money(p['gross'])}; the EOB shows a charge of "
                                      f"{money(c(ln.billed / ln.units))} per unit."),
                         action="Your share depends on the allowed amount, not the charge, but you may ask why.",
                         sources=[src("hpt", as_of=p["retrieved_at"], url=p["source_url"])])

    # ------------------------------------------------------------------ Plan balances box (P11)
    def plan_balances(self) -> None:
        """What is left of the deductible and the out-of-pocket limit, from the EOB's plan balances box, and
        whether its numbers add up."""
        if not self.eob or not self.eob.balances or self.ctx.coverage != "insured":
            return
        self.run.append("plan_balances")
        names = {"deductible": "Deductible", "out_of_pocket": "Out-of-pocket limit"}
        summary = []
        for b in self.eob.balances:
            scope = ", ".join(x for x in ({"in": "in network", "out": "out of network"}.get(b.network),
                                         {"family": "family", "individual": "individual"}.get(b.level)) if x)
            label = names[b.kind] + (f" ({scope})" if scope else "")
            ev = {"kind": b.kind, "network": b.network, "level": b.level, "limit": b.limit, "used": b.used,
                  "remaining": b.remaining}
            if None not in (b.limit, b.used, b.remaining) and abs(b.limit - b.used - b.remaining) > TOL:
                self.add(rule="plan_balance_math", severity="warning", evidence=ev, sources=[src("cms_eob")],
                         title=f"{label}: the plan balance numbers do not add up",
                         explanation=(f"The EOB shows a limit of {money(b.limit)} with {money(b.used)} used, which "
                                      f"leaves {money(c(b.limit - b.used))}, but it says {money(b.remaining)} remains."),
                         action="Ask the insurer for a statement of what has counted toward your deductible and "
                                "out-of-pocket limit this plan year.")
            if b.limit is not None and b.used is not None and b.used > b.limit + TOL:
                self.add(rule="plan_balance_over", severity="warning", evidence=ev, sources=[src("cms_eob")],
                         title=f"{label}: more than the limit is counted as used",
                         explanation=(f"The EOB counts {money(b.used)} toward a limit of {money(b.limit)}. Once a "
                                      "limit is reached, it should not keep growing."),
                         action="Ask the insurer to check the amounts counted toward this limit.")
            if b.network != "out" and (b.remaining is not None or None not in (b.limit, b.used)):
                left = b.remaining if b.remaining is not None else c(max(b.limit - b.used, 0))
                used = f"{money(b.used)} of {money(b.limit)} used, " if None not in (b.used, b.limit) else ""
                summary.append(f"{label}: {used}{money(left)} left.")
            oop_met = b.kind == "out_of_pocket" and b.network != "out" and (
                (b.remaining is not None and b.remaining <= TOL)
                or (None not in (b.limit, b.used) and b.used >= b.limit - TOL))
            owe = self.eob_owe()
            if oop_met and owe and owe > TOL:
                not_cov = c(sum(ln.not_covered for ln in self.eob.lines))
                self.add(rule="oop_met_still_owe", severity="warning", evidence={**ev, "you_owe": owe},
                         sources=[src("cms_eob")],
                         title="Your out-of-pocket limit is reached, but this claim still asks you to pay",
                         explanation=(f"The plan balances box shows the {label.lower()} is used up. After that, "
                                      "covered in-network care should cost you $0 for the rest of the plan year, "
                                      f"but this EOB says you owe {money(owe)}"
                                      + (f" ({money(not_cov)} of it for services the plan does not cover, which do "
                                         "not count toward the limit)." if not_cov else ".")),
                         action=("Ask the insurer whether this claim was processed before the limit was reached and "
                                 "whether it should be reprocessed."),
                         amount_at_stake=c(max(owe - not_cov, 0)) or None)
        if summary:
            self.add(rule="plan_balance_left", severity="info", evidence={"lines": summary}, sources=[src("cms_eob")],
                     title="What is left of your deductible and out-of-pocket limit",
                     explanation=(" ".join(summary) + " Until the deductible is met you usually pay the whole "
                                  "allowed amount; after it, only copays or coinsurance. Once the out-of-pocket "
                                  "limit is reached, covered in-network care costs you $0 until the plan year "
                                  "ends."),
                     action="Keep this EOB: the next one should show these numbers going up, never down.")

    # ------------------------------------------------------------------ Emergency visit vs published ER rates
    def er_visit(self) -> None:
        """Compare the allowed amount of an ER line with the ED visit rates (CPT 99281-99285) the hospital published
        for the insurer. EOBs often print the ER line without a code, so the line is found by its description."""
        from billcheck import er
        from pipeline.payers import match
        if self.ctx.coverage != "insured" or not self.eob:
            return
        lines = [(i, ln) for i, ln in enumerate(self.eob.lines, 1)
                 if er.is_er_line(ln.code, ln.description) and (self.allowed(ln) or 0) > 0]
        if not lines:
            return
        ccn = self.ctx.hospital_ccn or er.find_hospital(self.ctx.provider_name)
        payer, plan_type = self.ctx.insurer, None
        if self.ctx.insurer_name:
            m = match(self.ctx.insurer_name, "")
            payer = payer or (m["canonical_payer"] if m["canonical_payer"] != "other" else None)
            plan_type = m.get("plan_type") or None
        if not ccn or not payer:
            self.skipped["er_rates"] = "hospital or insurer not known"
            return
        rows = er.rates(ccn, payer)
        if not rows:
            self.skipped["er_rates"] = f"no published ER visit rates for {payer} at this hospital in our data"
            return
        self.run.append("er_rates")
        hospital = er.hospital_name(ccn)
        s = [src("hpt", as_of=rows[0]["retrieved_at"][:10], url=rows[0]["source_url"])]
        same_type = [r for r in rows if plan_type and r["plan_type"] == plan_type] or rows
        lo_all, hi_all = min(r["amount"] for r in rows), max(r["amount"] for r in rows)
        for i, ln in lines:
            allowed = self.allowed(ln)
            cand = [r for r in same_type if not ln.code or r["code"] == ln.code] or same_type
            hit = [r for r in cand if abs(r["amount"] - allowed) <= TOL]
            lo, hi = min(r["amount"] for r in cand), max(r["amount"] for r in cand)
            ev = {"hospital": hospital, "insurer": payer, "allowed": allowed, "published_min": lo,
                  "published_max": hi, "all_plans_min": lo_all, "all_plans_max": hi_all,
                  "plans": sorted({r["plan_name"] for r in (hit or cand)})}
            if hit:
                r = hit[0]
                per = "per visit (any visit level)" if r["methodology"] == "case rate" and len(
                    {x["code"] for x in hit}) == 5 else f"for visit level {r['code'][-1]} (CPT {r['code']})"
                ev["methodology"] = r["methodology"]
                self.add(rule="er_rate_matches", severity="ok", lines=[i], evidence=ev, sources=s,
                         title="Emergency visit: the allowed amount matches the hospital's published rate",
                         explanation=(f"{hospital} publishes {money(r['amount'])} {per} for {payer} "
                                      f"({', '.join(ev['plans'])} plan, {r['methodology']}). Your EOB allowed "
                                      f"{money(allowed)}, so the insurer applied the published contract rate."
                                      + (f" For comparison, the same hospital's published ER visit rates for all "
                                         f"{payer} plans range from {money(lo_all)} to {money(hi_all)}."
                                         if hi_all - lo_all > TOL else "")))
            elif allowed > hi * (1 + PRICE_TOL):
                share = ln.you_owe if ln.you_owe is not None else allowed - (ln.plan_paid or 0)
                self.add(rule="er_rate_over", severity="warning", lines=[i], evidence=ev, sources=s,
                         title="Emergency visit: allowed amount is above the hospital's published rates",
                         explanation=(f"{hospital} publishes ER visit rates for {payer} of {span(lo, hi)}. "
                                      f"Your EOB allowed {money(allowed)}. The claim may have been "
                                      "processed under the wrong contract or visit level."),
                         action=("Ask the insurer which contract rate and visit level were applied, and ask the "
                                 "hospital for the itemized bill with the CPT code of the ER visit."),
                         amount_at_stake=c(min(allowed - hi, share)) if share and share > 0 else None)
            else:
                self.add(rule="er_rate_within", severity="info", lines=[i], evidence=ev, sources=s,
                         title="Emergency visit: allowed amount is within the hospital's published rates",
                         explanation=(f"{hospital} publishes ER visit rates for {payer} of {span(lo, hi)}, "
                                      f"depending on the plan and visit level. Your EOB allowed "
                                      f"{money(allowed)}."))

    # ------------------------------------------------------------------ No Surprises Act
    def nsa_applies(self) -> bool:
        x = self.ctx
        return x.coverage == "insured" and x.network == "out" and (x.emergency or x.ambulance == "air")

    def surprises(self) -> None:
        x = self.ctx
        self.run.append("no_surprises_act")
        if x.coverage == "insured" and x.network == "out" and x.emergency:
            self.add(rule="nsa_emergency", severity="info",
                     title="Emergency care is protected from surprise bills",
                     explanation=("For emergency care, an out-of-network provider may not bill you more than your "
                                  "in-network copay, coinsurance or deductible."),
                     action=("If you were billed more, call the No Surprises Help Desk at 1-800-985-3059 or submit "
                             "a complaint."), sources=[src("nsa_insured")])
        if x.coverage == "insured" and x.network == "out" and not x.emergency and x.ambulance == "none" \
                and self.bill and self.bill.provider_type == "professional":
            self.add(rule="nsa_facility_provider", severity="info",
                     title="Out-of-network doctor at an in-network hospital?",
                     explanation=("If this doctor treated you at an in-network hospital or surgery center, the No "
                                  "Surprises Act usually limits you to your in-network share, unless you signed a "
                                  "notice and consent form agreeing to out-of-network billing."),
                     action="Ask the provider whether you signed a notice and consent form, and ask for a copy.",
                     sources=[src("nsa_insured")])
        if x.ambulance == "air" and x.coverage == "insured":
            self.add(rule="nsa_air_ambulance", severity="info",
                     title="Air ambulance bills are protected",
                     explanation=("For covered air ambulance services from an out-of-network provider, you should "
                                  "pay no more than your in-network share."),
                     action="If billed more, call the No Surprises Help Desk at 1-800-985-3059.",
                     sources=[src("nsa_insured")])
        if x.ambulance == "ground":
            self.add(rule="nsa_ground_ambulance", severity="info",
                     title="Ground ambulance bills are not covered by the federal protections",
                     explanation=("The No Surprises Act does not cover ground ambulances, so an out-of-network "
                                  "ambulance may bill you the difference, unless state law says otherwise."),
                     action=("Ask your insurer to review the claim, ask the ambulance company for an itemized bill, "
                             "and ask about financial assistance or a payment plan."),
                     sources=[src("nsa_ground")])
        if x.coverage == "self_pay":
            self.good_faith()

    def good_faith(self) -> None:
        x, b = self.ctx, self.bill
        if x.good_faith_estimate is None:
            self.add(rule="gfe_missing", severity="info",
                     title="Uninsured or paying yourself? You can ask for a Good Faith Estimate",
                     explanation=("If you schedule care and do not use insurance, the provider must give you a good "
                                  "faith estimate. If the bill is $400 or more above it, you can dispute the bill."),
                     action="For future care, ask for a written good faith estimate when you schedule.",
                     sources=[src("nsa_dispute")])
            return
        if not b:
            return
        total = c(sum(bl.amount for bl in b.lines)) if b.lines else c((b.balance_due or 0) + b.patient_payments
                                                                       + b.insurance_paid + b.adjustments)
        over = c(total - x.good_faith_estimate)
        if over >= GFE_THRESHOLD:
            today = x.today or date.today()
            late = b.statement_date is not None and today - b.statement_date > timedelta(days=GFE_DAYS)
            self.add(rule="gfe_dispute", severity="warning" if late else "error",
                     title=f"The bill is {money(over)} above your good faith estimate",
                     explanation=("When a provider charges at least $400 more than its good faith estimate, a "
                                  "self-pay patient can start the federal patient-provider dispute process within "
                                  "120 calendar days of the first bill. There is a $25 fee, which is subtracted from "
                                  "what you owe if you win."
                                  + (" Your bill appears to be older than 120 days." if late else "")),
                     action=("Keep the estimate and the bill. Start the dispute at cms.gov/medical-bill-rights or "
                             "call 1-800-985-3059."),
                     evidence={"good_faith_estimate": x.good_faith_estimate, "billed_total": total},
                     amount_at_stake=over, sources=[src("nsa_dispute")])
        else:
            self.add(rule="gfe_within", severity="ok",
                     title="The bill is within $400 of your good faith estimate",
                     explanation=f"Estimate {money(x.good_faith_estimate)}, billed {money(total)}.",
                     sources=[src("nsa_dispute")])

    # ------------------------------------------------------------------ Arizona ground ambulance (ADHS rates)
    BASE_CODES = {"A0427": "als", "A0433": "als", "A0429": "bls", "A0434": "ccs"}
    MILEAGE_CODE = "A0425"

    def ambulance_rates(self) -> None:
        x = self.ctx
        if x.ambulance != "ground" or not x.ambulance_con:
            if x.ambulance == "ground":
                self.skipped["az_ambulance_rate"] = "ambulance company not selected"
            return
        from billcheck.ambulance import find
        r = find(x.ambulance_con)
        if not r:
            self.skipped["az_ambulance_rate"] = "ambulance company not in the ADHS schedule"
            return
        self.run.append("az_ambulance_rate")
        name = r["entity"].split(" dba ")[-1] if " dba " in r["entity"] else r["entity"]
        srcs = [src("adhs_ambulance", as_of=r["schedule_prepared"]), src("ars_36_2239")]
        ev = {"company": r["entity"], "als": r["als"], "bls": r["bls"], "ccs": r["ccs"], "per_mile": r["mileage"],
              "supplies_may_be_charged": r["supplies_separate"], "rate_effective": r["effective"]}
        lines = self.bill.lines if self.bill else []
        coded = False
        for i, bl in enumerate(lines, 1):
            code = (bl.code or "").upper()
            per_unit = bl.amount / bl.units
            if code in self.BASE_CODES and r.get(self.BASE_CODES[code]):
                coded = True
                cap = r[self.BASE_CODES[code]]
                if per_unit > cap + 0.01:
                    self.add(rule="ambulance_over_rate", severity="error", lines=[i], evidence={**ev, "billed": per_unit},
                             title=f"Ambulance base charge is above the rate Arizona approved for {name}",
                             explanation=(f"ADHS set {name}'s {self.BASE_CODES[code].upper()} base rate at "
                                          f"{money(cap)}. The bill charges {money(c(per_unit))}. Arizona law (A.R.S. "
                                          "36-2239) says an ambulance service may not charge more than the approved rate."),
                             action="Ask the ambulance company to correct the charge to the ADHS-approved rate. If they "
                                    "refuse, you can file a complaint with the ADHS Bureau of EMS.",
                             amount_at_stake=c(per_unit - cap), sources=srcs)
            if code == self.MILEAGE_CODE and r.get("mileage"):
                coded = True
                if per_unit > r["mileage"] + 0.01:
                    self.add(rule="ambulance_over_rate", severity="error", lines=[i],
                             evidence={**ev, "billed_per_mile": c(per_unit)},
                             title=f"Ambulance mileage is above the rate Arizona approved for {name}",
                             explanation=(f"ADHS set {name}'s rate at {money(r['mileage'])} per mile. The bill charges "
                                          f"{money(c(per_unit))} per mile."),
                             action="Ask the ambulance company to correct the mileage charge.",
                             amount_at_stake=c((per_unit - r["mileage"]) * bl.units), sources=srcs)
        if not coded and self.bill:
            b = self.bill
            total = c(sum(bl.amount for bl in lines)) if lines else c((b.balance_due or 0) + b.patient_payments
                                                                      + b.insurance_paid + b.adjustments)
            level = x.ambulance_level if x.ambulance_level in ("als", "bls", "ccs") and r.get(x.ambulance_level) else "als"
            cap = r[level] + (r["mileage"] * x.ambulance_miles if x.ambulance_miles else 0)
            if total > cap + 0.01:
                supplies = r["supplies_separate"] in ("Yes", "only Oxygen")
                self.add(rule="ambulance_over_rate", severity="warning" if supplies or not x.ambulance_miles else "error",
                         evidence={**ev, "billed_total": total, "approved_base_plus_mileage": c(cap)},
                         title=f"The ambulance bill is above Arizona's approved rate for {name}",
                         explanation=(f"ADHS approved {money(r[level])} as {name}'s {level.upper()} base rate"
                                      + (f" plus {money(r['mileage'])} per mile, {money(c(cap))} for "
                                         f"{x.ambulance_miles:g} miles" if x.ambulance_miles else "")
                                      + f". The bill totals {money(total)}."
                                      + (" Supplies, medication and oxygen may be charged on top, at prices filed "
                                         "with ADHS." if supplies else "")),
                         action="Ask for an itemized bill with HCPCS codes (A0427, A0429, A0425) and the loaded miles, "
                                "then compare each line with the approved rates.",
                         amount_at_stake=c(total - cap), sources=srcs)   # supplies may explain part of it
            else:
                self.add(rule="ambulance_within_rate", severity="ok", evidence=ev, sources=srcs,
                         title=f"The ambulance bill is within Arizona's approved rate for {name}",
                         explanation=f"Approved: {money(r[level])} base"
                                     + (f" plus {money(r['mileage'])} per mile" if r.get("mileage") else "") + ".")
        if x.transported is False:
            self.add(rule="ambulance_no_transport", severity="warning", evidence=ev, sources=srcs,
                     title="You were not taken to the hospital",
                     explanation=("Under Arizona law an ambulance service may charge the advanced life support base "
                                  "rate without transport only if you received advanced life support care. If you "
                                  "declined treatment or transport, the law lets the service provide the call free of "
                                  "charge (A.R.S. 36-2239(K))."),
                     action=("Ask what care you were billed for. If you declined care, ask them to treat the call as "
                             "gratuitous under A.R.S. 36-2239(K)."))

    # ------------------------------------------------------------------ documents the patient should have
    def paperwork(self) -> None:
        b = self.bill
        if not b:
            return
        self.run.append("paperwork")
        if not b.lines or not any(bl.code for bl in b.lines):
            self.add(rule="itemized_bill", severity="info",
                     title="Ask for an itemized bill",
                     explanation=("A summary bill does not show what each charge is for. An itemized bill lists each "
                                  "service with its code (CPT or HCPCS), revenue code, date and units, which is what "
                                  "you need to check it."),
                     action="Ask the billing office: 'Please send me an itemized bill with CPT or HCPCS codes.'")
        if b.provider_type == "unknown":
            self.add(rule="facility_or_provider", severity="info",
                     title="Is this a hospital (facility) bill or a doctor (professional) bill?",
                     explanation=("Hospitals often send separate bills for the facility and for the doctors, from "
                                  "different billing offices. Billing staff will ask which one you are calling about."),
                     action="Look for 'professional', a physician group name, or 'hospital services' on the bill.")

    # ------------------------------------------------------------------
    BILL_TOTALS = ("balance_over_eob", "gfe_dispute")          # whole-bill differences
    BILL_LINES = ("duplicate_line", "bill_line_not_on_eob", "mue_units", "ncci_pair", "self_pay_over_cash",
                  "ambulance_over_rate")
    EOB_SIDE = ("allowed_vs_published", "eob_denied", "er_rate_over", "oop_met_still_owe")   # decided by the insurer

    def amount_at_stake(self) -> float:
        """Money in question without double counting: line-level bill problems usually explain the whole-bill
        difference, so the larger of the two counts; insurer-side amounts are added; the total never exceeds the
        bill balance."""
        amt = defaultdict(float)
        for f in self.findings:
            if f.severity in ("error", "warning") and f.amount_at_stake:
                amt[f.rule] += f.amount_at_stake
        bill_side = max([amt[r] for r in self.BILL_TOTALS] + [sum(amt[r] for r in self.BILL_LINES)])
        total = bill_side + sum(amt[r] for r in self.EOB_SIDE)
        if self.bill and self.bill.balance_due is not None:
            total = min(total, self.bill.balance_due)
        return c(total)

    def result(self) -> CheckResult:
        if not self.eob and not self.bill:
            return CheckResult(summary=Summary(verdict="not_enough_data",
                                               headline="Enter your EOB, your bill, or both."),
                               findings=[], checks_run=[])
        for step in (self.eob_arithmetic, self.plan_balances, self.bill_vs_eob, self.duplicates, self.units_mue,
                     self.code_pairs,
                     self.published, self.er_visit, self.surprises, self.ambulance_rates, self.paperwork):
            step()
        order = {"error": 0, "warning": 1, "info": 2, "ok": 3}
        self.findings.sort(key=lambda f: (order[f.severity], -(f.amount_at_stake or 0)))
        counts = Counter(f.severity for f in self.findings)
        at_stake = self.amount_at_stake()
        balance = self.bill.balance_due if self.bill else None
        owed = self.eob_owe() if self.eob and self.ctx.coverage == "insured" else None
        compared = self.lines_checked > 0 or bool(set(self.run) & {
            "bill_vs_eob", "published_prices", "duplicates", "mue_units", "ncci_ptp", "az_ambulance_rate"}) \
            or any(f.rule in ("gfe_dispute", "gfe_within", "balance_matches_eob") for f in self.findings)
        if counts["error"]:
            verdict = "likely_errors"
            n = counts["error"]
            headline = (f"We found {n} likely error{'s' if n > 1 else ''}"
                        + (f" worth up to {money(at_stake)}." if at_stake else "."))
        elif counts["warning"]:
            verdict = "questions"
            n = counts["warning"]
            headline = f"{n} thing{'s' if n > 1 else ''} to ask about before you pay."
        elif not compared:
            verdict = "not_enough_data"
            headline = "We could not compare your bill with anything yet."
        else:
            verdict = "looks_right"
            headline = "Nothing in what you entered looks wrong."
            if owed is not None and owed <= TOL and not self.bill:
                headline = "Your EOB says you owe $0 for this claim."
                self.add(rule="eob_owe_zero", severity="ok", title="You owe $0 for this claim",
                         explanation=("Your plan's discounts and payments cover the whole charge. The EOB is not a "
                                      "bill, but it is what the provider must follow."),
                         action=("Keep this EOB. If the provider later sends a bill for these services, do not pay "
                                 "it: call the billing office and give them the claim number on the EOB."),
                         sources=[src("cms_eob")])
                counts = Counter(f.severity for f in self.findings)
        return CheckResult(
            summary=Summary(verdict=verdict, headline=headline, eob_you_owe=owed, bill_balance=balance,
                            difference=c(balance - max((owed or 0) - (self.bill.patient_payments if self.bill else 0), 0))
                            if owed is not None and balance is not None else None,
                            amount_at_stake=at_stake, counts=dict(counts)),
            findings=self.findings, checks_run=self.run, checks_skipped=self.skipped)


def check(req: CheckRequest, prices: dict[str, dict] | None = None,
          mue: dict[str, dict[str, MueEdit]] | None = None, ptp: PtpTable | None = None) -> CheckResult:
    from billcheck.kit import build_kit
    res = Checker(req, prices, mue or {}, ptp).result()
    res.letter, res.call_script = build_kit(req, res)      # letters stay in English: they go to US billing offices
    if req.context.lang == "es":
        from billcheck.es import to_spanish
        res = to_spanish(res)
    return res
