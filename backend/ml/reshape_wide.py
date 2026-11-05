"""
Step 1b: your file has one column per year (y2008 ... y2018). The models need one
row per district per year. This converts it.

    python -m ml.reshape_wide
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def main():
    wide = pd.read_csv(cfg.RAW_WIDE_FILE)
    year_cols = [c for c in wide.columns if re.fullmatch(cfg.WIDE_YEAR_REGEX, c)]
    if not year_cols:
        raise SystemExit(f"No year columns matching {cfg.WIDE_YEAR_REGEX} in {cfg.RAW_WIDE_FILE.name}")
    id_cols = [c for c in wide.columns if c not in year_cols]
    long = wide.melt(id_vars=id_cols, value_vars=year_cols, var_name="_y", value_name=cfg.CASES_COL)
    long[cfg.DATE_COL] = pd.to_datetime(long["_y"].str.extract(r"(\d{4})")[0] + "-01-01")
    long = long.drop(columns="_y").sort_values([cfg.AREA_COL, cfg.DATE_COL])
    long.to_csv(cfg.DATA_FILE, index=False)
    print(f"{len(wide)} districts x {len(year_cols)} years -> {len(long)} rows")
    print(f"Saved {cfg.DATA_FILE}")


if __name__ == "__main__":
    main()
