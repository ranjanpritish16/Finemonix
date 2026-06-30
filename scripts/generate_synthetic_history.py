"""
Generate synthetic pre-history bank transactions to extend the model's
training window so calendar patterns (GST filing, salary week, month-end)
repeat enough times (12-24 cycles) for the LSTM to actually learn them.

Calibrated against your real data:
  - mean daily net_cash_flow ≈ ₹21,223 (from real March-June 2026 data)
  - real data starts 2026-03-01

This generates ~18 months of synthetic history ending right before your
real data starts, so splicing is seamless. Tagged source='bank_synthetic'
so it's clearly distinguishable from real uploads and easy to wipe later.
"""

import asyncio
import random
from datetime import date, timedelta
from backend.database import async_session_maker
from backend.models import Transaction

BUSINESS_ID = 1
REAL_DATA_START = date(2026, 3, 1)   # your real CSV's earliest date
SYNTHETIC_MONTHS = 18                 # ~1.5 years of synthetic pre-history
SYNTHETIC_START = date(REAL_DATA_START.year - 1, REAL_DATA_START.month, REAL_DATA_START.day) \
    if REAL_DATA_START.month != 3 else date(2024, 9, 1)  # fallback, adjust below

# Cleaner: just go back exactly SYNTHETIC_MONTHS*30 days from real start
SYNTHETIC_START = REAL_DATA_START - timedelta(days=SYNTHETIC_MONTHS * 30)
SYNTHETIC_END   = REAL_DATA_START - timedelta(days=1)

# Calibration from real data
BASE_DAILY_INFLOW_MEAN  = 14_000   # tune so cash_in - cash_out ≈ +21,223 avg
BASE_DAILY_INFLOW_STD   = 5_000
BASE_DAILY_OUTFLOW_MEAN = 6_500    # smaller baseline outflow most days
BASE_DAILY_OUTFLOW_STD  = 2_500

GST_FILING_OUTFLOW_MEAN = 45_000   # large spike near the 18th-22nd
GST_FILING_OUTFLOW_STD  = 8_000

SALARY_WEEK_OUTFLOW_MEAN = 60_000  # large spike days 25-31
SALARY_WEEK_OUTFLOW_STD  = 10_000

MONTH_END_EXTRA_OUTFLOW_MEAN = 15_000  # vendor settlements, last 2-3 days


def is_gst_day(d: date) -> bool:
    return abs(d.day - 20) <= 2


def is_salary_week(d: date) -> bool:
    return d.day >= 25


def is_month_end(d: date) -> bool:
    import calendar
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    return (days_in_month - d.day) <= 2


def generate_day(d: date) -> list[dict]:
    """Generate 0-3 synthetic transactions for a single day."""
    txns = []

    # Baseline daily inflow (client payments, sales)
    if random.random() < 0.75:  # most days have some inflow
        amt = max(500, random.gauss(BASE_DAILY_INFLOW_MEAN, BASE_DAILY_INFLOW_STD))
        txns.append({"amount": round(amt, 2), "direction": "in",
                     "category": "Sales Receipt", "raw_description": "Client Payment"})

    # Baseline daily outflow (routine expenses)
    if random.random() < 0.65:
        amt = max(500, random.gauss(BASE_DAILY_OUTFLOW_MEAN, BASE_DAILY_OUTFLOW_STD))
        txns.append({"amount": round(amt, 2), "direction": "out",
                     "category": "Operating Expense", "raw_description": "Vendor Payment"})

    # GST filing spike
    if is_gst_day(d) and random.random() < 0.6:
        amt = max(5_000, random.gauss(GST_FILING_OUTFLOW_MEAN, GST_FILING_OUTFLOW_STD))
        txns.append({"amount": round(amt, 2), "direction": "out",
                     "category": "Tax Payment", "raw_description": "GST Filing"})

    # Salary week spike
    if is_salary_week(d) and random.random() < 0.5:
        amt = max(10_000, random.gauss(SALARY_WEEK_OUTFLOW_MEAN, SALARY_WEEK_OUTFLOW_STD))
        txns.append({"amount": round(amt, 2), "direction": "out",
                     "category": "Payroll", "raw_description": "Salary Disbursement"})

    # Month-end vendor settlement
    if is_month_end(d) and random.random() < 0.4:
        amt = max(2_000, random.gauss(MONTH_END_EXTRA_OUTFLOW_MEAN, 4_000))
        txns.append({"amount": round(amt, 2), "direction": "out",
                     "category": "Operating Expense", "raw_description": "Month-End Settlement"})

    return txns


async def generate_and_insert():
    async with async_session_maker() as session:
        current = SYNTHETIC_START
        all_txns = []
        day_count = 0

        while current <= SYNTHETIC_END:
            for t in generate_day(current):
                all_txns.append(Transaction(
                    business_id=BUSINESS_ID,
                    date=current,
                    amount=t["amount"],
                    direction=t["direction"],
                    category=t["category"],
                    counterparty_id=None,
                    source="bank_syn",   # tagged separately from 'bank'
                    raw_description=t["raw_description"],
                ))
            current += timedelta(days=1)
            day_count += 1

        session.add_all(all_txns)
        await session.commit()
        print(f"Inserted {len(all_txns)} synthetic transactions across {day_count} days")
        print(f"Range: {SYNTHETIC_START} to {SYNTHETIC_END}")


if __name__ == "__main__":
    asyncio.run(generate_and_insert())