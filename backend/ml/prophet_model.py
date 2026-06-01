import sys
import os

def _add_project_root_to_path() -> None:
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.isdir(os.path.join(current, "backend")):
            if current not in sys.path:
                sys.path.insert(0, current)
            return
        current = os.path.dirname(current)

_add_project_root_to_path()

import json
import pandas as pd
import numpy as np
# pyrefly: ignore [missing-import]
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from typing import Optional, Tuple

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models")

# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_prophet() -> Prophet:
    """Factory so all Prophet instances share the same configuration."""
    m = Prophet(interval_width=0.80)
    m.add_seasonality(name="weekly", period=7, fourier_order=3)
    m.add_seasonality(name="monthly", period=30.5, fourier_order=5)
    m.add_regressor("is_gst_filing_day")
    m.add_regressor("future_invoices")
    return m


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise the input DataFrame to Prophet's required format:
    columns ds (datetime), y (target), and any regressors.
    """
    if "date" in df.columns:
        out = df.copy()
    else:
        out = df.reset_index().rename(columns={"index": "date"})

    out = out.rename(columns={"date": "ds", "running_balance": "y"})

    if "is_gst_filing_day" not in out.columns:
        out["is_gst_filing_day"] = (np.abs(out["ds"].dt.day - 20) <= 2).astype(int)

    if "future_invoices" not in out.columns:
        out["future_invoices"] = 0.0

    return out


# ── Public API ────────────────────────────────────────────────────────────────

def train_prophet_model(
    df: pd.DataFrame,
    future_invoices_df: Optional[pd.DataFrame] = None,
) -> Tuple[Prophet, dict]:
    """
    Train a Prophet model and return (model, metrics).

    FIX 13 + 16: metrics are now computed on a proper held-out split that
    the production model has NEVER seen.  A second, identical Prophet is
    trained on the training portion only; the production model is trained
    on all data after evaluation.
    """
    prepared = _prepare_df(df)

    # ── Evaluation on held-out split (separate model, never shown production data)
    metrics = _evaluate_on_holdout(prepared)

    # ── Production model trained on ALL available data ────────────────────────
    m = _make_prophet()
    m.fit(prepared)

    return m, metrics


def _evaluate_on_holdout(prepared: pd.DataFrame) -> dict:
    """
    FIX 13 & 16: train an *evaluation-only* Prophet on the first N-30 rows,
    forecast on the final 30 rows, and return honest out-of-sample metrics.
    The production model is NOT touched here.
    """
    if len(prepared) <= 30:
        return {"mae": None, "mape": None, "note": "Insufficient data for holdout eval"}

    train = prepared.iloc[:-30].copy()
    test = prepared.iloc[-30:].copy()

    m_eval = _make_prophet()
    m_eval.fit(train)

    # Predict on held-out rows using their actual regressor values
    future_eval = test[["ds", "is_gst_filing_day", "future_invoices"]].copy()
    forecast = m_eval.predict(future_eval)

    y_true = test["y"].values
    y_pred = forecast["yhat"].values

    mae = mean_absolute_error(y_true, y_pred)
    # Guard against division-by-zero if any true value is 0
    nonzero = y_true != 0
    mape = (
        float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])))
        if nonzero.any()
        else None
    )

    return {"mae": float(mae), "mape": mape}


def generate_forecast(
    m: Prophet,
    periods: int = 90,
    future_invoices_series: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """
    Generate a `periods`-day forward forecast.

    FIX 14: replaced row-by-row iterrows loop with vectorised pd.Series.reindex.
    FIX 15: future_invoices_series index is coerced to DatetimeIndex so the
            lookup always works regardless of how the caller constructed it.
    """
    future = m.make_future_dataframe(periods=periods, freq="D")
    future["is_gst_filing_day"] = (np.abs(future["ds"].dt.day - 20) <= 2).astype(int)
    future["future_invoices"] = 0.0

    if future_invoices_series is not None:
        # FIX 15: normalise index to DatetimeIndex
        inv = future_invoices_series.copy()
        inv.index = pd.to_datetime(inv.index)

        # FIX 14: vectorised assignment via reindex (O(n) not O(n²))
        future = future.set_index("ds")
        aligned = inv.reindex(future.index, fill_value=0.0)
        future["future_invoices"] = aligned.values
        future = future.reset_index().rename(columns={"index": "ds"})

    forecast = m.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]


def save_model(model: Prophet, business_id: int) -> None:
    """
    Persist Prophet model to disk.

    FIX 17: renamed from serialize_model → save_model to match load_model.
    Old name kept as an alias for backward compatibility.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    file_path = os.path.join(MODEL_DIR, f"prophet_b{business_id}.json")
    with open(file_path, "w") as f:
        json.dump(model_to_json(model), f)


# Backward-compatibility alias
serialize_model = save_model


def load_model(business_id: int) -> Optional[Prophet]:
    """Load a previously saved Prophet model, or return None if not found."""
    file_path = os.path.join(MODEL_DIR, f"prophet_b{business_id}.json")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return model_from_json(json.load(f))