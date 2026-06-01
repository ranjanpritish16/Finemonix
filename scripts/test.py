# debug_scaler.py  ← place this in your project root

import asyncio
import sys
import os

# So Python can find your backend modules
sys.path.append(os.path.dirname(__file__))

from backend.ml.lstm_model import load_lstm_model, MODEL_DIR
from backend.ml.features import FEATURE_COLS, TARGET_COL, build_cashflow_features
from backend.database import get_db  
from backend.config import get_settings

BUSINESS_ID = 1  # ← change to your actual business_id

async def main():
    async for db in get_db():
        # Build features
        df = await db.run_sync(build_cashflow_features, BUSINESS_ID)
        
        print(f"\n--- DATASET ---")
        print(f"Total rows:       {len(df)}")
        print(f"Current balance:  {df[TARGET_COL].iloc[-1]:,.0f}")
        print(f"Balance range:    {df[TARGET_COL].min():,.0f} → {df[TARGET_COL].max():,.0f}")

        # Load saved scaler
        model, feat_scaler, tgt_scaler = load_lstm_model(BUSINESS_ID)

        if tgt_scaler is None:
            print("\n❌ No saved model found for this business_id")
            return

        print(f"\n--- SAVED SCALER (what model was trained on) ---")
        print(f"Scaler mean:       {tgt_scaler.mean_[0]:,.0f}")
        print(f"Scaler std:        {tgt_scaler.scale_[0]:,.0f}")
        print(f"Scaler range:      {tgt_scaler.mean_[0] - 2*tgt_scaler.scale_[0]:,.0f} → "
                                f"{tgt_scaler.mean_[0] + 2*tgt_scaler.scale_[0]:,.0f}")

        print(f"\n--- VERDICT ---")
        current = df[TARGET_COL].iloc[-1]
        scaler_max = tgt_scaler.mean_[0] + 2 * tgt_scaler.scale_[0]
        if current > scaler_max:
            print(f"🔴 BUG CONFIRMED: current balance {current:,.0f} is WAY above "
                  f"scaler max {scaler_max:,.0f}")
            print(f"   → Delete model files and retrain")
            print(f"   → Files to delete:")
            print(f"      {MODEL_DIR}/lstm_b{BUSINESS_ID}.pt")
            print(f"      {MODEL_DIR}/lstm_scaler_b{BUSINESS_ID}.pkl")
        else:
            print(f"✅ Scaler range looks fine. Bug is elsewhere.")
        
        break  # only need one db session

asyncio.run(main())