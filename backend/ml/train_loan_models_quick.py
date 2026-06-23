"""
Quick Loan Model Training Script
=================================
Generates synthetic MSME loan approval data and trains 4 XGBoost classifiers
(PSU Bank, Private Bank, NBFC, MFI) in under 60 seconds.

Run with:
    python -m backend.ml.train_loan_models_quick

No external data files needed - all data is generated synthetically with
realistic Indian MSME lending criteria.
"""

import numpy as np
import pandas as pd
import pickle
import logging
from pathlib import Path

import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = Path("backend/data/loan_models")

FEATURE_COLS = [
    "cibil_score",
    "debt_to_income_ratio",
    "business_vintage_years",
    "client_concentration_pct",
    "revenue_stability",
    "cash_flow_coverage",
    "gst_compliance_score",
    "monthly_revenue_inr",
    "outstanding_loans_inr",
]

# Approval criteria per lender (stricter → more requirements)
LENDER_CRITERIA = {
    "psu": {
        "cibil_min": 700, "dti_max": 0.5, "vintage_min": 3,
        "gst_min": 70, "cfcov_min": 1.2, "revenue_min": 200_000,
    },
    "private": {
        "cibil_min": 680, "dti_max": 0.6, "vintage_min": 2,
        "gst_min": 60, "cfcov_min": 1.1, "revenue_min": 150_000,
    },
    "nbfc": {
        "cibil_min": 620, "dti_max": 0.8, "vintage_min": 1,
        "gst_min": 50, "cfcov_min": 0.9, "revenue_min": 75_000,
    },
    "mfi": {
        "cibil_min": 550, "dti_max": 1.0, "vintage_min": 0.5,
        "gst_min": 30, "cfcov_min": 0.7, "revenue_min": 25_000,
    },
}


def generate_synthetic_data(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Generate realistic MSME loan applicant data."""
    rng = np.random.default_rng(seed)

    df = pd.DataFrame({
        "cibil_score": rng.normal(670, 80, n).clip(300, 900),
        "debt_to_income_ratio": rng.lognormal(-0.5, 0.6, n).clip(0, 3.0),
        "business_vintage_years": rng.exponential(4, n).clip(0.1, 30),
        "client_concentration_pct": rng.beta(2, 3, n) * 100,
        "revenue_stability": rng.lognormal(-0.8, 0.7, n).clip(0.05, 3.0),  # lower = stable
        "cash_flow_coverage": rng.lognormal(0.2, 0.5, n).clip(0.1, 6.0),
        "gst_compliance_score": rng.beta(4, 2, n) * 100,
        "monthly_revenue_inr": rng.lognormal(12, 1.2, n).clip(10_000, 20_000_000),
        "outstanding_loans_inr": rng.lognormal(10, 1.5, n).clip(0, 10_000_000),
    })

    # Create labels for each lender using realistic approval rules + noise
    for lender, crit in LENDER_CRITERIA.items():
        score = (
            (df["cibil_score"] >= crit["cibil_min"]).astype(float) * 2.5
            + (df["debt_to_income_ratio"] <= crit["dti_max"]).astype(float) * 2.0
            + (df["business_vintage_years"] >= crit["vintage_min"]).astype(float) * 1.5
            + (df["gst_compliance_score"] >= crit["gst_min"]).astype(float) * 1.5
            + (df["cash_flow_coverage"] >= crit["cfcov_min"]).astype(float) * 2.0
            + (df["monthly_revenue_inr"] >= crit["revenue_min"]).astype(float) * 1.0
            + (df["client_concentration_pct"] <= 50).astype(float) * 0.5
        )
        # Add gaussian noise + use sigmoid threshold
        noise = rng.normal(0, 1.0, n)
        prob = 1 / (1 + np.exp(-(score - 5.5 + noise)))
        df[f"{lender}_approved"] = (prob > 0.5).astype(int)

    logger.info("Generated %d synthetic samples", n)
    for lender in LENDER_CRITERIA:
        approved = df[f"{lender}_approved"].mean()
        logger.info("  %s approval rate: %.1f%%", lender, approved * 100)

    return df


def train_and_save_all():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_data(n=4000)

    # 70/15/15 split
    n = len(df)
    idx = np.random.default_rng(42).permutation(n)
    train_df = df.iloc[idx[:int(n * 0.7)]]
    val_df   = df.iloc[idx[int(n * 0.7):int(n * 0.85)]]
    test_df  = df.iloc[idx[int(n * 0.85):]]

    X_train = train_df[FEATURE_COLS].values.astype(np.float32)
    X_val   = val_df[FEATURE_COLS].values.astype(np.float32)

    for lender in LENDER_CRITERIA:
        logger.info("Training %s model...", lender.upper())

        y_train = train_df[f"{lender}_approved"].values
        y_val   = val_df[f"{lender}_approved"].values

        # Fast XGBoost — no Optuna, sensible defaults
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
            eval_metric="logloss",
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Probability calibration
        calibrated = CalibratedClassifierCV(model, method="sigmoid", cv=3)
        calibrated.fit(X_train, y_train)

        model_path = MODEL_DIR / f"{lender}_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(calibrated, f)

        # Metadata
        meta = {
            "lender_type": lender,
            "features": FEATURE_COLS,
            "hyperparameters": {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05},
            "base_value": 0.5,
        }
        with open(MODEL_DIR / f"{lender}_metadata.pkl", "wb") as f:
            pickle.dump(meta, f)

        logger.info("  Saved %s_model.pkl", lender)

    logger.info("All 4 loan models trained and saved to %s", MODEL_DIR)
    print("\n✅ Loan model training complete!")
    print(f"   Models saved to: {MODEL_DIR.resolve()}")
    for lender in LENDER_CRITERIA:
        print(f"   • {lender}_model.pkl")


if __name__ == "__main__":
    train_and_save_all()
