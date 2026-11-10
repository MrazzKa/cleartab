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
    assert res["Tenet (Abrazo, Carondelet)"]["status"] == "above"           # charity care below 200%
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=4, annual_income=66100))["results"]}
    assert res["HonorHealth"]["result"].startswith("87%")
    assert res["Dignity Health (CommonSpirit)"]["status"] == "unknown"   # 200.3%: between "200%" and "201%"
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=4, annual_income=132000))["results"]}
    assert res["HonorHealth"]["status"] == "above"                       # exactly 400%: policy says less than 400%
    res = {r["system"]: r for r in evaluate(AssistanceRequest(household_size=1, annual_income=90000))["results"]}
    assert res["Mayo Clinic"]["status"] == "above"


def test_bill_without_eob_is_not_called_right():
    req = {"context": {"coverage": "insured"}, "bill": {"balance_due": 480.0}}
    res = check(CheckRequest(**req))
    assert res.summary.verdict == "questions" and rules(res)["no_eob_yet"] == "warning"
    res = check(CheckRequest(**{"context": {"coverage": "self_pay"}, "bill": {"balance_due": 480.0}}))
    assert res.summary.verdict == "not_enough_data"


def test_quick_check_totals_only():
    req = {"context": {"coverage": "insured", "network": "in"}, "eob": {"lines": [], "you_owe_total": 35.0},
           "bill": {"balance_due": 35.0, "patient_payments": 35.0}}
    res = check(CheckRequest(**req))
    assert rules(res)["balance_over_eob"] == "error" and res.summary.amount_at_stake == 35.0


def test_reader_parses_model_json(monkeypatch):
    import json as _json

    from billcheck import reader

    class Resp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": _json.dumps({
                "document_type": "eob", "you_owe_total": 35, "eob_lines": [{"description": "Medical care",
                                                                          "allowed": 118.12, "you_owe": 35}],
                "unreadable": []})}}]}

    class Session:
        def post(self, url, **kw):
            assert kw["json"]["response_format"] == {"type": "json_object"}
            return Resp()

    monkeypatch.delenv("JETSTREAM_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test")
    r = reader.read_document([(b"\xff\xd8fake", "image/jpeg")], session=Session())
    assert r.document_type == "eob" and r.you_owe_total == 35 and r.eob_lines[0].allowed == 118.12
    monkeypatch.delenv("GROQ_API_KEY")
    import pytest
    with pytest.raises(reader.ReaderError):
        reader.read_document([(b"x", "image/jpeg")])


def test_ambulance_rates_from_adhs_schedule():
    from billcheck.ambulance import find, parse
    sample = """139 fp
Alliance Ambulance of Arizona, LLC
dba ABC Ambulance ( 1,047.08)      ( 932.33)         ( 14.36)   ( 233.08)      00117 04/17/26 Yes
90 fp Action Medical Service Inc. - Ganado ( 1,644.37)      ( 1,644.37)      ( 20.33)   ( 411.07)      00117 04/17/26 No"""
    rows = parse(sample)
    assert [r["con"] for r in rows] == ["139", "90"]
    assert rows[0]["als"] == 1047.08 and rows[0]["bls"] == 932.33 and rows[0]["mileage"] == 14.36
    assert rows[0]["supplies_separate"] == "Yes" and rows[1]["entity"] == "Action Medical Service Inc. - Ganado"
    if find("108"):     # built from the ADHS PDF (python -m billcheck.ambulance)
        req = {"context": {"coverage": "insured", "ambulance": "ground", "ambulance_con": "108", "transported": False},
               "bill": {"provider_type": "ambulance", "balance_due": 1950,
                        "lines": [{"code": "A0427", "amount": 1950}, {"code": "A0425", "units": 4, "amount": 180}]}}
        res = check(CheckRequest(**req))
        over = [f for f in res.findings if f.rule == "ambulance_over_rate"]
        assert len(over) == 2 and all(f.severity == "error" for f in over)
        assert rules(res)["ambulance_no_transport"] == "warning"


def test_spanish_findings_keep_numbers_and_english_letter():
    req = copy.deepcopy(CASES["copay-paid-twice"])
    req["context"]["lang"] = "es"
    res = check(CheckRequest(**req))
    f = next(f for f in res.findings if f.rule == "balance_over_eob")
    assert f.title.startswith("Es posible") and "$35.00" in f.explanation
    assert res.summary.headline.startswith("Encontramos")
    assert "I compared my bill" in res.letter
    for case in CASES.values():                       # every finding of every demo case has Spanish text
        c = copy.deepcopy(case)
        c["context"]["lang"] = "es"
        for f in check(CheckRequest(**c), prices=PRICES_030064_BCBS).findings:
            from billcheck.es import es
            assert es(f) is not None, f.rule


def test_reader_aligns_amounts_to_printed_columns():
    from billcheck.reader import ReadResult, align_columns
    r = ReadResult(document_type="eob",
                   eob_columns=["Service", "Date", "Amount Billed", "Network Discount", "Amount Paid By Your Plan",
                                "Amount From Another Source", "Total Plan Discount & Payments", "Deductible",
                                "Coinsurance", "Amount Not Covered", "Your Total Responsibility"],
                   eob_lines=[{"description": "Office visit", "plan_paid": 0,          # the model's own guess
                               "amounts": [200, 80, 90, 0, 170, 20, 10, 0, 30]}])
    ln = align_columns(r).eob_lines[0]
    assert (ln.billed, ln.discount, ln.plan_paid, ln.deductible, ln.coinsurance, ln.you_owe) == (200, 80, 90, 20, 10, 30)


def test_reader_aligns_unitedhealthcare_columns():
    """Header layout of a real UnitedHealthcare EOB (2026); "Plan does not cover" once stopped the alignment."""
    from billcheck.reader import ReadResult, align_columns
    r = ReadResult(document_type="eob",
                   eob_columns=["Provider billed", "Amount saved", "Plan allowed amount", "Your plan paid",
                                "Applied to deductible", "Copay", "Coinsurance", "Plan does not cover",
                                "Amount you owe**"],
                   eob_lines=[{"description": "Office visits", "plan_paid": 265.68, "deductible": 0,  # model's guess
                               "amounts": [389.0, 123.32, 265.68, 0.0, 265.68, 0.0, 0.0, 0.0, 265.68]}])
    ln = align_columns(r).eob_lines[0]
    assert (ln.billed, ln.allowed, ln.plan_paid, ln.deductible, ln.not_covered, ln.you_owe) == \
        (389.0, 265.68, 0.0, 265.68, 0.0, 265.68)


def test_eob_with_discount_column_and_zero_owed():
    lines = [{"description": "Blood draw", "billed": 40, "discount": 40, "plan_paid": 0, "you_owe": 0},
             {"description": "Emergency visit", "billed": 1000, "discount": 600, "plan_paid": 400, "you_owe": 0}]
    res = check(CheckRequest(context={"coverage": "insured"},
                             eob={"lines": lines, "you_owe_total": 0, "oop_max_met": True}))
    r = rules(res)
    assert res.summary.verdict == "looks_right" and "$0" in res.summary.headline
    assert "eob_line_sum" not in r and r["eob_zero_allowed"] == "info" and r["oop_max_met"] == "info"
    assert r["network_discount"] == "info" and r["eob_owe_zero"] == "ok"
    bad = [{**lines[1], "plan_paid": 0}]          # a misread column must not pass silently
    assert rules(check(CheckRequest(eob={"lines": bad}))).get("eob_line_sum") == "warning"


def test_pdf_row_amounts_come_from_text_layer():
    """A real UnitedHealthcare ER EOB: the model shifted $1,543 from deductible to copay; the text layer is exact."""
    from billcheck.reader import ReadResult, align_columns, amounts_from_text
    cols = ["Provider billed", "Amount saved", "Plan allowed amount", "Your plan paid", "Applied to deductible",
            "Copay", "Coinsurance", "Plan does not cover", "Amount you owe**"]
    text = ("Provider billed  $3,411.00\n"
            "UG $1,588.00 $45.00 $1,543.00 $0.00 $1,543.00 $0.00 $0.00 $0.00 $1,543.00\n"
            "D2 $5.00 $5.00 $0.00 $0.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
            "D2 $1,818.00 $1,818.00 $0.00 $0.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
            "Total amount $3,411.00 $1,868.00 $1,543.00 $0.00 $1,543.00 $0.00 $0.00 $0.00 $1,543.00\n")
    misread = [1588.0, 45.0, 1543.0, 0.0, 0.0, 1543.0, 0.0, 0.0, 1543.0]
    r = ReadResult(document_type="eob", eob_columns=cols,
                   eob_lines=[{"amounts": misread}, {"amounts": [5.0] + [0.0] * 8}, {"amounts": [1818.0] + [0.0] * 8}])
    ln = align_columns(amounts_from_text(r, text)).eob_lines
    assert (ln[0].deductible, ln[0].copay, ln[0].you_owe) == (1543.0, 0, 1543.0)
    assert (ln[2].billed, ln[2].allowed, ln[2].you_owe) == (1818.0, 0.0, 0.0)
    # rows that do not match the model's rows one to one leave the model's copy untouched
    r2 = ReadResult(document_type="eob", eob_columns=cols, eob_lines=[{"amounts": misread}])
    assert amounts_from_text(r2, text).eob_lines[0].amounts == misread


def test_reader_falls_back_to_next_service_and_parses_fenced_json(monkeypatch):
    import json as _json

    from billcheck import reader
    calls = []

    class Resp:
        def __init__(self, code, content=""):
            self.status_code, self.content = code, content

        def json(self):
            return {"choices": [{"message": {"content": self.content}}]}

    class Session:
        def post(self, url, **kw):
            calls.append((url, kw["json"]["model"]))
            if "jetstream" in url:
                return Resp(503)
            return Resp(200, "Here it is:\n```json\n" + _json.dumps({"document_type": "bill", "balance_due": 40}) + "\n```")

    monkeypatch.setenv("JETSTREAM_API_KEY", "j")
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.delenv("READER_PROVIDERS", raising=False)
    r = reader.read_document([(b"\xff\xd8fake", "image/jpeg")], session=Session())
    assert [m for _, m in calls] == ["muse-glimmer", reader.MODEL]
    assert r.balance_due == 40 and "Groq" in r.model


def test_read_mode_examples_only(monkeypatch):
    import pytest

    from billcheck import reader
    monkeypatch.setenv("READ_MODE", "examples")
    with pytest.raises(reader.ReaderError):
        reader.check_allowed([(b"a real bill", "image/jpeg")])
    for e in reader.examples():
        reader.check_allowed([((reader.EXAMPLES_DIR / e["name"]).read_bytes(), "application/pdf")])
    monkeypatch.setenv("READ_MODE", "off")
    assert not reader.available()
    with pytest.raises(reader.ReaderError):
        reader.check_allowed([(b"x", "image/png")])
    monkeypatch.setenv("READ_MODE", "anything else")
    assert reader.read_mode() == "off"
