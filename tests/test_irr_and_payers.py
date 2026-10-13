from pipeline.payers import match, norm
from research.h2.irr_score import kappa


def test_kappa_perfect_and_chance():
    assert kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert abs(kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])) < 1e-9


def test_rules():
    assert norm("BCBS - AZ") == "bcbs az"
    assert norm("AETNA [91160003]") == "aetna"
    assert match("Aetna", "Medical Rental")["canonical_payer"] == "other"          # rental network
    assert match("BCBS - AZ", "Commercial|Workers Comp")["plan_type"] == "workers comp"
    assert match("UNITED HEALTHCARE", "UNITED HEALTHCARE APIPA")["plan_type"] == "ahcccs"
    m = match("Ambetter", "Az Complete Exchange")
    assert m["canonical_payer"].startswith("Centene") and m["plan_type"] == "marketplace"
    assert match("Quiktrip Corporation", "Commercial")["canonical_payer"] == "other"


def test_brand_words_and_network_contract():
    assert match("UHC Navigate", "UHC Navigate")["canonical_payer"] == "UnitedHealthcare"
    assert match("BCBSAZ MCR ADV", "NODE BCBS AZ MCR ADV")["canonical_payer"] == "Blue Cross Blue Shield of Arizona"
    m = match("BOILERMAKERS NATIONAL FUND [91160079]", "AZ CIGNA [39]")       # fund using Cigna's contract
    assert m["canonical_payer"] == "Cigna" and m["method"] == "network contract"
    assert match("OSCAR PPO [91160912]", "AZ CIGNA [39]")["canonical_payer"] == "Oscar"  # payer column wins
    assert match("MULTIPLAN", "AZ CIGNA [39]")["canonical_payer"] == "other"           # rental network stays other
    assert match("WORLD INSURANCE [91160466]", "AZ FL BY PLAN [182]")["canonical_payer"] == "other"
