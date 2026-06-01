import asyncio
import sys
import os
import json
import glob
from datetime import date, timedelta
import random
import redis as redis_lib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import async_session_maker, engine
from backend.models import Business, Transaction


async def seed():
    async with async_session_maker() as session:

        # ── Opening balance ────────────────────────────────────────────────
        # Set this to whatever starting balance the demo business has.
        OPENING_BALANCE = 70_132.0

        # ── Derive realistic daily cash flow ranges from opening balance ───
        # Assumption: opening balance ≈ 1-2 months of operating capital.
        # Monthly revenue ≈ 3x opening balance (standard MSME rule of thumb).
        # Daily inflow  = monthly_revenue / 30  (±40% variance for realism)
        # Daily outflow = 85% of daily inflow   (healthy positive net margin)
        # This ensures transaction amounts are always proportional to the
        # business size — avoids the old hardcoded ₹10k-30k range that made
        # no sense for small (₹70k) or large (₹1Cr) opening balances.

        monthly_revenue    = OPENING_BALANCE * 3.0
        avg_daily_inflow   = monthly_revenue / 30
        avg_daily_outflow  = avg_daily_inflow * 0.85   # 85% → net positive bias

        inflow_min  = max(500.0,  avg_daily_inflow  * 0.6)
        inflow_max  =             avg_daily_inflow  * 1.4
        outflow_min = max(400.0,  avg_daily_outflow * 0.6)
        outflow_max =             avg_daily_outflow * 1.4

        print(f"Seed config:")
        print(f"  OPENING_BALANCE  = ₹{OPENING_BALANCE:,.2f}")
        print(f"  monthly_revenue  ≈ ₹{monthly_revenue:,.2f}")
        print(f"  inflow  range    = ₹{inflow_min:,.2f} – ₹{inflow_max:,.2f}/day")
        print(f"  outflow range    = ₹{outflow_min:,.2f} – ₹{outflow_max:,.2f}/day")

        # ── Upsert Business 1 ──────────────────────────────────────────────
        business = await session.get(Business, 1)
        if not business:
            business = Business(
                id=1,
                name="Finemonix Demo Inc.",
                email="demo@finemonix.com",
                industry="Retail",
                opening_balance=OPENING_BALANCE,
            )
            session.add(business)
        else:
            business.opening_balance = OPENING_BALANCE
        await session.commit()
        print(f"\nBusiness 1 ready, opening_balance=₹{OPENING_BALANCE:,.0f}")

        # ── Clear existing transactions ────────────────────────────────────
        await session.execute(delete(Transaction).where(Transaction.business_id == 1))
        await session.commit()
        print("Cleared existing transactions")

        # ── Generate 365 days of transactions ─────────────────────────────
        transactions    = []
        records_for_json = []
        today      = date.today()
        start_date = today - timedelta(days=365)
        running_balance = OPENING_BALANCE

        for i in range(365):
            curr_date   = start_date + timedelta(days=i)
            inflow_amt  = round(random.uniform(inflow_min,  inflow_max),  2)
            outflow_amt = round(random.uniform(outflow_min, outflow_max), 2)

            transactions.append(Transaction(
                business_id=1,
                date=curr_date,
                amount=inflow_amt,
                direction="in",
                source="bank",
                category="Sales",
            ))
            transactions.append(Transaction(
                business_id=1,
                date=curr_date,
                amount=outflow_amt,
                direction="out",
                source="bank",
                category="Expenses",
            ))

            running_balance += inflow_amt - outflow_amt
            records_for_json.append({
                "date":            str(curr_date),
                "inflow":          inflow_amt,
                "outflow":         outflow_amt,
                "net":             round(inflow_amt - outflow_amt, 2),
                "running_balance": round(running_balance, 2),
            })

        session.add_all(transactions)
        await session.commit()
        print(f"Inserted {len(transactions)} transactions "
              f"({len(transactions)//2} days × 2 rows)")
        print(f"Final running_balance in JSON: ₹{running_balance:,.2f}")

        # ── Export JSON for inspection ─────────────────────────────────────
        out_path = os.path.join(os.path.dirname(__file__), "seed_data_output.json")
        with open(out_path, "w") as f:
            json.dump(
                {
                    "business_id": 1,
                    "opening_balance": OPENING_BALANCE,
                    "total_days": len(records_for_json),
                    "date_range": {
                        "from": str(start_date),
                        "to":   str(today),
                    },
                    "daily_records": records_for_json,
                },
                f,
                indent=2,
            )
        print(f"JSON exported: {out_path}")

        # ── Bust Redis forecast cache ──────────────────────────────────────
        try:
            r = redis_lib.Redis(host="localhost", port=6379, decode_responses=True)
            keys = r.keys("forecast:*")
            if keys:
                r.delete(*keys)
                print(f"Redis: cleared {len(keys)} forecast cache key(s)")
            else:
                print("Redis: no forecast keys to clear")
        except Exception as e:
            print(f"Redis: could not connect ({e}) — clear manually if needed")

        # ── Delete stale LSTM model files ──────────────────────────────────
        model_dir = os.path.join(
            os.path.dirname(__file__), "..", "backend", "data", "models"
        )
        removed = []
        for pattern in ["lstm_b1.*", "lstm_scaler_b1.*", "prophet_b1.*"]:
            for f in glob.glob(os.path.join(model_dir, pattern)):
                os.remove(f)
                removed.append(os.path.basename(f))
        print(f"Models cleared: {removed}" if removed else "No stale model files found")


if __name__ == "__main__":
    asyncio.run(seed())