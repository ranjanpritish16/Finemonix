# backend/services/anomaly_service.py

import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional
from sklearn.ensemble import IsolationForest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.models import AnomalyScore


FINANCIAL_FEATURES = [
    "revenue_growth",        # QoQ revenue change %
    "expense_ratio",         # expenses / revenue
    "receivables_days",      # debtor days
    "payables_days",         # creditor days
    "cash_to_debt",          # cash / total debt
    "promoter_pledge_pct",   # % shares pledged
    "interest_coverage",     # EBIT / interest expense
]


def _severity(z_score: float) -> str:
    """
    Severity band when the quarter HAS crossed at least one absolute
    danger threshold (see _danger_flags). z_score is relative to the
    company's own historical baseline:
        <= -2.0  -> critical  (~bottom 2.5%)
        <= -1.0  -> high      (~bottom 16%)
        <= -0.25 -> medium    (~bottom 40%)
        else     -> low
    """
    if z_score <= -2.0:
        return "critical"
    elif z_score <= -1.0:
        return "high"
    elif z_score <= -0.25:
        return "medium"
    return "low"


def _danger_flags(feature_values: Dict[str, float]) -> List[str]:
    """
    Absolute, business-meaningful red flags — independent of the
    company's own history. These follow standard credit-risk /
    working-capital heuristics:

      revenue_growth < 0          -> revenue contracting
      expense_ratio > 0.85         -> <15% margin left
      receivables_days > 90        -> DSO over a full quarter
      payables_days > 75           -> stretching suppliers / liquidity stress
      cash_to_debt < 0.10          -> <10% cash cover vs total debt
      promoter_pledge_pct > 0.40   -> commonly cited distress/governance flag
      interest_coverage < 1.5      -> struggling to service debt (ICR < 1.5x)

    A quarter with ZERO flags cannot be rated above "low", regardless
    of how statistically unusual it looks relative to the company's
    own (possibly very narrow) history.
    """
    flags = []
    if feature_values.get("revenue_growth", 0.0) < 0:
        flags.append("revenue_growth")
    if feature_values.get("expense_ratio", 0.0) > 0.85:
        flags.append("expense_ratio")
    if feature_values.get("receivables_days", 0.0) > 90:
        flags.append("receivables_days")
    if feature_values.get("payables_days", 0.0) > 75:
        flags.append("payables_days")
    if feature_values.get("cash_to_debt", 1.0) < 0.10:
        flags.append("cash_to_debt")
    if feature_values.get("promoter_pledge_pct", 0.0) > 0.40:
        flags.append("promoter_pledge_pct")
    if feature_values.get("interest_coverage", 99.0) < 1.5:
        flags.append("interest_coverage")
    return flags


def run_isolation_forest(
    quarterly_data: List[Dict[str, float]],
    contamination: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Fit IsolationForest on a company's own quarterly history.
    Each dict in quarterly_data must have keys matching FINANCIAL_FEATURES
    plus a 'quarter' key (e.g. '2023Q3').

    Returns a list of dicts with keys:
        quarter, score_financial, severity, contributing_features
    where contributing_features = {
        "top_deviations": {feature: signed_deviation_from_median, ...},
        "danger_flags": [feature_names_in_absolute_danger_zone, ...]
    }
    """
    if len(quarterly_data) < 4:
        raise ValueError(
            f"Need at least 4 quarters of data, got {len(quarterly_data)}"
        )

    quarters = [d["quarter"] for d in quarterly_data]
    X = np.array(
        [[d.get(f, 0.0) for f in FINANCIAL_FEATURES] for d in quarterly_data],
        dtype=np.float32,
    )

    # Replace NaN/inf with column medians before fitting
    col_medians = np.nanmedian(X, axis=0)
    inds = np.where(~np.isfinite(X))
    X[inds] = np.take(col_medians, inds[1])

    clf = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
    )
    clf.fit(X)
    raw_scores = clf.score_samples(X)   # shape (n_quarters,)

    # Convert to z-scores relative to THIS company's own score distribution.
    mean_score = float(np.mean(raw_scores))
    std_score = float(np.std(raw_scores))
    if std_score < 1e-6:
        z_scores = np.zeros_like(raw_scores)
    else:
        z_scores = (raw_scores - mean_score) / std_score

    results = []
    for i, q in enumerate(quarters):
        feature_values = {
            feat: float(X[i, j]) for j, feat in enumerate(FINANCIAL_FEATURES)
        }
        danger_flags = _danger_flags(feature_values)

        # Contributing features: deviation from median, signed
        deviations = {
            feat: round(float(X[i, j] - col_medians[j]), 4)
            for j, feat in enumerate(FINANCIAL_FEATURES)
        }
        # Top 3 by absolute deviation
        top3 = dict(
            sorted(deviations.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        )

        severity = "low" if not danger_flags else _severity(float(z_scores[i]))

        results.append({
            "quarter": q,
            "score_financial": round(float(raw_scores[i]), 4),
            "severity": severity,
            "contributing_features": {
                "top_deviations": top3,
                "danger_flags": danger_flags,
            },
        })

    return results


async def upsert_anomaly_scores(
    db: AsyncSession,
    company_bse_code: str,
    scored: List[Dict[str, Any]],
) -> None:
    """
    Delete existing scores for this company then bulk-insert fresh ones.
    Simple upsert strategy — safe for demo-scale data.
    """
    await db.execute(
        delete(AnomalyScore).where(
            AnomalyScore.company_bse_code == company_bse_code
        )
    )
    for row in scored:
        db.add(AnomalyScore(
            company_bse_code=company_bse_code,
            quarter=row["quarter"],
            score_financial=row["score_financial"],
            severity=row["severity"],
            contributing_features=row["contributing_features"],
        ))
    await db.commit()


async def get_anomaly_timeline(
    db: AsyncSession,
    company_bse_code: str,
) -> List[Dict[str, Any]]:
    """Fetch stored anomaly scores for a company, ordered by quarter."""
    result = await db.execute(
        select(AnomalyScore)
        .where(AnomalyScore.company_bse_code == company_bse_code)
        .order_by(AnomalyScore.quarter)
    )
    rows = result.scalars().all()
    return [
        {
            "quarter": r.quarter,
            "score_financial": float(r.score_financial or 0),
            "severity": r.severity,
            "contributing_features": r.contributing_features,
        }
        for r in rows
    ]