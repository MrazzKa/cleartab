"""Feature 4: deterministic payer and plan matching (case folding, punctuation, regex, alias table only).

Canonical list (about 10 Arizona insurers + "other"), from the payer strings in the H1 files and the AHCCCS
contractor list (AHCCCS Population by Health Care Contractor, September 2026,
https://www.azahcccs.gov/Resources/Downloads/PopulationStatistics/PopulationbyContractor09102026.pdf).

Every mapping carries method (alias table | regex) and confidence (high | medium). "medium" marks a judgement
a human rater must confirm; the reason is in the note column of payer_aliases.csv.
"""
import csv
import re

from pipeline.common import PROCESSED, now_utc

AHCCCS_SOURCE = "https://www.azahcccs.gov/Resources/Downloads/PopulationStatistics/PopulationbyContractor09102026.pdf"

CANONICAL = [
    "Aetna", "Blue Cross Blue Shield of Arizona", "Cigna", "UnitedHealthcare", "Humana", "Banner Health plans",
    "Mercy Care", "Health Choice Arizona", "Centene (Arizona Complete Health, Ambetter, Health Net, Wellcare)",
    "Molina", "Oscar", "other",
]
CENTENE = CANONICAL[8]

# normalized payer string -> (canonical, confidence, note). Keys are produced by norm().
ALIASES = {
    "aetna": ("Aetna", "high", ""),
    "blue cross blue shield of arizona": ("Blue Cross Blue Shield of Arizona", "high", ""),
    "bcbs az": ("Blue Cross Blue Shield of Arizona", "high", ""),
    "bcbs": ("Blue Cross Blue Shield of Arizona", "medium", "BCBS without state; files are Arizona hospitals"),
    "cigna": ("Cigna", "high", ""),
    "cigna healthcare of arizona inc": ("Cigna", "high", ""),
    "united": ("UnitedHealthcare", "high", ""),
    "united healthcare": ("UnitedHealthcare", "high", ""),
    "unitedhealthcare": ("UnitedHealthcare", "high", ""),
    "arizona physicians ipa": ("UnitedHealthcare", "medium",
                               "APIPA is the former name of UnitedHealthcare Community Plan in AHCCCS"),
    "humana": ("Humana", "high", ""),
    "humana bh": ("Humana", "medium", "Humana behavioral health product"),
    "united bh": ("UnitedHealthcare", "medium", "UnitedHealthcare behavioral health product"),
    "banner university": ("Banner Health plans", "high", ""),
    "health net of arizona": (CENTENE, "high", ""),
    "arizona complete health": (CENTENE, "high", ""),
    "banner health": ("Banner Health plans", "high", ""),
    "banner": ("Banner Health plans", "high", ""),
    "banner university health plan": ("Banner Health plans", "high", ""),
    "banner university family": ("Banner Health plans", "high", ""),
    "mercy care": ("Mercy Care", "high", ""),
    "mercy care plan": ("Mercy Care", "high", ""),
    "health choice": ("Health Choice Arizona", "high", ""),
    "health choice arizona inc": ("Health Choice Arizona", "high", ""),
    "ambetter": (CENTENE, "high", ""),
    "allwell": (CENTENE, "high", "Allwell / Wellcare are Centene Medicare plans"),
    "wellcare": (CENTENE, "high", ""),
    "centene": (CENTENE, "high", ""),
    "celtic aka centene": (CENTENE, "high", ""),
    "health net": (CENTENE, "high", ""),
    "arizona complete care": (CENTENE, "medium", "read as Arizona Complete Health - Complete Care Plan (AHCCCS)"),
    "care 1st": (CENTENE, "medium", "Care1st Arizona is owned by WellCare/Centene; AHCCCS enrollment 0 in Sep 2026"),
    "molina": ("Molina", "high", ""),
    "magellan health": ("Molina", "medium", "Magellan Complete Care of Arizona (AHCCCS) was acquired by Molina"),
    "oscar health plan": ("Oscar", "high", ""),
    # Spellings in the Tucson Medical Center and Northwest Healthcare files (added 2026-10-13).
    "arizona complete": (CENTENE, "high", ""),
    "complete health medicaid az": (CENTENE, "high", ""),
    "banner university family care": ("Banner Health plans", "high", ""),
    "banner ufc medicaid az": ("Banner Health plans", "high", ""),
    "health choice medicaid az": ("Health Choice Arizona", "high", ""),
    "mercy care medicaid az": ("Mercy Care", "high", ""),
    "apipa medicaid az": ("UnitedHealthcare", "medium",
                          "APIPA is the former name of UnitedHealthcare Community Plan in AHCCCS"),
    "uhc hix": ("UnitedHealthcare", "high", ""),
    "uhc": ("UnitedHealthcare", "high", ""),
    "bcbs az ppo hmo nbr": ("Blue Cross Blue Shield of Arizona", "high", ""),
    "bcbs pimaconnect": ("Blue Cross Blue Shield of Arizona", "high", ""),
    "bcbs az pima connect": ("Blue Cross Blue Shield of Arizona", "high", ""),
    "blue cross blue shield": ("Blue Cross Blue Shield of Arizona", "medium",
                               "no state given; read as BCBS of Arizona because the files are Arizona hospitals"),
    "blue cross health choice": ("Blue Cross Blue Shield of Arizona", "medium",
                                 "BCBSAZ Health Choice plan; Health Choice Arizona is owned by BCBSAZ"),
    "magellan medicaid az": ("Molina", "medium",
                             "Magellan Complete Care of Arizona (AHCCCS) was acquired by Molina"),
}

# Plans that are not the named insurer's own product for a patient: rental networks, workers compensation.
OTHER_PLAN_RULES = [
    (re.compile(r"rental|first health|multiplan|provider network of america|plotkin|nhsi"), "rental network",
     "rental or access network rate, not an insurer's member plan"),
    (re.compile(r"work(ers)? ?comp"), "workers comp", "workers compensation rate, not paid by a patient's plan"),
]
PLAN_TYPE_RULES = [
    (re.compile(r"supplement"), "medicare supplement"),
    (re.compile(r"medicaid|ahcccs|\bltc\b|managed care program|apipa"), "ahcccs"),
    (re.compile(r"medicare|advantage|\bdual\b|care improvement plus|university care advantage|\bma\b|mcr adv"),
     "medicare advantage"),
    (re.compile(r"exchange|\bhix\b|marketplace|\baca\b|\bifp\b|\bqhp\b|hmox|ppox"), "marketplace"),
    (re.compile(r"tricare|government|community care network|veterans|federal prison"), "government"),
    (re.compile(r"commer|hmo|ppo|epo|all plans|all other plans|navigate|options|compass|core|doctor|localplus|"
                r"surefit|lifesource|localflex|focus|neighborhood|alliance|hpn|network|signature|savings|"
                r"employee|designated|joint venture|nap|acn|spp|interlink|intel|optumhealth"), "commercial"),
]


def norm(s: str) -> str:
    s = re.sub(r"\[\s*\d+\s*\]", " ", (s or ""))  # Mayo appends payer IDs: "AETNA [91160003]"
    s = s.casefold().replace("&", " and ")
    s = re.sub(r"\(.*?\)", lambda m: " " + m.group(0)[1:-1] + " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def plan_type(payer: str, plan: str) -> str:
    text = f"{norm(plan)} {norm(payer)}"
    for rx, t in PLAN_TYPE_RULES:
        if rx.search(text):
            return t
    return "unknown"


def match(payer: str, plan: str) -> dict:
    p, pl = norm(payer), norm(plan)
    out = {"raw_payer": payer, "raw_plan": plan, "plan_type": plan_type(payer, plan)}
    for rx, ptype, note in OTHER_PLAN_RULES:
        if rx.search(pl) or rx.search(p):
            return {**out, "canonical_payer": "other", "plan_type": ptype, "method": "regex",
                    "confidence": "high", "note": note}
    if p == "magellan" and "medicaid" in pl:
        return {**out, "canonical_payer": "Molina", "method": "regex", "confidence": "medium",
                "note": "Magellan Complete Care of Arizona (AHCCCS) was acquired by Molina"}
    if p in ALIASES:
        canon, conf, note = ALIASES[p]
        return {**out, "canonical_payer": canon, "method": "alias table", "confidence": conf, "note": note}
    # Payer column filled with a long plan-style name: try regex on brand words.
    for rx, canon in ((r"\bunited ?healthcare\b", "UnitedHealthcare"), (r"\baetna\b", "Aetna"),
                      (r"\bcigna\b", "Cigna"), (r"\bhumana\b", "Humana"), (r"\bmolina\b", "Molina"),
                      (r"\boscar\b", "Oscar")):
        if re.search(rx, p):
            return {**out, "canonical_payer": canon, "method": "regex", "confidence": "high", "note": ""}
    return {**out, "canonical_payer": "other", "method": "alias table", "confidence": "high",
            "note": "not one of the canonical insurers"}


def build_dictionary() -> list[dict]:
    with open(PROCESSED / "payer_strings.csv", newline="") as f:
        strings = list(csv.DictReader(f))
    pairs: dict[tuple[str, str], int] = {}
    for r in strings:
        k = (r["raw_payer"], r["raw_plan"])
        pairs[k] = pairs.get(k, 0) + int(r["row_count"])
    rows = []
    for (payer, plan), n in sorted(pairs.items()):
        m = match(payer, plan)
        rows.append({**m, "row_count": n, "rater_status": "provisional",
                     "source_url": "data/processed/payer_strings.csv; AHCCCS list: " + AHCCCS_SOURCE,
                     "retrieved_at": now_utc()})
    with open(PROCESSED / "payer_aliases.csv", "w", newline="") as f:
        cols = ["raw_payer", "raw_plan", "canonical_payer", "plan_type", "method", "confidence", "note",
                "row_count", "rater_status", "source_url", "retrieved_at"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    rows = build_dictionary()
    from collections import Counter
    print(len(rows), "raw payer+plan strings")
    print(Counter(r["canonical_payer"] for r in rows))
    print(Counter(r["plan_type"] for r in rows))
    print("medium confidence:", sum(r["confidence"] == "medium" for r in rows))
