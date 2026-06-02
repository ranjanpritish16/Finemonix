"""
Loan Feature Extractor
======================
Derives the 9 loan eligibility features from a business's existing DB data.
No manual input required — everything is computed from transactions, invoices,
and the business record itself.

Features extracted:
  1. cibil_score           — estimated from payment delay history (300–900)
  2. debt_to_income_ratio  — monthly obligations / avg monthly revenue
  3. business_vintage_years — (today - first_transaction_date) / 365
  4. client_concentration_pct — revenue share of single largest client
  5. revenue_stability     — CV of last 12 months monthly revenue (lower = better)
  6. cash_flow_coverage    — avg monthly cash_in / avg monthly cash_out
  7. gst_compliance_score  — % of months with regular inflows (proxy for GST filing)
  8. monthly_revenue_inr   — last 3 months avg monthly inflow (in INR, not lakhs)
  9. outstanding_loans_inr — estimated from recurring large outflows (loan EMI proxy)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Business, Client, Invoice, Transaction

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CIBIL_MAX_DELAY_DAYS = 90          # 90+ days late → minimum CIBIL score
CIBIL_MIN = 300
CIBIL_MAX = 900
EMI_DETECTION_AMOUNT_MIN = 5_000   # recurring outflow >= ₹5k = possible EMI
EMI_WINDOW_DAYS_LOW = 27
EMI_WINDOW_DAYS_HIGH = 33


# ── Main extractor ────────────────────────────────────────────────────────────

def extract_loan_features(
    db: Session,
    business_id: int,
) -> Dict[str, float]:
    """
    Extract all 9 loan features from DB for a given business.
    Returns a dict keyed by feature name, values are raw floats.
    Also returns metadata about data quality.
    """

    # ── Load raw data ──────────────────────────────────────────────────────────
    # All transactions
    tx_rows = db.execute(
        select(Transaction).where(Transaction.business_id == business_id)
    ).scalars().all()

    # All invoices
    inv_rows = db.execute(
        select(Invoice).where(Invoice.business_id == business_id)
    ).scalars().all()

    # All clients
    client_rows = db.execute(
        select(Client).where(Client.business_id == business_id)
    ).scalars().all()

    # Opening balance
    opening_balance = float(
        db.execute(
            select(Business.opening_balance).where(Business.id == business_id)
        ).scalar() or 0.0
    )

    if not tx_rows:
        logger.warning("No transactions found for business %s", business_id)
        return _default_features(), {"missing_fields": ["all"], "data_freshness_days": None}

    # ── Build DataFrames ───────────────────────────────────────────────────────
    tx_df = pd.DataFrame([{
        "date":           tx.date,
        "amount":         float(tx.amount),
        "direction":      tx.direction,
        "category":       tx.category or "",
        "counterparty_id": tx.counterparty_id,
    } for tx in tx_rows])
    tx_df["date"] = pd.to_datetime(tx_df["date"])

    inv_df = pd.DataFrame([{
        "amount":      float(inv.amount),
        "issue_date":  inv.issue_date,
        "due_date":    inv.due_date,
        "paid_date":   inv.paid_date,
        "status":      inv.status,
        "days_overdue": inv.days_overdue or 0,
        "client_id":   inv.client_id,
    } for inv in inv_rows]) if inv_rows else pd.DataFrame()

    client_map = {c.id: c for c in client_rows}

    today = pd.Timestamp(date.today())

    # ── Feature 1: CIBIL score (estimated) ────────────────────────────────────
    # Formula: start at 750 (neutral). Each paid invoice:
    #   on-time or early  → +2 points
    #   1-30 days late    → -5 points
    #   31-60 days late   → -15 points
    #   61-90 days late   → -30 points
    #   90+ days late     → -50 points
    # Clamped to 300–900.
    cibil_score = _estimate_cibil(inv_df)

    # ── Feature 2: Debt-to-income ratio ───────────────────────────────────────
    # Detected EMI-like recurring outflows / avg monthly revenue
    monthly_revenue = _avg_monthly_revenue(tx_df, months=3)
    monthly_emi = _estimate_monthly_emi(tx_df)
    dti = (monthly_emi / monthly_revenue) if monthly_revenue > 0 else 0.5
    dti = float(np.clip(dti, 0.0, 1.0))

    # ── Feature 3: Business vintage (years) ───────────────────────────────────
    first_tx_date = tx_df["date"].min()
    vintage_years = float((today - first_tx_date).days / 365.25)
    vintage_years = max(0.0, round(vintage_years, 2))

    # ── Feature 4: Client concentration % ────────────────────────────────────
    concentration_pct = _client_concentration(tx_df, client_map)

    # ── Feature 5: Revenue stability (CV of monthly revenue) ─────────────────
    revenue_stability = _revenue_stability(tx_df, months=12)

    # ── Feature 6: Cash flow coverage ─────────────────────────────────────────
    avg_in  = _avg_monthly_revenue(tx_df, months=6)
    avg_out = _avg_monthly_outflow(tx_df, months=6)
    cash_flow_coverage = float(avg_in / avg_out) if avg_out > 0 else 2.0
    cash_flow_coverage = float(np.clip(cash_flow_coverage, 0.0, 5.0))

    # ── Feature 7: GST compliance score ───────────────────────────────────────
    # Proxy: % of months in last 12 where business had inflow activity
    # (active businesses file GST regularly)
    gst_compliance_score = _gst_compliance_proxy(tx_df, months=12)

    # ── Feature 8: Monthly revenue INR ────────────────────────────────────────
    monthly_revenue_inr = _avg_monthly_revenue(tx_df, months=3)

    # ── Feature 9: Outstanding loans INR ─────────────────────────────────────
    # Estimated from recurring monthly outflows that look like EMIs
    outstanding_loans_inr = monthly_emi * 24  # assume avg 2-year remaining tenure

    features = {
        "cibil_score":              round(cibil_score, 1),
        "debt_to_income_ratio":     round(dti, 4),
        "business_vintage_years":   round(vintage_years, 2),
        "client_concentration_pct": round(concentration_pct, 2),
        "revenue_stability":        round(revenue_stability, 4),
        "cash_flow_coverage":       round(cash_flow_coverage, 4),
        "gst_compliance_score":     round(gst_compliance_score, 2),
        "monthly_revenue_inr":      round(monthly_revenue_inr, 2),
        "outstanding_loans_inr":    round(outstanding_loans_inr, 2),
    }

    # Data quality metadata
    data_freshness_days = int((today - tx_df["date"].max()).days)
    missing_fields = _detect_missing_fields(features)

    logger.info("Extracted loan features for business %s: %s", business_id, features)

    return features, {
        "data_freshness_days": data_freshness_days,
        "missing_fields": missing_fields,
        "total_transactions": len(tx_df),
        "total_invoices": len(inv_df),
        "vintage_years": vintage_years,
    }


# ── Feature sub-calculators ───────────────────────────────────────────────────

def _estimate_cibil(inv_df: pd.DataFrame) -> float:
    """Estimate CIBIL score from invoice payment history."""
    if inv_df.empty:
        return 650.0  # neutral default when no invoice data

    paid = inv_df[inv_df["status"] == "paid"].copy()
    if paid.empty:
        # Penalise if there are overdue invoices but nothing paid
        overdue_count = len(inv_df[inv_df["status"] == "overdue"])
        return max(CIBIL_MIN, 650.0 - overdue_count * 10)

    score = 750.0
    for _, row in paid.iterrows():
        delay = row["days_overdue"] or 0
        if delay <= 0:
            score += 2
        elif delay <= 30:
            score -= 5
        elif delay <= 60:
            score -= 15
        elif delay <= 90:
            score -= 30
        else:
            score -= 50

    # Also penalise currently overdue invoices
    overdue_count = len(inv_df[inv_df["status"] == "overdue"])
    score -= overdue_count * 20

    return float(np.clip(score, CIBIL_MIN, CIBIL_MAX))


def _avg_monthly_revenue(tx_df: pd.DataFrame, months: int = 3) -> float:
    """Average monthly inflow over last N months."""
    cutoff = pd.Timestamp(date.today()) - pd.DateOffset(months=months)
    recent = tx_df[(tx_df["direction"] == "in") & (tx_df["date"] >= cutoff)]
    if recent.empty:
        return 0.0
    monthly = recent.groupby(recent["date"].dt.to_period("M"))["amount"].sum()
    return float(monthly.mean())


def _avg_monthly_outflow(tx_df: pd.DataFrame, months: int = 6) -> float:
    """Average monthly outflow over last N months."""
    cutoff = pd.Timestamp(date.today()) - pd.DateOffset(months=months)
    recent = tx_df[(tx_df["direction"] == "out") & (tx_df["date"] >= cutoff)]
    if recent.empty:
        return 0.0
    monthly = recent.groupby(recent["date"].dt.to_period("M"))["amount"].sum()
    return float(monthly.mean())


def _estimate_monthly_emi(tx_df: pd.DataFrame) -> float:
    """
    Detect recurring fixed outflows (EMI-like) by finding outflow amounts
    that repeat monthly (27-33 day gap) above ₹5,000.
    Returns total monthly EMI estimate.
    """
    large_out = tx_df[
        (tx_df["direction"] == "out") &
        (tx_df["amount"] >= EMI_DETECTION_AMOUNT_MIN)
    ].sort_values("date")

    if large_out.empty:
        return 0.0

    emi_amounts: List[float] = []

    for category, group in large_out.groupby("category"):
        dates = group["date"].tolist()
        amounts = group["amount"].tolist()
        if len(dates) < 2:
            continue
        for i in range(len(dates) - 1):
            diff = (dates[i + 1] - dates[i]).days
            if EMI_WINDOW_DAYS_LOW <= diff <= EMI_WINDOW_DAYS_HIGH:
                emi_amounts.append(amounts[i])
                break  # count each category once

    return float(sum(emi_amounts))


def _client_concentration(
    tx_df: pd.DataFrame,
    client_map: dict,
) -> float:
    """% of total inflow attributable to the single largest client."""
    inflows = tx_df[tx_df["direction"] == "in"]
    if inflows.empty:
        return 0.0

    total_inflow = inflows["amount"].sum()
    if total_inflow == 0:
        return 0.0

    by_client = inflows.groupby("counterparty_id")["amount"].sum()

    # Ignore rows with no client assigned (NaN counterparty_id)
    by_client = by_client.dropna()

    if by_client.empty:
        return 0.0

    max_client_inflow = by_client.max()
    return float((max_client_inflow / total_inflow) * 100)


def _revenue_stability(tx_df: pd.DataFrame, months: int = 12) -> float:
    """
    Coefficient of variation of monthly revenue over last N months.
    Lower CV = more stable revenue. Clamped to [0, 2].
    """
    cutoff = pd.Timestamp(date.today()) - pd.DateOffset(months=months)
    recent = tx_df[(tx_df["direction"] == "in") & (tx_df["date"] >= cutoff)]
    if recent.empty:
        return 1.0  # high instability default

    monthly = recent.groupby(recent["date"].dt.to_period("M"))["amount"].sum()
    if len(monthly) < 2:
        return 0.5

    cv = float(monthly.std() / monthly.mean()) if monthly.mean() > 0 else 1.0
    return float(np.clip(cv, 0.0, 2.0))


def _gst_compliance_proxy(tx_df: pd.DataFrame, months: int = 12) -> float:
    """
    Proxy for GST compliance: % of months in last N months where
    business had inflow activity. Active businesses file GST regularly.
    Returns score 0-100.
    """
    cutoff = pd.Timestamp(date.today()) - pd.DateOffset(months=months)
    recent = tx_df[(tx_df["direction"] == "in") & (tx_df["date"] >= cutoff)]

    if recent.empty:
        return 50.0

    active_months = recent["date"].dt.to_period("M").nunique()
    score = (active_months / months) * 100
    return float(np.clip(score, 0.0, 100.0))


def _detect_missing_fields(features: Dict[str, float]) -> List[str]:
    """Flag features that are at their default/fallback values."""
    missing = []
    if features["cibil_score"] == 650.0:
        missing.append("cibil_score (no invoice history)")
    if features["client_concentration_pct"] == 0.0:
        missing.append("client_concentration_pct (no client tagging)")
    if features["outstanding_loans_inr"] == 0.0:
        missing.append("outstanding_loans_inr (no recurring outflows detected)")
    return missing


def _default_features() -> Dict[str, float]:
    """Return neutral defaults when no data exists."""
    return {
        "cibil_score":              650.0,
        "debt_to_income_ratio":     0.4,
        "business_vintage_years":   1.0,
        "client_concentration_pct": 30.0,
        "revenue_stability":        0.5,
        "cash_flow_coverage":       1.2,
        "gst_compliance_score":     60.0,
        "monthly_revenue_inr":      0.0,
        "outstanding_loans_inr":    0.0,
    }