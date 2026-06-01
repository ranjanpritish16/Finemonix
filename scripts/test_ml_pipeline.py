"""
Standalone script to test the ML pipeline end-to-end with synthetic data.
Run from the project root with:
    python scripts/test_ml_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import date, timedelta

print("=" * 60)
print("FINEMONIX ML PIPELINE - END-TO-END TEST")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# STEP 1: Generate synthetic daily cash flow data
# ─────────────────────────────────────────────────────────────
print("\n[STEP 1] Generating synthetic daily cash flow data...")

np.random.seed(42)
num_days = 200  # ~6.5 months of data

dates = pd.date_range(start="2023-10-01", periods=num_days, freq="D")

# Simulate a realistic SME cash balance with trend + seasonality + noise
trend = np.linspace(100000, 150000, num_days)
seasonality = 10000 * np.sin(np.arange(num_days) * 2 * np.pi / 30)  # monthly cycle
noise = np.random.normal(0, 5000, num_days)
balance = trend + seasonality + noise

df = pd.DataFrame({
    "date": dates,
    "running_balance": balance,
    "net_cashflow": np.diff(balance, prepend=balance[0]),
    "inflow": np.abs(np.random.normal(20000, 5000, num_days)),
    "outflow": np.abs(np.random.normal(15000, 4000, num_days)),
    "is_month_end": (dates.day >= 28).astype(int),
    "is_gst_filing_day": ((dates.day >= 18) & (dates.day <= 22)).astype(int),
    "is_salary_week": (dates.day >= 25).astype(int),
    "day_of_week": dates.dayofweek,
    "day_of_month": dates.day,
    "month": dates.month,
    "week_of_year": dates.isocalendar().week.astype(int),
    "is_quarter_end": dates.is_quarter_end.astype(int),
    "recurring_expense_flag": np.random.choice([0, 1], size=num_days, p=[0.85, 0.15]),
    "avg_client_delay_days": np.random.normal(15, 5, num_days).clip(0),
    "overdue_receivables": np.random.normal(30000, 10000, num_days).clip(0),
    "future_invoices": np.random.normal(25000, 8000, num_days).clip(0),
})

print(f"  ✓ Generated {num_days} days of synthetic data")
print(f"  Balance range: ₹{balance.min():,.0f} – ₹{balance.max():,.0f}")

# ─────────────────────────────────────────────────────────────
# STEP 2: Prophet Model (for < 6 months of data use case)
# ─────────────────────────────────────────────────────────────
print("\n[STEP 2] Training Prophet Baseline Model...")
print("  (Prophet is used when business has < 6 months of data)")

from backend.ml.prophet_model import train_prophet_model, generate_forecast, serialize_model

# Use only 90 days (3 months) to demonstrate Prophet's cold-start use case
df_short = df.iloc[:90].copy()

prophet_model, metrics = train_prophet_model(df_short)

print(f"  ✓ Prophet model trained!")
print(f"  Evaluation Metrics (last 30-day holdout):")
print(f"    MAE  = ₹{metrics['mae']:,.0f}")
print(f"    MAPE = {metrics['mape']*100:.2f}%")

# Generate forecast
forecast_df = generate_forecast(prophet_model, periods=90)
print(f"\n  Sample 7-day Forecast (Prophet):")
print(f"  {'Date':<15} {'Predicted':>15} {'P10':>15} {'P90':>15}")
print(f"  {'-'*60}")
for _, row in forecast_df.head(7).iterrows():
    print(f"  {str(row['ds'].date()):<15} ₹{row['yhat']:>12,.0f} ₹{row['yhat_lower']:>12,.0f} ₹{row['yhat_upper']:>12,.0f}")

# ─────────────────────────────────────────────────────────────
# STEP 3: LSTM Model (for >= 6 months of data)
# ─────────────────────────────────────────────────────────────
print("\n[STEP 3] Training LSTM Model...")
print("  (LSTM is used when business has >= 6 months of data)")

from backend.ml.lstm_model import train_lstm_model, predict_lstm_mc_dropout

FEATURE_COLS = [
    "net_cashflow", "inflow", "outflow",
    "is_month_end", "is_gst_filing_day", "is_salary_week",
    "day_of_week", "day_of_month", "month", "week_of_year",
    "is_quarter_end", "recurring_expense_flag",
    "avg_client_delay_days", "overdue_receivables", "future_invoices"
]
TARGET_COL = "running_balance"

# Use full 200-day dataset for LSTM
lstm_model = train_lstm_model(df, FEATURE_COLS, TARGET_COL, business_id=999)
print("  ✓ LSTM model trained! (saved to backend/data/models/lstm_b999.pt)")

# Inference with MC Dropout
print("\n  Running 30-pass Monte Carlo Dropout inference for uncertainty...")
last_60_features = df[FEATURE_COLS].iloc[-60:].values  # Last 60 days

lstm_forecast_df = predict_lstm_mc_dropout(lstm_model, last_60_features, num_passes=30)

print(f"\n  Sample 7-day LSTM Forecast with Uncertainty Bands:")
print(f"  {'Date':<15} {'Predicted':>15} {'P10':>15} {'P90':>15}")
print(f"  {'-'*60}")
for _, row in lstm_forecast_df.head(7).iterrows():
    print(f"  {str(row['date']):<15} ₹{row['predicted_balance']:>12,.0f} ₹{row['p10_balance']:>12,.0f} ₹{row['p90_balance']:>12,.0f}")

# ─────────────────────────────────────────────────────────────
# STEP 4: Summary
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PIPELINE TEST COMPLETE ✓")
print("=" * 60)
print("""
Key Results:
  - Prophet: Works for cold-start (< 6 months). Returns P10/P90 bands.
  - LSTM: Works for mature businesses (>= 6 months). MC Dropout gives
          uncertainty estimates from 30 stochastic forward passes.
  - Both models are triggered automatically via Celery after data upload.
  - Forecasts are served at GET /api/forecast/{business_id}
""")
