import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ml.loan_inference import get_loan_service

def test_whatif():
    service = get_loan_service()
    
    # Fake base data for testing
    features = {
        "cibil_score": 650.0,
        "debt_to_income_ratio": 0.4,
        "business_vintage_years": 3.0,
        "client_concentration_pct": 50.0,
        "revenue_stability": 0.5,
        "cash_flow_coverage": 1.2,
        "gst_compliance_score": 80.0,
        "monthly_revenue_inr": 500000.0,
        "outstanding_loans_inr": 200000.0,
    }
    
    # Run predict to get initial shap and probabilities
    result = service.predict(features)
    
    base_prob = result["raw_probabilities"]
    base_shap = result["raw_shap_by_lender"]
    
    print("Initial probabilities:")
    print(base_prob)
    
    # Run whatif
    whatif_result = service.whatif(
        base_features=features,
        base_probabilities=base_prob,
        base_shap_by_lender=base_shap,
        changed_feature="client_concentration_pct",
        new_value=20.0
    )
    
    print("\nWhatif probabilities (reduced concentration from 50 to 20):")
    print(whatif_result["updated_probabilities"])
    print("Delta:")
    print(whatif_result["delta"])

if __name__ == "__main__":
    test_whatif()
