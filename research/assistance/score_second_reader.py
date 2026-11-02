"""Score the second reader of the financial assistance policies (research/assistance/second_reader.xlsx).

Usage: python -m research.assistance.score_second_reader [path]
Prints agreement overall and per system, and lists every disagreement for the two readers to resolve together.
The dictionary rule applies here too: values are not changed by anyone except through that joint review.
"""
import sys
from collections import defaultdict

from openpyxl import load_workbook

path = sys.argv[1] if len(sys.argv) > 1 else "research/assistance/second_reader.xlsx"
ws = load_workbook(path, data_only=True)["Check"]
head = [c.value for c in ws[3]]
rows = [dict(zip(head, (c.value for c in r), strict=False)) for r in ws.iter_rows(min_row=4) if r[0].value]
answer = lambda r: str(r["Agrees?"] or "").strip().lower()  # noqa: E731
done = [r for r in rows if answer(r) in ("yes", "no")]
agree = [r for r in done if answer(r) == "yes"]
print(f"checked {len(done)} of {len(rows)} items; agreement {len(agree)}/{len(done)}"
      + (f" = {100 * len(agree) / len(done):.1f}%" if done else ""))
per = defaultdict(lambda: [0, 0])
for r in done:
    per[r["Health system"]][0] += answer(r) == "yes"
    per[r["Health system"]][1] += 1
for s, (a, n) in sorted(per.items()):
    print(f"  {s}: {a}/{n}")
for r in done:
    if answer(r) == "no":
        print(f"DISAGREE #{r['#']} {r['Health system']} / {r['What to check']}: ours '{r['Our value']}' vs "
              f"'{r['Correct value (if No)']}' ({r['Page or quote where you found it']})")
