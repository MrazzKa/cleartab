"""Score the second reader of the financial assistance policies (research/assistance/second_reader.csv).

Usage: python -m research.assistance.score_second_reader [path]
Prints agreement overall and per system, and lists every disagreement for the two readers to resolve together.
The dictionary rule applies here too: values are not changed by anyone except through that joint review.
"""
import csv
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else "research/assistance/second_reader.csv"
with open(path, newline="") as f:
    rows = list(csv.DictReader(f))
done = [r for r in rows if r["second_reader_agrees (Y/N)"].strip().upper() in ("Y", "N")]
agree = [r for r in done if r["second_reader_agrees (Y/N)"].strip().upper() == "Y"]
print(f"checked {len(done)} of {len(rows)} items; agreement {len(agree)}/{len(done)}"
      + (f" = {100 * len(agree) / len(done):.1f}%" if done else ""))
per = defaultdict(lambda: [0, 0])
for r in done:
    per[r["system"]][0] += r["second_reader_agrees (Y/N)"].strip().upper() == "Y"
    per[r["system"]][1] += 1
for s, (a, n) in sorted(per.items()):
    print(f"  {s}: {a}/{n}")
for r in done:
    if r["second_reader_agrees (Y/N)"].strip().upper() == "N":
        print(f"DISAGREE #{r['item']} {r['system']} / {r['field']}: first '{r['first_reader_value']}' vs second "
              f"'{r['second_reader_value_if_different']}' ({r['page_or_quote']})")
