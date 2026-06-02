"""
Loan Eligibility API — Day 15
==============================
POST /api/loan/eligibility   — run 4 classifiers + SHAP for a business
GET  /api/loan/prefill/{id}  — return pre-computed features for form pre-fill
GET  /api/loan/status        — health check
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.ml.loan_features import extract_loan_features
from backend.ml.loan_inference import get_loan_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/loan", tags=["Loan"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class EligibilityRequest(BaseModel):
    business_id: int


class LenderScore(BaseModel):
    probability: float
    probability_pct: float
    verdict: str          # 'approved' | 'rejected'
    display_name: str


class ShapAttribution(BaseModel):
    feature_name: str
    display_name: str
    value: float
    shap_value: float
    impact: str           # 'positive' | 'negative'


class ImprovementAction(BaseModel):
    feature: str
    display_name: str
    action: str
    current_value: float
    target_value: float
    direction: str
    projected_improvement_pct: float


class EligibilityResponse(BaseModel):
    lender_scores: Dict[str, LenderScore]
    shap_attributions: List[ShapAttribution]
    top_actions: List[ImprovementAction]
    best_lender: str
    best_lender_display: str
    best_probability_pct: float
    extracted_features: Dict[str, float]
    data_quality: Dict[str, Any]


class PrefillResponse(BaseModel):
    features: Dict[str, float]
    data_freshness_days: Optional[int]
    missing_fields: List[str]
    total_transactions: int
    total_invoices: int


# ── Sync bridge helpers ───────────────────────────────────────────────────────

def _extract_features_sync(sync_session: Session, business_id: int):
    """Sync wrapper for run_sync bridge."""
    return extract_loan_features(sync_session, business_id)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def loan_status():
    """Health check — also confirms models are loaded."""
    service = get_loan_service()
    loaded_lenders = list(service.models.keys())
    return {
        "status": "ok",
        "models_loaded": loaded_lenders,
        "all_models_ready": len(loaded_lenders) == 4,
    }


@router.post("/eligibility", response_model=EligibilityResponse)
async def get_loan_eligibility(
    req: EligibilityRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Compute loan eligibility for a business across 4 lender types.

    Extracts 9 financial features from existing transaction/invoice data,
    runs trained XGBoost classifiers, and returns:
    - Approval probabilities per lender
    - SHAP attribution (which features helped/hurt)
    - Top 3 specific improvement actions

    No manual input required — all features derived from uploaded financial data.
    """
    # ── 1. Extract features from DB ───────────────────────────────────────────
    try:
        features, quality_meta = await db.run_sync(
            _extract_features_sync, req.business_id
        )
    except Exception as e:
        logger.error("Feature extraction failed for business %s: %s", req.business_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Feature extraction failed: {e}"
        )

    if not features or features.get("monthly_revenue_inr", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail="Insufficient transaction data to compute loan eligibility. "
                   "Upload at least 3 months of financial data first."
        )

    # ── 2. Run inference ───────────────────────────────────────────────────────
    try:
        service = get_loan_service()
        result = service.predict(features)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Loan inference failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Model inference failed: {e}"
        )

    # ── 3. Build response ──────────────────────────────────────────────────────
    return EligibilityResponse(
        lender_scores=result["lender_scores"],
        shap_attributions=result["shap_attributions"],
        top_actions=result["top_actions"],
        best_lender=result["best_lender"],
        best_lender_display=result["best_lender_display"],
        best_probability_pct=result["best_probability_pct"],
        extracted_features=features,
        data_quality=quality_meta,
    )


@router.get("/prefill/{business_id}", response_model=PrefillResponse)
async def get_prefill_features(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Return all 9 loan features pre-computed from business data.
    Use this to pre-fill the loan eligibility form on the frontend.
    """
    try:
        features, quality_meta = await db.run_sync(
            _extract_features_sync, business_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feature extraction failed: {e}"
        )

    return PrefillResponse(
        features=features,
        data_freshness_days=quality_meta.get("data_freshness_days"),
        missing_fields=quality_meta.get("missing_fields", []),
        total_transactions=quality_meta.get("total_transactions", 0),
        total_invoices=quality_meta.get("total_invoices", 0),
    )