"""
Step 3: compare Logistic Regression and Random Forest with a rolling-origin test,
then fit the winner on all data and save it.

    python -m ml.train
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402
from ml.prepare import TARGET, feature_columns, step  # noqa: E402


def metrics(y, score, pred) -> dict:
    return {
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }


def make_models() -> dict:
    return {
        "logistic_regression": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", C=0.5, max_iter=2000,
                                         random_state=cfg.RANDOM_STATE)),
        ]),
        "random_forest": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(n_estimators=400, min_samples_leaf=3,
                                             class_weight="balanced_subsample", n_jobs=-1,
                                             random_state=cfg.RANDOM_STATE)),
        ]),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=cfg.PROCESSED_DIR / "model_table.csv")
    args = p.parse_args()

    df = pd.read_csv(args.input, parse_dates=[cfg.DATE_COL])
    feats = feature_columns()
    dates = sorted(df[cfg.DATE_COL].unique())
    test_dates = [pd.Timestamp(d) for d in dates[-cfg.N_TEST_PERIODS:]]
    models = make_models()

    # Rolling origin: for each test period, train only on rows whose label was
    # already known BEFORE that period began, then predict that period.
    preds = {n: [] for n in models}
    truth, baseline, used = [], [], []
    for d in test_dates:
        train = df[df[cfg.DATE_COL] + step(cfg.HORIZON) <= d]
        test = df[df[cfg.DATE_COL] == d]
        if train[cfg.DATE_COL].nunique() < cfg.MIN_TRAIN_PERIODS or train[TARGET].nunique() < 2:
            continue
        used.append(d)
        truth.append(test[TARGET].astype(int).values)
        baseline.append((test["cases_now"] > np.log1p(cfg.OUTBREAK_THRESHOLD)).astype(int).values)
        for name, pipe in models.items():
            m = clone(pipe).fit(train[feats], train[TARGET].astype(int))
            preds[name].append(m.predict_proba(test[feats])[:, 1])

    if not used:
        raise SystemExit("Not enough history for the rolling test. Lower MIN_TRAIN_PERIODS or N_TEST_PERIODS.")
    y = np.concatenate(truth)
    print(f"Rolling test over {len(used)} periods: "
          f"{', '.join(str(d.year if cfg.FREQ == 'Y' else d.strftime('%Y-%m')) for d in used)}")
    print(f"{len(y)} test predictions, {y.sum()} actual outbreaks ({y.mean():.1%})\n")

    results = {"baseline_persistence": metrics(y, np.concatenate(baseline), np.concatenate(baseline))}
    for name in models:
        s = np.concatenate(preds[name])
        results[name] = metrics(y, s, (s >= 0.5).astype(int))
    print(pd.DataFrame(results).T.round(3).to_string(), "\n")

    winner = max(models, key=lambda n: results[n]["pr_auc"])
    print(f"Selected model: {winner}")
    if results[winner]["pr_auc"] <= results["baseline_persistence"]["pr_auc"]:
        print("WARNING: the winner does not beat the 'same as this period' baseline.")

    final = clone(models[winner]).fit(df[feats], df[TARGET].astype(int))
    inner = final.named_steps["model"]
    imp = inner.feature_importances_ if hasattr(inner, "feature_importances_") else np.abs(inner.coef_[0])
    importance = dict(sorted(zip(feats, map(float, imp)), key=lambda kv: -kv[1]))

    cfg.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": final, "features": feats, "name": winner,
                 "horizon": cfg.HORIZON, "threshold": cfg.OUTBREAK_THRESHOLD},
                cfg.MODEL_DIR / "best_model.joblib")
    (cfg.MODEL_DIR / "metrics.json").write_text(json.dumps(
        {"selected": winner, "test_periods": [str(d.date()) for d in used],
         "results": results, "feature_importance": importance}, indent=2))
    print("Top features:", ", ".join(list(importance)[:6]))
    print(f"Saved model and metrics to {cfg.MODEL_DIR}")


if __name__ == "__main__":
    main()
