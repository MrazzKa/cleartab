from pipeline.payers import match, norm
from research.h2.irr_score import kappa


def test_kappa_perfect_and_chance():
    assert kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert abs(kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])) < 1e-9


def test_rules():
    assert norm("BCBS - AZ") == "bcbs az"
    assert match("Aetna", "Medical Rental")["canonical_payer"] == "other"          # rental network
    assert match("BCBS - AZ", "Commercial|Workers Comp")["plan_type"] == "workers comp"
    assert match("UNITED HEALTHCARE", "UNITED HEALTHCARE APIPA")["plan_type"] == "ahcccs"
    m = match("Ambetter", "Az Complete Exchange")
    assert m["canonical_payer"].startswith("Centene") and m["plan_type"] == "marketplace"
    assert match("Quiktrip Corporation", "Commercial")["canonical_payer"] == "other"
