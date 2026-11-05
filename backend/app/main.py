import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402
from ml.prepare import step  # noqa: E402

app = FastAPI(
    title="Cholera Early-Warning API (Zambia)",
    version="0.1.0"
)

# Extra dashboard origins (for example a phone on the same Wi-Fi) are set with an
# environment variable instead of being hardcoded:
#   CORS_EXTRA_ORIGINS=http://192.168.1.20:5173 uvicorn app.main:app --reload
EXTRA_ORIGINS = [o.strip() for o in os.environ.get("CORS_EXTRA_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *EXTRA_ORIGINS,
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

AREA, DATE, CASES = cfg.AREA_COL, cfg.DATE_COL, cfg.CASES_COL
ORDER = {"low": 0, "medium": 1, "high": 2}


def _load():
    needed = [cfg.MODEL_DIR / "best_model.joblib", cfg.MODEL_DIR / "metrics.json",
              cfg.PROCESSED_DIR / "predict_table.csv", cfg.DATA_FILE]
    missing = [p.name for p in needed if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing {missing}. Run: python -m ml.reshape_wide, "
                           "python -m ml.prepare, python -m ml.train")
    bundle = joblib.load(cfg.MODEL_DIR / "best_model.joblib")
    metrics = json.loads((cfg.MODEL_DIR / "metrics.json").read_text())
    long = pd.read_csv(cfg.DATA_FILE, parse_dates=[DATE])
    latest = pd.read_csv(cfg.PROCESSED_DIR / "predict_table.csv", parse_dates=[DATE])
    latest["risk"] = bundle["pipeline"].predict_proba(latest[bundle["features"]])[:, 1]
    return bundle, metrics, long, latest


BUNDLE, METRICS, LONG, LATEST = _load()
BASED_ON = LATEST[DATE].max()
FORECAST_PERIOD = BASED_ON + step(cfg.HORIZON)
YEAR = lambda ts: int(ts.year)  # noqa: E731
STATIC_COLS = [c for c in ["Dist_ID", "pop2010", "urban(%)", "water(%)", "sanitation(%)",
                           "poverty(%)", "Dist_Waterbody (km)"] if c in LONG.columns]


def level(risk: float) -> str:
    if risk >= cfg.RISK_HIGH:
        return "high"
    return "medium" if risk >= cfg.RISK_MEDIUM else "low"


def clean(v):
    """Make numpy/pandas values JSON friendly."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else round(float(v), 4)
    return v


def risk_rows() -> list:
    last_cases = LONG[LONG[DATE] == BASED_ON].set_index(AREA)[CASES]
    rows = []
    for _, r in LATEST.sort_values("risk", ascending=False).iterrows():
        rows.append({
            "district": r[AREA],
            "risk": round(float(r["risk"]), 3),
            "level": level(r["risk"]),
            "cases_latest": clean(last_cases.get(r[AREA])),
        })
    return rows


@app.get("/health")
def health():
    return {"status": "ok", "model": BUNDLE["name"]}


@app.get("/api/risk")
def risk():
    """Risk score for every district for the forecast period, highest first."""
    rows = risk_rows()
    return {
        "based_on_year": YEAR(BASED_ON),
        "forecast_year": YEAR(FORECAST_PERIOD),
        "model": BUNDLE["name"],
        "thresholds": {"medium": cfg.RISK_MEDIUM, "high": cfg.RISK_HIGH},
        "note": "Scores rank districts by relative risk. They are not calibrated probabilities.",
        "districts": rows,
    }


@app.get("/api/alerts")
def alerts(min_level: str = Query("high", pattern="^(medium|high)$")):
    """Districts at or above the chosen alert level."""
    rows = [r for r in risk_rows() if ORDER[r["level"]] >= ORDER[min_level]]
    return {"forecast_year": YEAR(FORECAST_PERIOD), "min_level": min_level,
            "count": len(rows), "alerts": rows}


@app.get("/api/summary")
def summary():
    """Headline numbers for the top of the dashboard."""
    rows = risk_rows()
    counts = {lv: sum(r["level"] == lv for r in rows) for lv in ORDER}
    return {"forecast_year": YEAR(FORECAST_PERIOD), "districts": len(rows),
            "levels": counts, "top5": rows[:5], "model": BUNDLE["name"]}


@app.get("/api/districts")
def districts():
    static = LONG.drop_duplicates(AREA)[[AREA] + STATIC_COLS].sort_values(AREA)
    out = []
    for rec in static.to_dict("records"):
        item = {"district": rec.pop(AREA)}
        item.update({k: clean(v) for k, v in rec.items()})
        out.append(item)
    return out


@app.get("/api/districts/{name}")
def district_detail(name: str):
    g = LONG[LONG[AREA].str.lower() == name.lower()].sort_values(DATE)
    if g.empty:
        raise HTTPException(404, f"District '{name}' not found")
    real = g[AREA].iloc[0]
    me = next(r for r in risk_rows() if r["district"] == real)
    static = {c: clean(g[c].iloc[0]) for c in STATIC_COLS}
    history = [{"year": YEAR(d), "cases": clean(c)} for d, c in zip(g[DATE], g[CASES])]
    return {"district": real, "forecast_year": YEAR(FORECAST_PERIOD),
            "risk": me["risk"], "level": me["level"], "static": static, "history": history}


@app.get("/api/trends/national")
def national_trend():
    """National totals per year, for the trend chart."""
    t = LONG.groupby(DATE).agg(cases=(CASES, "sum"),
                               districts_affected=(CASES, lambda s: int((s > 0).sum())))
    return [{"year": YEAR(d), "cases": int(r["cases"]), "districts_affected": int(r["districts_affected"])}
            for d, r in t.iterrows()]


@app.get("/api/model")
def model_info():
    """Model comparison table and feature importance, for the methodology panel."""
    return METRICS
