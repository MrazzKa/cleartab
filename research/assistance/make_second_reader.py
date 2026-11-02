"""Build the second reader's workbook for the financial assistance policies.

Usage: python -m research.assistance.make_second_reader   -> research/assistance/second_reader.xlsx
One row per value in data/processed/assistance_policies.json, grouped by health system, with a link to the
hospital's own document, a Yes/No drop-down and columns for the reader's answer. Scored by
`python -m research.assistance.score_second_reader`.
"""
import json
import pathlib

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from pipeline.common import PROCESSED

OUT = pathlib.Path(__file__).with_name("second_reader.xlsx")
LABELS = {
    "effective": "Date the policy takes effect",
    "covers": "Who and what the policy covers",
    "above_max": "What happens above the top income band",
    "insured_eligible": "Can insured patients apply (for what insurance did not pay)?",
    "assets_test": "Are savings or other assets counted?",
    "window": "Deadline to apply / time window",
    "max_charge": "Most a qualifying patient can be charged",
    "phone": "Phone number for financial assistance",
}
HEAD = ["#", "Health system", "What to check", "Our value", "Document", "Agrees?", "Correct value (if No)",
        "Page or quote where you found it", "Note"]
WIDTHS = [6, 22, 34, 46, 16, 11, 34, 34, 28]
TEAL, PALE, GREY = "0F6B74", "EAF3F2", "F5F7F7"


def show(v) -> str:
    if v is True:
        return "Yes"
    if v is False:
        return "No"
    if v is None:
        return "not published"
    return str(v)


def band(lo: float, hi: float) -> str:
    """Plain wording of a band stored as numbers: 199.99 means 'below 200', 300.01 means 'above 300'."""
    top = f"below {round(hi):g}%" if hi % 1 else f"up to {hi:g}%"
    if lo == 0:
        return f"{top} of the federal poverty level"
    bottom = f"above {round(lo):g}%" if lo % 1 else f"from {lo:g}%"
    return f"{bottom} {top.replace('up to', 'up to and including')} of the federal poverty level"


def rows(d: dict) -> list[list]:
    out = []
    for s in d["systems"]:
        sysname = s["system"]
        for i, t in enumerate(s["tiers"], 1):
            out.append([sysname, f"Band {i}: household income range", band(t.get("min_fpl", 0), t["max_fpl"]),
                        s["source_url"]])
            out.append([sysname, f"Band {i}: result for an uninsured patient", t["uninsured"], s["source_url"]])
            out.append([sysname, f"Band {i}: result for an insured patient", t["insured"], s["source_url"]])
        if not s["tiers"]:
            out.append([sysname, "Income bands", "Not published (search the hospital website)", s["page_url"]])
        for f, label in LABELS.items():
            out.append([sysname, label, show(s.get(f)), s["source_url"]])
    g = d["poverty_guidelines"]
    out.append(["HHS poverty guidelines 2026", "Amount for a household of 1", f"${g['base']:,}", g["source_url"]])
    out.append(["HHS poverty guidelines 2026", "Added for each extra person", f"${g['per_additional_person']:,}",
                g["source_url"]])
    return out


def main() -> None:
    d = json.loads((PROCESSED / "assistance_policies.json").read_text())
    wb = Workbook()
    thin = Side(style="thin", color="D5DFDE")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    how = wb.active
    how.title = "How to"
    text = [
        ("Second reader: hospital financial assistance policies", True),
        ("Why: ClearTab tells people whether a hospital will give them free or discounted care. One person read "
         "these values from the hospitals' documents. Before anyone relies on them, a second person checks each one "
         "independently (the same rule as the payer dictionary).", False),
        ("", False),
        ("Steps", True),
        ("1. Go to the sheet 'Check'. Each row is one value.", False),
        ("2. Click 'Open document' in that row. It opens the hospital's own policy (PDF or web page).", False),
        ("3. Find the value in the document yourself. Compare it with 'Our value'.", False),
        ("4. In 'Agrees?' choose Yes or No from the drop-down.", False),
        ("5. If No: write what the document really says in 'Correct value'.", False),
        ("6. Always write the page number or a short quote in 'Page or quote', for Yes and for No.", False),
        ("7. Use 'Note' for anything unclear: the document contradicts itself, the link is broken, and so on.", False),
        ("", False),
        ("Watch out for", True),
        ("- Band edges: 'below 200%' and 'up to 200%' are different. A family exactly at 200% is in a different band.",
         False),
        ("- 'Not published' rows: search the hospital's website. If you find the income limits, choose No and add the "
         "link in 'Correct value'.", False),
        ("- Only the hospital's own documents count. Do not use summary sites (careroute.ai, healthbillcentral.com).",
         False),
        ("- Do not change the policy file yourself. Disagreements are resolved together, with the document open.",
         False),
        ("", False),
        ("When done: save this file with the same name and send it back. Progress is counted at the top of 'Check'.",
         False),
    ]
    for i, (t, bold) in enumerate(text, 1):
        c = how.cell(row=i, column=1, value=t)
        c.alignment = wrap
        c.font = Font(bold=bold, size=14 if i == 1 else 11, color=TEAL if bold else "14232B")
    how.column_dimensions["A"].width = 110

    ws = wb.create_sheet("Check")
    data = rows(d)
    ws["A1"] = "Done:"
    ws["A1"].font = Font(bold=True)
    ws["B1"] = f'=COUNTA(F4:F{3 + len(data)})&" of {len(data)}"'
    ws["C1"] = "Disagreements:"
    ws["C1"].font = Font(bold=True)
    ws["D1"] = f'=COUNTIF(F4:F{3 + len(data)},"No")'
    for j, h in enumerate(HEAD, 1):
        c = ws.cell(row=3, column=j, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=TEAL)
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = border
        ws.column_dimensions[c.column_letter].width = WIDTHS[j - 1]
    shade, last = False, None
    for i, (system, what, value, url) in enumerate(data, 1):
        r = 3 + i
        if system != last:
            shade, last = not shade, system
        vals = [i, system, what, value, "Open document", None, None, None, None]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=v)
            c.alignment = wrap
            c.border = border
            if shade:
                c.fill = PatternFill("solid", fgColor=PALE)
        link = ws.cell(row=r, column=5)
        link.hyperlink = url
        link.font = Font(color="0563C1", underline="single")
        ws.cell(row=r, column=2).font = Font(bold=True)
        for j in (6, 7, 8, 9):
            ws.cell(row=r, column=j).fill = PatternFill("solid", fgColor="FFFFFF")
    end = 3 + len(data)
    dv = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True, showDropDown=False)
    dv.error, dv.errorTitle = "Choose Yes or No", "Agrees?"
    ws.add_data_validation(dv)
    dv.add(f"F4:F{end}")
    ws.conditional_formatting.add(f"F4:F{end}", CellIsRule(operator="equal", formula=['"Yes"'],
                                                            fill=PatternFill("solid", fgColor="D9F2E3")))
    ws.conditional_formatting.add(f"F4:F{end}", CellIsRule(operator="equal", formula=['"No"'],
                                                            fill=PatternFill("solid", fgColor="FBDADA")))
    ws.conditional_formatting.add(f"G4:G{end}", FormulaRule(formula=['AND($F4="No",$G4="")'],
                                                             fill=PatternFill("solid", fgColor="FFF2CC")))
    ws.freeze_panes = "D4"
    ws.auto_filter.ref = f"A3:I{end}"
    ws.row_dimensions[3].height = 32

    src = wb.create_sheet("Sources")
    for j, h in enumerate(["Health system", "Policy", "Effective", "Main document", "Web page"], 1):
        c = src.cell(row=1, column=j, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=TEAL)
    for i, s in enumerate(d["systems"], 2):
        src.cell(row=i, column=1, value=s["system"]).font = Font(bold=True)
        src.cell(row=i, column=2, value=s["policy"]).alignment = wrap
        src.cell(row=i, column=3, value=s["effective"])
        for col, key in ((4, "source_url"), (5, "page_url")):
            c = src.cell(row=i, column=col, value="Open")
            c.hyperlink = s[key]
            c.font = Font(color="0563C1", underline="single")
    for col, w in zip("ABCDE", (28, 60, 22, 12, 12), strict=True):
        src.column_dimensions[col].width = w
    wb.active = 1
    wb.save(OUT)
    print(OUT, len(data), "rows")


if __name__ == "__main__":
    main()
