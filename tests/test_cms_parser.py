"""Parser tests on fixtures cut unchanged from real hospital files (first rows of each file)."""
import pathlib

from pipeline.parsers.cms import parse_file

FIX = pathlib.Path(__file__).parent / "fixtures"


def run(name, ccn):
    prof, rows = parse_file(str(FIX / name), ccn)
    return prof, list(rows)


def test_banner_tall_csv():
    prof, rows = run("030064_tall.csv", "030064")
    assert prof.format == "CMS CSV tall"
    assert prof.schema_version == "3.0.0"
    assert prof.last_updated_on == "2026-09-25"
    assert prof.org_npi == "1265820179"
    assert prof.attester_name == "Katie LeBlanc"
    assert prof.attestation_statement == "present"
    assert prof.source_items == 40
    first = [r for r in rows if r["description"] == "R&B MEDICAL/SURGICAL PVT" and r["code"] == "93419"]
    # Room and board rows carry only CDM and RC codes, so they are not usable codes.
    assert first and not first[0]["usable_code"]
    gross = [r for r in first if r["price_type"] == "gross"]
    assert len(gross) == 1 and gross[0]["amount"] == 3477.0      # gross emitted once, not once per payer row
    neg = [r for r in first if r["price_type"] == "negotiated_dollar" and r["payer_name"] == "Aetna"]
    assert neg[0]["amount"] == 1783.70 and neg[0]["methodology"] == "percent of total billed charges"


def test_small_tall_csv_no_payers():
    prof, rows = run("030152_tall.csv", "030152")
    assert prof.attester_name == "Nat Rocha"
    assert prof.last_updated_on == "2/1/2026"
    r = [x for x in rows if x["description"].startswith("INCISION & DRAINAGE ABSCESS SIMPLE")]
    types = {x["price_type"]: x["amount"] for x in r}
    assert types == {"gross": 1052.9, "cash": 631.74}
    assert prof.element_status("median_amount").startswith("not applicable")  # no percent or algorithm rates


def test_dignity_json():
    prof, rows = run("030024.json", "030024")
    assert prof.format == "CMS JSON"
    assert prof.org_npi == "1982733655|1992131734"
    assert prof.attestation_statement == "present"
    assert prof.attestation_confirmed == "True"
    drg = [r for r in rows if r["code"] == "001" and r["code_type"] == "MS-DRG"]
    assert drg and all(r["usable_code"] for r in drg)
    pct = [r for r in drg if r["price_type"] == "negotiated_percent" and r["payer_name"] == "First Health"]
    assert pct[0]["percentage"] == 70.0 and pct[0]["amount"] is None   # a percentage is never a dollar price
    counts = [r for r in drg if r["price_type"] == "allowed_count"]
    assert counts and counts[0]["amount"] == 0.0
    assert prof.element_status("count") == "present"
    assert prof.element_status("median_amount") == "missing"   # percent rows here carry a count but no median


def test_uspi_json_cash_on_drg():
    prof, rows = run("030107.json", "030107")
    cash = [r for r in rows if r["code"] == "770" and r["price_type"] == "cash"]
    assert cash[0]["amount"] == 5844.75
    assert prof.payer_strings[("United Healthcare", "Navigate")] >= 1


def test_wide_csv_synthetic(tmp_path):
    # No wide CSV exists in the H1 sample; this 2-row file follows the CMS v3 wide template layout.
    p = tmp_path / "wide.csv"
    p.write_text(
        "hospital_name,last_updated_on,version,type_2_npi,attester_name\n"
        "Test Hospital,2026-01-01,3.0.0,1234567890,A Person\n"
        "description,code|1,code|1|type,setting,standard_charge|gross,standard_charge|discounted_cash,"
        "standard_charge|Aetna|PPO|negotiated_dollar,standard_charge|Aetna|PPO|negotiated_percentage,"
        "standard_charge|Aetna|PPO|methodology,median_amount|Aetna|PPO\n"
        "KNEE MRI,73721,CPT,outpatient,2379,457,900,,fee schedule,\n"
        "LAB,80053,CPT,outpatient,100,50,,40,percent of total billed charges,61.5\n")
    prof, it = parse_file(str(p), "999999")
    rows = list(it)
    assert prof.format == "CMS CSV wide"
    assert prof.attestation_statement == "missing"
    assert {(r["code"], r["price_type"]) for r in rows} >= {("73721", "negotiated_dollar"), ("80053", "allowed_median")}
    assert prof.pct_algo_with_median == 1 and prof.pct_algo_total == 1


def test_non_template_csv_is_not_parsed(tmp_path):
    # Layout of The CORE Institute file (2026-09): its own columns, not the CMS template.
    p = tmp_path / "core.csv"
    p.write_text("ITEMNUM,DESCRIPTION,REVCODE,SERVICEID,MOD1,MODNAME1,AMOUNT\r121,IP SURGERY SEMI PRVT,121,,,,1587\r")
    prof, rows = parse_file(str(p), "030108")
    assert prof.format == "non-standard" and list(rows) == []
