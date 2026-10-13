"""Inter-rater agreement for the payer dictionary: percent agreement, Cohen's kappa, list of disagreements.

Usage: python research/h2/irr_score.py [rater_A.csv rater_B.csv]
Target (proposal Table 9): 85% agreement or higher on canonical_payer.
"""
import csv
import sys
from collections import Counter


def load(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main() -> None:
    pa, pb = (sys.argv[1:3] if len(sys.argv) >= 3 else
              ("research/h2/irr_rater_A.csv", "research/h2/irr_rater_B.csv"))
    A, B = load(pa), load(pb)
    assert [(r["raw_payer"], r["raw_plan"]) for r in A] == [(r["raw_payer"], r["raw_plan"]) for r in B], \
        "the two files must list the same strings in the same order"
    empty = [i for i, (x, y) in enumerate(zip(A, B, strict=True))
             if not x["canonical_payer"].strip() or not y["canonical_payer"].strip()]
    if empty:
        sys.exit(f"{len(empty)} rows are not labelled yet (first: row {empty[0] + 2})")
    for field in ("canonical_payer", "plan_type"):
        a = [r[field].strip().casefold() for r in A]
        b = [r[field].strip().casefold() for r in B]
        agree = sum(x == y for x, y in zip(a, b, strict=True))
        print(f"{field}: {agree}/{len(a)} = {agree / len(a):.1%} agreement, Cohen's kappa = {kappa(a, b):.3f}")
    print("target: 85% agreement on canonical_payer")
    print("\nDisagreements (canonical_payer or plan_type):")
    for x, y in zip(A, B, strict=True):
        if (x["canonical_payer"].strip().casefold() != y["canonical_payer"].strip().casefold()
                or x["plan_type"].strip().casefold() != y["plan_type"].strip().casefold()):
            print(f"- {x['raw_payer']} | {x['raw_plan']}: A={x['canonical_payer']}/{x['plan_type']}  "
                  f"B={y['canonical_payer']}/{y['plan_type']}")


if __name__ == "__main__":
    main()
