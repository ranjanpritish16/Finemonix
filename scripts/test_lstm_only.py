"""
Test script for LSTM model only (no CmdStan required).
Run from project root:
    python scripts/test_lstm_only.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["PYTHONIOENCODING"] = "utf-8"

import pandas as pd
import numpy as np
from datetime import date, timedelta

print("=" * 60)
print("LSTM CASH FLOW MODEL - END-TO-END TEST")
print("=" * 60)

# ── STEP 1: Synthetic data ──────────────────────────────────
print("\n[STEP 1] Generating 200-day synthetic cash flow data...")
np.random.seed(42)
num_days = 200
dates = pd.date_range(start="2023-10-01", periods=num_days, freq="D")

trend       = np.linspace(100000, 150000, num_days)
seasonality = 10000 * np.sin(np.arange(num_days) * 2 * np.pi / 30)
noise       = np.random.normal(0, 5000, num_days)
balance     = trend + seasonality + noise

df = pd.DataFrame({
    "date":                   dates,
    "running_balance":        balance,
    "net_cashflow":           np.diff(balance, prepend=balance[0]),
    "inflow":                 np.abs(np.random.normal(20000, 5000, num_days)),
    "outflow":                np.abs(np.random.normal(15000, 4000, num_days)),
    "is_month_end":           (dates.day >= 28).astype(int),
    "is_gst_filing_day":      ((dates.day >= 18) & (dates.day <= 22)).astype(int),
    "is_salary_week":         (dates.day >= 25).astype(int),
    "day_of_week":            dates.dayofweek,
    "day_of_month":           dates.day,
    "month":                  dates.month,
    "week_of_year":           dates.isocalendar().week.astype(int),
    "is_quarter_end":         dates.is_quarter_end.astype(int),
    "recurring_expense_flag": np.random.choice([0, 1], size=num_days, p=[0.85, 0.15]),
    "avg_client_delay_days":  np.random.normal(15, 5, num_days).clip(0),
    "overdue_receivables":    np.random.normal(30000, 10000, num_days).clip(0),
    "future_invoices":        np.random.normal(25000, 8000, num_days).clip(0),
})

print(f"  OK  {num_days} days generated")
print(f"  Balance: Rs.{balance.min():,.0f} - Rs.{balance.max():,.0f}")

# ── STEP 2: Train LSTM ──────────────────────────────────────
print("\n[STEP 2] Training 2-Layer LSTM (may take 10-30s)...")

FEATURE_COLS = [
    "net_cashflow", "inflow", "outflow",
    "is_month_end", "is_gst_filing_day", "is_salary_week",
    "day_of_week", "day_of_month", "month", "week_of_year",
    "is_quarter_end", "recurring_expense_flag",
    "avg_client_delay_days", "overdue_receivables", "future_invoices"
]

from backend.ml.lstm_model import train_lstm_model, predict_lstm_mc_dropout

model, feat_scaler, tgt_scaler = train_lstm_model(df, FEATURE_COLS, "running_balance", business_id=1)
print("  OK  LSTM training complete!")

# ── STEP 3: Inference with MC Dropout ──────────────────────
print("\n[STEP 3] Predicting next 90 days (30 MC Dropout passes)...")

last_60 = df[FEATURE_COLS].iloc[-60:].values
forecast = predict_lstm_mc_dropout(model, last_60, feat_scaler, tgt_scaler, num_passes=30)

print("\n  Next 14-day forecast:")
print(f"  {'Date':<14} {'Predicted':>14} {'P10 (Low)':>14} {'P90 (High)':>14}")
print(f"  {'-'*56}")
for _, row in forecast.head(14).iterrows():
    uncertainty = row["p90_balance"] - row["p10_balance"]
    print(f"  {str(row['date']):<14} "
          f"Rs.{row['predicted_balance']:>10,.0f} "
          f"Rs.{row['p10_balance']:>10,.0f} "
          f"Rs.{row['p90_balance']:>10,.0f}  "
          f"(+/-Rs.{uncertainty/2:,.0f})")

# ── STEP 4: Quick accuracy check ──────────────────────────
print("\n[STEP 4] Checking prediction accuracy on known data...")
import torch

# Use rows 60-149 as input, predict days 150-239... but we only have 200
# So test: use rows 0-59 as window, check if prediction is in right range for days 60-90
from backend.ml.lstm_model import CashFlowLSTM

window = df[FEATURE_COLS].iloc[0:60].values
actual_next_7 = df["running_balance"].iloc[60:67].values

test_forecast = predict_lstm_mc_dropout(model, window, feat_scaler, tgt_scaler, num_passes=30)
predicted_next_7 = test_forecast["predicted_balance"].iloc[:7].values

mae = np.mean(np.abs(predicted_next_7 - actual_next_7))
mape = np.mean(np.abs((predicted_next_7 - actual_next_7) / actual_next_7)) * 100

print(f"\n  Accuracy on first 7 known future days:")
print(f"  MAE  = Rs.{mae:,.0f}  (mean absolute error)")
print(f"  MAPE = {mape:.1f}%  (target: under 15%)")

for i in range(7):
    status = "GOOD" if abs(predicted_next_7[i] - actual_next_7[i]) / actual_next_7[i] < 0.15 else "MISS"
    print(f"  Day {i+1}: Actual Rs.{actual_next_7[i]:>10,.0f} | Predicted Rs.{predicted_next_7[i]:>10,.0f} [{status}]")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
