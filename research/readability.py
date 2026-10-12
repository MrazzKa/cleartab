"""Flesch-Kincaid grade level with a simple vowel-group syllable counter (approximate, no dictionary).

Usage: python research/readability.py "text"  or  python research/readability.py --procedures
"""
import csv
import re
import sys


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def fk_grade(text: str) -> float:
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[A-Za-z']+", text)
    syl = sum(syllables(w) for w in words)
    return 0.39 * len(words) / sentences + 11.8 * syl / len(words) - 15.59


if __name__ == "__main__":
    if sys.argv[1:] == ["--procedures"]:
        with open("data/processed/procedure_text.csv", newline="") as f:
            g = [fk_grade(r["description"]) for r in csv.DictReader(f)]
        print(f"descriptions: n={len(g)} mean grade {sum(g) / len(g):.1f}, max {max(g):.1f}, "
              f"over 8: {sum(x > 8 for x in g)}")
    else:
        t = " ".join(sys.argv[1:])
        print(f"{len(t.split())} words, Flesch-Kincaid grade {fk_grade(t):.1f}")
