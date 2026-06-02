"""
Loan CTA Engine — Day 17
=========================
Computes the contextual loan call-to-action payload that gets injected
into the GET /api/forecast/{business_id} response.

Trigger conditions (both must be true):
  1. A danger zone exists within the next 60 days
  2. Business vintage > 6 months (enough data to trust the features)

Lender recommendation logic (CIBIL-based):
  CIBIL > 700  -> PSU Bank
  CIBIL > 650  -> Private Bank
  CIBIL > 550  -> NBFC
  else         -> MFI
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional


# Days ahead within which a danger zone triggers the CTA
CTA_DANGER_WINDOW_DAYS = 60

# Minimum business vintage (months) to show the CTA
CTA_MIN_VINTAGE_MONTHS = 6

LENDER_DISPLAY = {
    "psu":     "PSU Bank",
    "private": "Private Bank",
    "nbfc":    "NBFC",
    "mfi":     "Microfinance (MFI)",
}


def _infer_lender(cibil_score: float) -> str:
    if cibil_score > 700:
        return "psu"
    elif cibil_score > 650:
        return "private"
    elif cibil_score > 550:
        return "nbfc"
    return "mfi"


def _format_inr(amount: float) -> str:
    """Format an INR amount as 'Rs X.XL' (lakhs) or 'Rs X,XXX'."""
    if amount >= 100_000:
        return f"Rs {amount / 100_000:.1f}L"
    return f"Rs {amount:,.0f}"


def compute_loan_cta(
    danger_zones: List[Dict],
    vintage_years: float,
    cibil_score: float,
    operating_threshold: float,
) -> Optional[Dict]:
    """
    Build the loan_cta payload for the forecast response.

    Args:
        danger_zones:        Output of _compute_danger_zones() in forecast.py
        vintage_years:       Business age in years
        cibil_score:         Estimated CIBIL (from loan features extractor)
        operating_threshold: Monthly operating cost (used for shortfall magnitude)

    Returns:
        A dict with CTA fields, or None if conditions are not met.
    """
    # -- Guard 1: business must have enough history ----------------------------
    if vintage_years < (CTA_MIN_VINTAGE_MONTHS / 12):
        return None

    # -- Guard 2: there must be a danger zone within the window ---------------
    today = date.today()
    cutoff = today + timedelta(days=CTA_DANGER_WINDOW_DAYS)

    first_zone = None
    for zone in danger_zones:
        zone_start = date.fromisoformat(zone["start_date"])
        if zone_start <= cutoff:
            first_zone = zone
            break

    if first_zone is None:
        return None

    # -- Build payload ---------------------------------------------------------
    shortfall_date = date.fromisoformat(first_zone["start_date"])
    days_until = (shortfall_date - today).days
    days_until = max(0, days_until)

    # Shortfall magnitude: how much below the threshold
    min_balance = first_zone.get("min_balance", 0.0)
    shortfall_inr = max(0.0, operating_threshold - min_balance)

    recommended_lender = _infer_lender(cibil_score)
    lender_display = LENDER_DISPLAY[recommended_lender]
    shortfall_str = _format_inr(shortfall_inr)

    message = (
        f"A cash shortfall of {shortfall_str} is projected in "
        f"{days_until} day{'s' if days_until != 1 else ''}. "
        f"See your loan options with {lender_display}."
    )

    return {
        "show": True,
        "message": message,
        "projected_shortfall_inr": round(shortfall_inr, 2),
        "shortfall_date": str(shortfall_date),
        "days_until_shortfall": days_until,
        "recommended_lender": recommended_lender,
        "recommended_lender_display": lender_display,
        "severity": first_zone.get("severity", "medium"),
    }
