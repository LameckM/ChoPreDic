"""
Step 2: turn the long table into a model-ready table.

    python -m ml.prepare
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

TARGET = "target"


def step(n: int) -> pd.DateOffset:
    """n periods as a date offset (years or months depending on config.FREQ)."""
    return pd.DateOffset(years=n) if cfg.FREQ == "Y" else pd.DateOffset(months=n)


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    needed = [cfg.DATE_COL, cfg.AREA_COL, cfg.CASES_COL] + list(cfg.COVARIATES)
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise SystemExit(f"Columns not found in {path.name}: {missing}\n"
                         f"Columns in the file: {list(df.columns)}\nFix the names in config.py.")
    df = df[needed].copy()
    df[cfg.DATE_COL] = pd.to_datetime(df[cfg.DATE_COL], errors="coerce").dt.to_period(cfg.PERIOD).dt.to_timestamp()
    bad = df[cfg.DATE_COL].isna().sum()
    if bad:
        print(f"Dropping {bad} rows with unreadable dates")
        df = df.dropna(subset=[cfg.DATE_COL])
    df[cfg.CASES_COL] = pd.to_numeric(df[cfg.CASES_COL], errors="coerce")
    dupes = df.duplicated([cfg.AREA_COL, cfg.DATE_COL]).sum()
    if dupes:
        raise SystemExit(f"{dupes} duplicate area+period rows. Aggregate them first and re-run.")
    return df


def complete_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Give every area every period so shifting by one row always means one period."""
    parts = []
    for area, g in df.groupby(cfg.AREA_COL):
        g = g.set_index(cfg.DATE_COL).sort_index().asfreq(cfg.PANDAS_FREQ)
        g[cfg.AREA_COL] = area
        parts.append(g.reset_index())
    out = pd.concat(parts, ignore_index=True)
    # Static covariates stay constant for an area, so fill any gap created above.
    out[list(cfg.COVARIATES)] = out.groupby(cfg.AREA_COL)[list(cfg.COVARIATES)].transform(lambda s: s.ffill().bfill())
    if cfg.FILL_MISSING_CASES_WITH_ZERO:
        out[cfg.CASES_COL] = out[cfg.CASES_COL].fillna(0)
    return out


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for _, g in df.groupby(cfg.AREA_COL):
        g = g.sort_values(cfg.DATE_COL).copy()
        c = g[cfg.CASES_COL]
        # Case counts are heavy-tailed (Lusaka has thousands, most districts have 0),
        # so features use log(1 + cases).
        g["cases_now"] = np.log1p(c)
        for lag in cfg.LAGS:
            g[f"cases_lag{lag}"] = np.log1p(c.shift(lag))
        g["cases_roll3"] = np.log1p(c.rolling(3).sum())
        g["outbreak_periods_so_far"] = (c > 0).cumsum()      # history up to now only
        future = c.shift(-cfg.HORIZON)                        # used ONLY for the label
        g[TARGET] = np.where(future.isna(), np.nan, (future > cfg.OUTBREAK_THRESHOLD).astype(float))
        parts.append(g)
    out = pd.concat(parts, ignore_index=True)

    # How widespread is cholera nationally in this period? Known at row time, no leakage.
    out["national_active_areas"] = out.groupby(cfg.DATE_COL)[cfg.CASES_COL].transform(lambda s: (s > 0).sum())

    if cfg.FREQ == "M":
        month = out[cfg.DATE_COL].dt.month
        out["month_sin"] = np.sin(2 * np.pi * month / 12)
        out["month_cos"] = np.cos(2 * np.pi * month / 12)
    for col in cfg.LOG_COVARIATES:
        out[col] = np.log1p(out[col])
    return out


def feature_columns() -> list:
    cols = (["cases_now"] + [f"cases_lag{l}" for l in cfg.LAGS]
            + ["cases_roll3", "outbreak_periods_so_far", "national_active_areas"])
    if cfg.FREQ == "M":
        cols += ["month_sin", "month_cos"]
    return cols + list(cfg.COVARIATES)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=cfg.DATA_FILE)
    p.add_argument("--output", type=Path, default=cfg.PROCESSED_DIR / "model_table.csv")
    args = p.parse_args()

    df = load_raw(args.input)
    print(f"Loaded {len(df)} rows, {df[cfg.AREA_COL].nunique()} areas, "
          f"{df[cfg.DATE_COL].min():%Y} to {df[cfg.DATE_COL].max():%Y}")
    df = build_features(complete_calendar(df))

    history = ["cases_now", "cases_roll3"] + [f"cases_lag{l}" for l in cfg.LAGS]

    # The newest period has no label yet (its future has not happened). Those rows are
    # exactly what the live system predicts from, so save them separately.
    latest = df[df[cfg.DATE_COL] == df[cfg.DATE_COL].max()].dropna(subset=history)
    latest = latest[[cfg.AREA_COL, cfg.DATE_COL] + feature_columns()]
    latest.to_csv(args.output.with_name("predict_table.csv"), index=False)
    print(f"Saved {len(latest)} rows for live prediction (period {df[cfg.DATE_COL].max():%Y})")

    before = len(df)
    df = df.dropna(subset=[TARGET] + history)
    print(f"Kept {len(df)} of {before} rows (dropped rows without history or without a label)")

    df = df[[cfg.AREA_COL, cfg.DATE_COL] + feature_columns() + [TARGET]]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print("\nOutbreak rate by feature period:")
    print((df.groupby(df[cfg.DATE_COL].dt.year)[TARGET].agg(["sum", "count", "mean"])
             .rename(columns={"sum": "outbreaks", "count": "rows", "mean": "rate"}).round(2)).to_string())
    print(f"\nSaved {args.output}")


if __name__ == "__main__":
    main()
