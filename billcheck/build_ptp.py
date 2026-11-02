"""Build data/raw/reference/ncci_ptp.sqlite from the hand-downloaded CMS PTP zips (see billcheck/reference.py).

Usage: python -m billcheck.build_ptp [--active-on 20261001]
"""
import argparse

from billcheck.reference import build_ptp

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--active-on", default="20261001")
    for table, n in build_ptp(ap.parse_args().active_on).items():
        print(f"{table}: {n:,} active pairs")
