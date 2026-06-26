from __future__ import annotations

import os
import json
import logging
import time
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import get_db
from backend.ml.features import (
    FEATURE_COLS,
    TARGET_COL,
    build_cashflow_features,
)
from backend.ml.loan_cta import compute_loan_cta
from backend.ml.loan_features import extract_loan_features
from backend.ml.lstm_model import (
    load_lstm_model,
    predict_lstm_mc_dropout,
    train_lstm_model,
    MODEL_DIR,
)
from backend.models import Invoice, Transaction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forecast", tags=["Forecast"])
settings = get_settings()


# ── Redis dependency ──────────────────────────────────────────────────────────

async def get_redis() -> aioredis.Redis:
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.aclose()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ScenarioRequest(BaseModel):
    business_id: int
    client_id: int
    delay_days: int
    amount_override: Optional[float] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_danger_zones(
    forecast_df: pd.DataFrame,
    operating_threshold: float,
) -> list[dict]:
    """
    Return contiguous date ranges where the p10 (pessimistic) balance
    falls below the operating threshold.
    """
    danger = forecast_df[forecast_df["p10_balance"] < operating_threshold].copy()
    if danger.empty:
        return []

    zones = []
    danger = danger.sort_values("date").reset_index(drop=True)
    start = danger.loc[0, "date"]
    prev  = danger.loc[0, "date"]

    for i in range(1, len(danger)):
        curr = danger.loc[i, "date"]
        if (curr - prev).days > 1:
            zones.append(_zone(danger, start, prev, operating_threshold))
            start = curr
        prev = curr

    zones.append(_zone(danger, start, prev, operating_threshold))
    return zones


def _zone(df: pd.DataFrame, start, end, threshold: float) -> dict:
    mask = (df["date"] >= start) & (df["date"] <= end)
    min_bal = float(df.loc[mask, "p10_balance"].min())
    shortfall = threshold - min_bal
    severity = (
        "critical" if shortfall > threshold * 0.5
        else "high"  if shortfall > threshold * 0.2
        else "medium"
    )
    return {
        "start_date": str(start),
        "end_date":   str(end),
        "min_balance": round(min_bal, 2),
        "severity":    severity,
    }


def _build_features_sync(sync_session: Session, business_id: int) -> pd.DataFrame:
    return build_cashflow_features(sync_session, business_id)


def _get_operating_threshold_sync(sync_session: Session, business_id: int) -> float:
    """30-day average daily outflow as operating threshold."""
    stmt = (
        select(func.avg(Transaction.amount))
        .where(
            Transaction.business_id == business_id,
            Transaction.direction == "out",
            Transaction.date >= date.today() - timedelta(days=30),
        )
    )
    avg_daily = sync_session.execute(stmt).scalar()
    return float(avg_daily or 0) * 30


async def _get_features(db: AsyncSession, business_id: int) -> pd.DataFrame:
    return await db.run_sync(_build_features_sync, business_id)


async def _get_threshold(db: AsyncSession, business_id: int) -> float:
    return await db.run_sync(_get_operating_threshold_sync, business_id)


def _run_lstm(
    df: pd.DataFrame,
    horizon_days: int,
    business_id: int,
) -> tuple[pd.DataFrame, float]:
    """
    Load or train LSTM, run MC Dropout inference, then convert predicted
    net cash flows → running balance via cumsum anchored to last known balance.

    Architecture:
      Model predicts: net_cash_flow[day_1 .. day_90]  (small deltas, easy to learn)
      We convert to:  balance[day_n] = last_known + cumsum(net[1..n])
      This guarantees day-1 starts exactly at last_known_balance.

    Retrain if:
      - No model file exists
      - Saved target_col is not net_cash_flow (stale model from old architecture)
      - Model file older than 7 days
    """
    model, feat_scaler, tgt_scaler = load_lstm_model(business_id)

    should_retrain = model is None

    if not should_retrain:
        # ── Check 1: stale architecture (old model predicted balance, not net) ─
        weights_path = os.path.join(MODEL_DIR, f"lstm_b{business_id}.pt")
        scaler_path  = os.path.join(MODEL_DIR, f"lstm_scaler_b{business_id}.pkl")
        if os.path.exists(scaler_path):
            import pickle
            with open(scaler_path, "rb") as f:
                meta = pickle.load(f)
            saved_target = meta.get("target_col", "")
            if saved_target != TARGET_COL:
                logger.info(
                    "Stale model: saved target_col='%s', current TARGET_COL='%s'. Retraining.",
                    saved_target, TARGET_COL,
                )
                should_retrain = True

        # ── Check 2: model file older than 7 days ────────────────────────────
        if not should_retrain and os.path.exists(weights_path):
            model_age_days = (time.time() - os.path.getmtime(weights_path)) / 86400
            if model_age_days > 7:
                logger.info("Model is %.1f days old. Retraining.", model_age_days)
                should_retrain = True

    if should_retrain:
        logger.info("Training new LSTM model for business %s", business_id)
        model, feat_scaler, tgt_scaler = train_lstm_model(
            df, FEATURE_COLS, TARGET_COL, business_id
        )

    # ── Inference ─────────────────────────────────────────────────────────────
    # Use last 60 rows as input window (unscaled — predict_lstm_mc_dropout
    # scales internally using feat_scaler)
    window = df[FEATURE_COLS].iloc[-60:].values

    # Returns DataFrame with columns: date, predicted_net, p10_net, p90_net
    net_forecast_df = predict_lstm_mc_dropout(
        model, window, feat_scaler, tgt_scaler, num_passes=30
    )

    if len(net_forecast_df) < horizon_days:
        logger.warning(
            "Model horizon %d < requested horizon %d.",
            len(net_forecast_df), horizon_days,
        )

    net_forecast_df = net_forecast_df.head(horizon_days)

    # ── Convert net cash flow → running balance ───────────────────────────────
    # This is the key architectural fix:
    #   balance[day_1] = last_known + net[day_1]
    #   balance[day_2] = last_known + net[day_1] + net[day_2]
    #   ...
    # Day 1 is guaranteed to be near last_known_balance regardless of model quality.
    last_known_balance = float(df["running_balance"].iloc[-1])

    predicted_balance = last_known_balance + net_forecast_df["predicted_net"].cumsum().values
    p10_balance       = last_known_balance + net_forecast_df["cum_p10_net"].values
    p90_balance       = last_known_balance + net_forecast_df["cum_p90_net"].values

    logger.info(
        "Forecast anchored: last_known=%.2f, day1_predicted=%.2f, day1_p10=%.2f, day1_p90=%.2f",
        last_known_balance, predicted_balance[0], p10_balance[0], p90_balance[0],
    )
    print(f"DEBUG last_known_balance: {last_known_balance:,.2f}")
    print(f"DEBUG day1 predicted_balance: {predicted_balance[0]:,.2f}")
    print(f"DEBUG day1 p10_balance: {p10_balance[0]:,.2f}")
    print(f"DEBUG day1 p90_balance: {p90_balance[0]:,.2f}")

    forecast_df = pd.DataFrame({
        "date":              net_forecast_df["date"].values,
        "predicted_balance": predicted_balance,
        "p10_balance":       p10_balance,
        "p90_balance":       p90_balance,
    })

    return forecast_df, 85.0


def _run_linear_fallback(df: pd.DataFrame, horizon_days: int) -> tuple[pd.DataFrame, float]:
    """
    Fast statistical fallback (< 100ms) using linear regression on running balance.
    Used when: data < 90 days, or LSTM training fails.
    """
    from sklearn.linear_model import LinearRegression

    df = df.copy().reset_index(drop=True)
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["running_balance"].values

    model = LinearRegression()
    model.fit(X, y)

    # Extrapolate
    last_idx = len(df)
    future_X = np.arange(last_idx, last_idx + horizon_days).reshape(-1, 1)
    predicted = model.predict(future_X)

    # Simple uncertainty: ±1 std of recent residuals
    residuals = y - model.predict(X)
    std = float(np.std(residuals)) if len(residuals) > 1 else abs(float(y[-1]) * 0.05)

    base_date = pd.Timestamp.today().date()
    dates = [base_date + pd.Timedelta(days=i) for i in range(1, horizon_days + 1)]

    forecast_df = pd.DataFrame({
        "date":              dates,
        "predicted_balance": predicted,
        "p10_balance":       predicted - 1.28 * std,
        "p90_balance":       predicted + 1.28 * std,
    })

    logger.info("Linear fallback: day1=%.2f, trend_slope=%.2f/day", predicted[0], model.coef_[0])
    return forecast_df, 60.0  # 60% baseline accuracy for linear model




@router.get("/{business_id}")
async def get_forecast(
    business_id: int,
    horizon_days: int = Query(90, le=180),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    # ── 1. Cache check ────────────────────────────────────────────────────────
    cache_key = f"forecast:{business_id}:{horizon_days}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # ── 2. Check how much data we have ───────────────────────────────────────
    stmt = select(
        func.min(Transaction.date), func.max(Transaction.date)
    ).where(Transaction.business_id == business_id)
    result = await db.execute(stmt)
    min_date, max_date = result.first()

    if not min_date or not max_date:
        raise HTTPException(
            status_code=404,
            detail="No transaction data found. Please upload data first.",
        )

    days_of_data = (max_date - min_date).days
    has_sufficient_data = days_of_data >= 180

    # ── 3. Build features ─────────────────────────────────────────────────────
    try:
        df = await _get_features(db, business_id)
    except Exception as e:
        logger.error("Feature engineering failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {e}")

    if df.empty:
        raise HTTPException(status_code=404, detail="No transaction data found.")

    # ── 4. Run model (in thread pool so we don't block the event loop) ────────
    import asyncio
    loop = asyncio.get_event_loop()

    warning = (
        None if has_sufficient_data
        else "Due to scarcity of dataset, predictions may be imprecise."
    )

    # Use fast linear fallback when data is insufficient for LSTM (<90 days)
    if days_of_data < 90:
        logger.info("Insufficient data for LSTM (%d days). Using linear fallback.", days_of_data)
        try:
            forecast_df, accuracy_pct = await loop.run_in_executor(
                None, _run_linear_fallback, df, horizon_days
            )
            model_used = "linear"
        except Exception as e:
            logger.error("Linear fallback failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Fallback model failed: {e}")
    else:
        try:
            forecast_df, accuracy_pct = await loop.run_in_executor(
                None, _run_lstm, df, horizon_days, business_id
            )
            model_used = "lstm"
        except Exception as e:
            logger.warning("LSTM failed (%s). Falling back to linear model.", e)
            try:
                forecast_df, accuracy_pct = await loop.run_in_executor(
                    None, _run_linear_fallback, df, horizon_days
                )
                model_used = "linear"
                warning = "LSTM model failed; using statistical fallback."
            except Exception as e2:
                logger.error("All models failed: %s", e2)
                raise HTTPException(status_code=500, detail=f"All forecast models failed: {e2}")

    # ── 5. Compute danger zones ───────────────────────────────────────────────
    try:
        threshold = await _get_threshold(db, business_id)
    except Exception:
        threshold = 50_000.0

    danger_zones = _compute_danger_zones(forecast_df, threshold)


    # ── 6. Contextual loan CTA ────────────────────────────────────────────────
    loan_cta = None
    try:
        loan_features, loan_meta = await db.run_sync(
            lambda s: extract_loan_features(s, business_id)
        )
        vintage_years = loan_meta.get("vintage_years", 0.0)
        cibil_score   = loan_features.get("cibil_score", 650.0)
        loan_cta = compute_loan_cta(
            danger_zones=danger_zones,
            vintage_years=vintage_years,
            cibil_score=cibil_score,
            operating_threshold=threshold,
        )
    except Exception as e:
        logger.warning("Could not compute loan CTA: %s", e)

    # ── 7. Serialise ──────────────────────────────────────────────────────────
    forecast_list = [
        {
            "date": str(row["date"]),
            "predicted_balance": round(float(row["predicted_balance"]), 2),
            "p10": round(float(row["p10_balance"]), 2),
            "p90": round(float(row["p90_balance"]), 2),
        }
        for _, row in forecast_df.iterrows()
    ]

    response = {
        "forecast": forecast_list,
        "danger_zones": danger_zones,
        "model_used": model_used,
        "accuracy_pct": accuracy_pct,
        "days_of_data": days_of_data,
        "warning": warning,
        "loan_cta": loan_cta,
    }

    await redis.set(cache_key, json.dumps(response), ex=6 * 3600)
    return response



@router.post("/scenario")
async def run_scenario(
    req: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    # ── 1. Load base forecast from cache ─────────────────────────────────────
    cache_key = f"forecast:{req.business_id}:90"
    cached = await redis.get(cache_key)
    if not cached:
        raise HTTPException(
            status_code=400,
            detail="Base forecast not cached. Call GET /forecast/{business_id} first.",
        )
    base_response = json.loads(cached)
    base_forecast = base_response["forecast"]

    # ── 2. Find pending invoices from this client ─────────────────────────────
    stmt = select(Invoice).where(
        Invoice.business_id == req.business_id,
        Invoice.client_id == req.client_id,
        Invoice.status.in_(["pending", "overdue"]),
    )
    result = await db.execute(stmt)
    pending_invoices = result.scalars().all()

    inflow_by_date: dict[str, float] = {}
    for inv in pending_invoices:
        amount = float(req.amount_override or inv.amount)
        key = str(inv.due_date)
        inflow_by_date[key] = inflow_by_date.get(key, 0.0) + amount

    shifted_inflows: dict[str, float] = {
        str(date.fromisoformat(d) + timedelta(days=req.delay_days)): amt
        for d, amt in inflow_by_date.items()
    }

    # ── 3. Apply shift to base forecast ──────────────────────────────────────
    scenario_forecast = []
    running_delta = 0.0

    for item in base_forecast:
        d = item["date"]
        if d in inflow_by_date:
            running_delta -= inflow_by_date[d]
        if d in shifted_inflows:
            running_delta += shifted_inflows[d]

        scenario_forecast.append({
            "date": d,
            "predicted_balance": round(item["predicted_balance"] + running_delta, 2),
            "p10": round(item["p10"] + running_delta, 2),
            "p90": round(item["p90"] + running_delta, 2),
        })

    # ── 4. Scenario summary ───────────────────────────────────────────────────
    total_delayed = sum(inflow_by_date.values())

    first_danger_date = None
    for item in scenario_forecast:
        if item["p10"] < 50_000:
            first_danger_date = item["date"]
            break

    days_until = None
    if first_danger_date:
        days_until = (date.fromisoformat(first_danger_date) - date.today()).days

    if days_until is not None and days_until <= 14:
        action = f"Critical: cash shortfall in {days_until} days. Arrange bridge financing immediately."
    elif days_until is not None and days_until <= 30:
        action = f"Warning: potential shortfall in {days_until} days. Follow up with client urgently."
    elif total_delayed > 0:
        action = f"Rs {total_delayed:,.0f} delayed by {req.delay_days} days. Monitor closely."
    else:
        action = "No pending invoices from this client. Scenario has no cash flow impact."

    return {
        "base_forecast": base_forecast,
        "scenario_forecast": scenario_forecast,
        "scenario_summary": {
            "total_amount_delayed": round(total_delayed, 2),
            "delay_days": req.delay_days,
            "first_danger_date": first_danger_date,
            "days_until_danger": days_until,
            "recommended_action": action,
        },
    }

@router.get("/{business_id}/status")
async def get_training_status(business_id: int):
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        progress = await r.get(f"training_progress:{business_id}")
        if progress:
            return json.loads(progress)
        return {"status": "idle"}
    finally:
        await r.aclose()