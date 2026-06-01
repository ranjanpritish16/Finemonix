import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Tuple

from backend.models import Transaction, Invoice, Business


def build_cashflow_features(db: Session, business_id: int) -> pd.DataFrame:
    """
    Produce a daily time series of cash flow features ready for LSTM.

    ARCHITECTURE:
      The model predicts net_cash_flow (daily delta, e.g. +₹5,000 or -₹3,000)
      instead of next_day_balance (absolute rupee level, e.g. ₹12L).
      Predicting small deltas is a much simpler task for an LSTM with 365 rows.
      The running balance is reconstructed in forecast.py via:
          balance[day_n] = last_known_balance + cumsum(predicted_net[1..n])
      This guarantees day-1 anchoring without any offset hack.

    FIX 1: real_current_balance = opening_balance + total_in - total_out
            opening_balance is fetched from the Business table so the
            running_balance is on the correct absolute rupee scale.
    FIX 2: TARGET_COL = net_cash_flow. next_day_balance is no longer used.
    FIX 3: is_month_end = last 3 days of month only (not first 3).
    FIX 4: business_avg_delay excluded (scalar, not per-day).
    FIX 5: No NaN drop needed — net_cash_flow has no shift, so no NaN row.
    """
    stmt = select(Transaction).where(Transaction.business_id == business_id)
    tx_records = db.execute(stmt).scalars().all()

    if not tx_records:
        return pd.DataFrame()

    tx_data = [
        {
            "date": tx.date,
            "amount": float(tx.amount),
            "direction": tx.direction,
            "category": tx.category,
            "counterparty_id": tx.counterparty_id,
        }
        for tx in tx_records
    ]

    df_tx = pd.DataFrame(tx_data)
    df_tx["date"] = pd.to_datetime(df_tx["date"])

    # ── Daily aggregates ─────────────────────────────────────────────────────
    df_tx["cash_in"] = np.where(df_tx["direction"] == "in", df_tx["amount"], 0.0)
    df_tx["cash_out"] = np.where(df_tx["direction"] == "out", df_tx["amount"], 0.0)

    daily_df = (
        df_tx.groupby("date")
        .agg(cash_in=("cash_in", "sum"), cash_out=("cash_out", "sum"))
        .reset_index()
    )

    # Fill missing dates → continuous time series
    full_range = pd.date_range(
        start=daily_df["date"].min(), end=daily_df["date"].max(), freq="D"
    )
    daily_df = (
        daily_df.set_index("date")
        .reindex(full_range)
        .fillna(0.0)
        .rename_axis("date")
        .reset_index()
    )

    daily_df["net_cash_flow"] = daily_df["cash_in"] - daily_df["cash_out"]

    # ── FIX 1: Anchor running_balance to real DB balance ──────────────────────
    # real_current_balance = opening_balance + sum(inflows) - sum(outflows)
    # opening_balance comes from the Business table — this is the correct
    # starting point that seed.py and real imports set explicitly.
    opening_balance = float(
        db.execute(
            select(Business.opening_balance).where(Business.id == business_id)
        ).scalar() or 0.0
    )

    total_in = float(
        db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.business_id == business_id,
                Transaction.direction == "in",
            )
        ).scalar() or 0.0
    )

    total_out = float(
        db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.business_id == business_id,
                Transaction.direction == "out",
            )
        ).scalar() or 0.0
    )

    real_current_balance = opening_balance + total_in - total_out

    # Shift cumsum so its last value == real_current_balance.
    # This preserves the daily shape/pattern while anchoring to the correct
    # absolute rupee scale.
    raw_cumsum = daily_df["net_cash_flow"].cumsum()
    offset = real_current_balance - raw_cumsum.iloc[-1]
    daily_df["running_balance"] = raw_cumsum + offset

    # ── Calendar features ────────────────────────────────────────────────────
    daily_df["day_of_week"]   = daily_df["date"].dt.dayofweek
    daily_df["day_of_month"]  = daily_df["date"].dt.day
    daily_df["month"]         = daily_df["date"].dt.month

    # is_month_end = last 3 days of the month ONLY
    days_in_month = daily_df["date"].dt.days_in_month
    daily_df["is_month_end"] = (
        (days_in_month - daily_df["day_of_month"]) <= 2
    ).astype(int)

    daily_df["is_quarter_end"] = (
        daily_df["month"].isin([3, 6, 9, 12]) & (daily_df["is_month_end"] == 1)
    ).astype(int)

    # GST filing due ≈ 20th of every month (±2 days)
    daily_df["is_gst_filing_day"] = (
        np.abs(daily_df["day_of_month"] - 20) <= 2
    ).astype(int)

    # Salary week (25th–31st)
    daily_df["is_salary_week"] = (daily_df["day_of_month"] >= 25).astype(int)

    # ── Recurring expense flag ────────────────────────────────────────────────
    recurring_dates = detect_recurring_expenses(df_tx)
    daily_df["has_recurring_expense"] = (
        daily_df["date"].isin(recurring_dates).astype(int)
    )

    daily_df = daily_df.set_index("date")

    # Debug prints
    print(f"DEBUG opening_balance:       {opening_balance:,.2f}")
    print(f"DEBUG total_in:              {total_in:,.2f}")
    print(f"DEBUG total_out:             {total_out:,.2f}")
    print(f"DEBUG real_current_balance:  {real_current_balance:,.2f}")
    print(f"DEBUG running_balance last:  {daily_df['running_balance'].iloc[-1]:,.2f}")
    print(f"DEBUG net_cash_flow mean:    {daily_df['net_cash_flow'].mean():,.2f}")
    print(f"DEBUG total rows:            {len(daily_df)}")

    return daily_df


# ---------------------------------------------------------------------------
# Feature columns — inputs to the LSTM.
# net_cash_flow is the TARGET so it is excluded here (data leakage guard).
# running_balance is included so the model knows current balance level.
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "running_balance",
    "cash_in",
    "cash_out",
    "day_of_week",
    "day_of_month",
    "month",
    "is_month_end",
    "is_quarter_end",
    "is_gst_filing_day",
    "is_salary_week",
    "has_recurring_expense",
]

# TARGET: predict today's net cash flow (delta), NOT absolute balance.
# forecast.py converts predictions → running balance via cumsum anchored
# to last_known_balance.
TARGET_COL = "net_cash_flow"


def detect_recurring_expenses(df_tx: pd.DataFrame) -> set:
    """
    Identify dates where recurring large expenses occur (>= Rs 10,000, ~monthly).
    Checks ALL pairs within 27-33 day window, not just consecutive ones.
    """
    large_out = df_tx[
        (df_tx["direction"] == "out") & (df_tx["amount"] >= 10_000)
    ].copy()

    if large_out.empty:
        return set()

    recurring_dates: set = set()
    large_out = large_out.sort_values("date")

    for category, group in large_out.groupby("category"):
        dates = group["date"].tolist()
        if len(dates) < 2:
            continue
        for i in range(len(dates)):
            for j in range(i + 1, len(dates)):
                diff = (dates[j] - dates[i]).days
                if 27 <= diff <= 33:
                    recurring_dates.add(dates[i])
                    recurring_dates.add(dates[j])

    return recurring_dates


def compute_business_avg_delay(db: Session, business_id: int) -> float:
    """Average payment delay across all paid invoices for the business."""
    stmt = select(func.avg(Invoice.days_overdue)).where(
        Invoice.business_id == business_id,
        Invoice.status == "paid",
        Invoice.days_overdue.isnot(None),
    )
    avg_delay = db.execute(stmt).scalar()
    return float(avg_delay) if avg_delay is not None else 0.0


def split_train_val_test(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    last 30 days -> test | previous 30 -> val | rest -> train.
    Raises ValueError when data is too short.
    """
    if len(df) < 90:
        raise ValueError(
            f"Insufficient data for LSTM split: {len(df)} rows (need >= 90). "
            "Use the Prophet model for cold-start."
        )

    test_size = 30
    val_size  = 30
    train_end = len(df) - test_size - val_size
    val_end   = len(df) - test_size

    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]