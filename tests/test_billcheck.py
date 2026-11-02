"""Bill check rule engine. Synthetic reference data only, so these run without a database or CMS files."""
import copy

from billcheck import demo_cases
from billcheck.models import CheckRequest
from billcheck.reference import MueEdit, PtpTable
from billcheck.rules import check

CASES = {c["id"]: c["request"] for c in demo_cases()}
PRICES_030064_BCBS = {
    "73721": {"code": "73721", "hospital": "Test Hospital", "ccn": "030064", "cash": 685.61, "gross": 3706.0,
              "neg_min": 712.68, "neg_median": 798.19, "neg_max": 950.22, "neg_n": 10,
              "source_url": "https://example.org/mrf.json", "retrieved_at": "2026-10-12"},
    "85025": {"code": "85025", "hospital": "Test Hospital", "ccn": "030064", "cash": 5.82, "gross": 42.5,
              "neg_min": 7.77, "neg_median": 23.98, "neg_max": 30.93, "neg_n": 8,
              "source_url": "https://example.org/mrf.json", "retrieved_at": "2026-10-12"},
}
PRICES_030024 = {
    "71046": {"code": "71046", "hospital": "Test Hospital", "ccn": "030024", "cash": 254.03, "gross": 665.0,
              "neg_min": None, "neg_median": None, "neg_max": None, "neg_n": 0, "source_url": "u", "retrieved_at": "d"},
    "80053": {"code": "80053", "hospital": "Test Hospital", "ccn": "030024", "cash": 131.41, "gross": 344.0,
              "neg_min": None, "neg_median": None, "neg_max": None, "neg_n": 0, "source_url": "u", "retrieved_at": "d"},
    "85025": {"code": "85025", "hospital": "Test Hospital", "ccn": "030024", "cash": 96.27, "gross": 252.0,
              "neg_min": None, "neg_median": None, "neg_max": None, "neg_n": 0, "source_url": "u", "retrieved_at": "d"},
}


def run(case: str, **kw):
    return check(CheckRequest(**CASES[case]), **kw)


def rules(res) -> dict[str, str]:
    return {f.rule: f.severity for f in res.findings}


def test_cms_sample_matches():
    res = run("cms-sample-ok")
    assert res.summary.verdict == "looks_right"
    assert res.summary.eob_you_owe == 35.0 and res.summary.difference == 0.0
    assert rules(res)["balance_matches_eob"] == "ok"
    assert res.letter == "" and res.call_script == []


def test_payment_not_subtracted():
    res = run("copay-paid-twice")
    f = next(f for f in res.findings if f.rule == "balance_over_eob")
    assert f.severity == "error" and f.amount_at_stake == 35.0
    assert "payment may not be subtracted" in f.title
    assert "[Your name]" in res.letter and "[Account number]" in res.letter


def test_knee_mri_findings_and_no_double_counting():
    res = run("knee-mri-tucson", prices=PRICES_030064_BCBS)
    r = rules(res)
    assert r["balance_over_eob"] == "error"
    assert r["duplicate_line"] == "warning"
    assert r["bill_line_not_on_eob"] == "warning"
    assert r["allowed_vs_published"] == "warning"
    assert r["allowed_matches_published"] == "ok"
    # $67.50 bill difference (duplicate $42.50 + blood draw $25.00 inside it) + $199.78 above the published maximum
    assert res.summary.amount_at_stake == 267.28
    assert res.findings[0].severity == "error"


def test_self_pay_good_faith_estimate():
    res = run("self-pay-estimate", prices=PRICES_030024)
    r = rules(res)
    assert r["gfe_dispute"] == "error"
    assert r["self_pay_over_cash"] == "warning"
    assert res.summary.amount_at_stake == 779.29        # the larger of the GFE excess and the cash excess


def test_good_faith_estimate_too_late_is_a_warning():
    req = copy.deepcopy(CASES["self-pay-estimate"])
    req["context"]["today"] = "2027-03-30"
    res = check(CheckRequest(**req))
    assert rules(res)["gfe_dispute"] == "warning"


def test_emergency_out_of_network_is_protected():
    res = run("er-doctor-out-of-network")
    r = rules(res)
    assert r["balance_over_eob"] == "error" and r["nsa_emergency"] == "info"


def test_ground_ambulance_and_denial():
    res = run("ground-ambulance-denied")
    r = rules(res)
    assert r["eob_denied"] == "warning" and r["nsa_ground_ambulance"] == "info"
    assert r["balance_over_eob"] == "warning"           # out of network, no federal protection
    assert res.summary.amount_at_stake == 2400.0


def test_eob_arithmetic():
    req = copy.deepcopy(CASES["cms-sample-ok"])
    req["eob"]["lines"][1]["plan_paid"] = 90.00
    res = check(CheckRequest(**req))
    assert rules(res)["eob_line_sum"] == "warning"


def test_mue_units():
    req = copy.deepcopy(CASES["knee-mri-tucson"])
    req["bill"]["lines"][0]["units"] = 4
    mue = {"facility outpatient": {"73721": MueEdit(3, "3 Date of Service Edit: Clinical", "facility outpatient",
                                                    "10-01-2026")}}
    res = check(CheckRequest(**req), mue=mue)
    f = next(f for f in res.findings if f.rule == "mue_units")
    assert f.severity == "warning" and f.evidence["limit"] == 3


def test_code_pairs():
    req = {"context": {"coverage": "insured"},
           "bill": {"provider_type": "facility", "balance_due": 100, "lines": [
               {"service_date": "2026-09-01", "code": "11111", "amount": 60},
               {"service_date": "2026-09-01", "code": "22222", "amount": 40}]}}
    ptp = PtpTable(pairs={"11111": {"22222": "0"}})
    res = check(CheckRequest(**req), ptp=ptp)
    assert rules(res)["ncci_pair"] == "error"
    assert "ncci_ptp" not in check(CheckRequest(**req)).checks_run


def test_nothing_entered():
    res = check(CheckRequest())
    assert res.summary.verdict == "not_enough_data"


def test_assistance_bands():
    from billcheck.assistance import AssistanceRequest, evaluate, fpl_percent, poverty_line
    assert poverty_line(1) == 15960 and poverty_line(4) == 33000
    assert fpl_percent(66000, 4) == 200.0
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=4, annual_income=66000))["results"]}
    assert res["Banner Health"]["result"] == "75% discount off AGB"           # policy: free care below 200%
    assert res["HonorHealth"]["status"] == "free"                            # 0-200% inclusive
    assert res["Tenet (Abrazo, Carondelet)"]["status"] == "unknown"
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=4, annual_income=66100))["results"]}
    assert res["HonorHealth"]["result"].startswith("87%")
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=1, annual_income=90000))["results"]}
    assert res["Mayo Clinic"]["status"] == "above"
