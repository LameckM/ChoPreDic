"""
FAKE data, only for testing that the pipeline runs end to end.
Never use results from this file in your report.

    python tools/make_synthetic_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(1)
out = Path(__file__).resolve().parents[1] / "data" / "raw" / "synthetic_cholera.csv"

districts = {"Lusaka": 0.9, "Kapiri": 0.5, "Nakonde": 0.7, "Mansa": 0.3, "Kasama": 0.4, "Chipata": 0.2}
months = pd.date_range("2015-01-01", "2024-12-01", freq="MS")
rows = []
for d, risk in districts.items():
    pop = rng.integers(20, 400)
    water = rng.uniform(40, 90)
    prev = 0
    for m in months:
        wet = 1 if m.month in (11, 12, 1, 2, 3, 4) else 0
        rain = rng.gamma(4, 40) * (2.5 if wet else 0.3)
        lam = max(0, risk * wet * (rain / 400) * 3 + 0.5 * prev - 0.8)
        cases = int(rng.poisson(lam)) if rng.random() < 0.6 or prev > 0 else 0
        prev = cases
        rows.append((d, m.strftime("%Y-%m-%d"), cases, round(rain, 1), pop, round(water, 1)))

pd.DataFrame(rows, columns=["district", "month", "cases", "rainfall_mm",
                            "population_density", "safe_water_pct"]).to_csv(out, index=False)
print("Wrote", out)
