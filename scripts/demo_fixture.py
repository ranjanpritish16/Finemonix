"""
Day 18 Demo Fixture
====================
Demonstrates the exact pitch sequence from the NeevFinance proposal:
  - Business profile that produces: PSU ~28%, NBFC ~71%
  - Slide client_concentration down → NBFC jumps to ~81%

This is a standalone script (no DB needed) that drives the ML
inference service directly with a hand-crafted profile.

Run:
  python scripts/demo_fixture.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.loan_inference import get_loan_service, LENDER_DISPLAY_NAMES

# ── Demo profile tuned to match the proposal ─────────────────────────────────
# PSU requires CIBIL > 700 — we set it to 680 (just below) to get ~28% PSU
# High client_concentration (60%) hurts NBFC, pulling it to ~71%
DEMO_PROFILE = {
    "cibil_score":              680.0,   # just below PSU threshold (700)
    "debt_to_income_ratio":     0.38,    # moderate leverage
    "business_vintage_years":   4.5,     # established SME
    "client_concentration_pct": 60.0,    # one big client = risk flag
    "revenue_stability":        0.28,    # decent stability
    "cash_flow_coverage":       1.35,    # covers obligations
    "gst_compliance_score":     78.0,    # mostly compliant
    "monthly_revenue_inr":      420_000, # Rs 4.2L/month
    "outstanding_loans_inr":    180_000, # existing EMI
}

def bar(pct: float, width: int = 30) -> str:
    filled = int(pct / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.1f}%"

def print_scores(scores: dict, label: str):
    print(f"\n  {label}")
    for lender in ["psu", "private", "nbfc", "mfi"]:
        s = scores[lender]
        verdict = "APPROVED" if s["probability_pct"] >= 50 else "rejected"
        print(f"    {s['display_name']:<20} {bar(s['probability_pct'])}  [{verdict}]")

def main():
    print("=" * 65)
    print("  NeevFinance Demo — Loan Eligibility Simulator")
    print("=" * 65)

    service = get_loan_service()

    # ── Step 1: Base profile ──────────────────────────────────────────────────
    print("\n[STEP 1] Running base profile through 4 lender models...")
    result = service.predict(DEMO_PROFILE)

    base_scores  = result["lender_scores"]
    base_probs   = result["raw_probabilities"]
    base_shap    = result["raw_shap_by_lender"]

    print_scores(base_scores, "Base Profile Results:")

    psu_pct  = base_scores["psu"]["probability_pct"]
    nbfc_pct = base_scores["nbfc"]["probability_pct"]
    print(f"\n  Key numbers  ->  PSU: {psu_pct:.1f}%  |  NBFC: {nbfc_pct:.1f}%")

    # ── Step 2: Show top SHAP drivers ────────────────────────────────────────
    print("\n[STEP 2] Top 3 factors driving NBFC eligibility (SHAP):")
    for i, attr in enumerate(result["shap_attributions"][:3], 1):
        direction = "+" if attr["impact"] == "positive" else "-"
        print(f"  {i}. {attr['display_name']:<30} SHAP={direction}{abs(attr['shap_value']):.4f}")

    # ── Step 3: Show improvement actions ─────────────────────────────────────
    print("\n[STEP 3] Recommended actions:")
    for action in result["top_actions"]:
        print(f"  * {action['action']}")

    # ── Step 4: What-if — reduce client concentration ────────────────────────
    print("\n[STEP 4] What-if simulator: reducing client_concentration_pct")
    print(f"  Current: {DEMO_PROFILE['client_concentration_pct']:.0f}%  ->  Target: 30%")

    whatif_result = service.whatif(
        base_features=DEMO_PROFILE,
        base_probabilities=base_probs,
        base_shap_by_lender=base_shap,
        changed_feature="client_concentration_pct",
        new_value=30.0,
    )

    print("\n  Updated probabilities:")
    for lender in ["psu", "private", "nbfc", "mfi"]:
        new_pct   = whatif_result["updated_probabilities"][lender]
        delta_pct = whatif_result["delta"][lender]
        sign      = "+" if delta_pct >= 0 else ""
        display   = LENDER_DISPLAY_NAMES[lender]
        print(f"    {display:<20} {bar(new_pct)}  (D {sign}{delta_pct:.1f}pp)")

    new_nbfc = whatif_result["updated_probabilities"]["nbfc"]
    new_psu  = whatif_result["updated_probabilities"]["psu"]
    print(f"\n  Result  ->  PSU: {new_psu:.1f}%  |  NBFC: {new_nbfc:.1f}%")
    print(f"  NBFC improvement: {whatif_result['delta']['nbfc']:+.1f} percentage points")

    # ── Step 5: Verify demo targets ───────────────────────────────────────────
    print("\n[STEP 5] Demo target verification:")
    psu_ok  = 15.0 <= psu_pct <= 45.0    # expect ~28%
    nbfc_ok = 60.0 <= nbfc_pct <= 85.0   # expect ~71%
    nbfc_improved = new_nbfc > nbfc_pct  # NBFC should improve after concentration drop

    print(f"  PSU ~28%   (got {psu_pct:.1f}%)    : {'[OK]' if psu_ok  else '[WARN] out of target range'}")
    print(f"  NBFC ~71%  (got {nbfc_pct:.1f}%)   : {'[OK]' if nbfc_ok else '[WARN] out of target range'}")
    print(f"  NBFC improves after whatif          : {'[OK]' if nbfc_improved else '[WARN]'}")

    print("\n" + "=" * 65)
    print("  Demo fixture complete.")
    print("=" * 65)

if __name__ == "__main__":
    main()
