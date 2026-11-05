"""
Step 1: look at the data before touching any model.

Usage:
    python step1_inspect_data.py data.csv
    python step1_inspect_data.py data.csv --date month --area district --cases cases

Only the path is required. The other flags unlock the deeper checks.
"""
import argparse
import sys

import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", help="CSV file to inspect")
    p.add_argument("--date", help="name of the date/month column")
    p.add_argument("--area", help="name of the district/province column")
    p.add_argument("--cases", help="name of the cholera case count column")
    args = p.parse_args()

    df = pd.read_csv(args.path)

    print("\n=== SHAPE ===")
    print(f"{df.shape[0]} rows, {df.shape[1]} columns")

    print("\n=== COLUMNS ===")
    info = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    })
    print(info.to_string())

    print("\n=== FIRST 5 ROWS ===")
    print(df.head().to_string())

    if args.date:
        d = pd.to_datetime(df[args.date], errors="coerce")
        bad = d.isna().sum()
        print("\n=== DATE RANGE ===")
        print(f"{d.min()} to {d.max()}  (unparseable dates: {bad})")

    if args.area:
        print("\n=== AREAS ===")
        print(f"{df[args.area].nunique()} distinct values in '{args.area}'")
        print(df[args.area].value_counts().head(10).to_string())

    if args.area and args.date:
        d = pd.to_datetime(df[args.date], errors="coerce")
        dupes = df.assign(_d=d).duplicated([args.area, "_d"]).sum()
        print(f"\nDuplicate area+date rows: {dupes}")

    if args.cases:
        c = pd.to_numeric(df[args.cases], errors="coerce")
        print("\n=== CASES ===")
        print(c.describe().to_string())
        print(f"\nRows with zero cases: {(c == 0).sum()} ({(c == 0).mean() * 100:.1f}%)")
        print(f"Rows with 1+ cases:  {(c > 0).sum()} ({(c > 0).mean() * 100:.1f}%)")
        print("\nIf that second number is small, you have a class imbalance problem.")


if __name__ == "__main__":
    sys.exit(main())
