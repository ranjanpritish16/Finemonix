# backend/services/demo_fixture.py

"""
Synthetic quarterly financial data for watchlist demo.
Used when a company has no real filing data scraped yet.
DHFL: shows a spike in 2018Q3 (matches the known collapse timeline).
Yes Bank: stress visible from 2019Q1.
Infosys: stable baseline (negative control).
"""

from typing import Dict, List

DEMO_COMPANIES: Dict[str, List[Dict]] = {
    "DHFL": [
        {"quarter": "2016Q1", "revenue_growth": 0.18, "expense_ratio": 0.62, "receivables_days": 45, "payables_days": 30, "cash_to_debt": 0.12, "promoter_pledge_pct": 0.20, "interest_coverage": 3.2},
        {"quarter": "2016Q2", "revenue_growth": 0.21, "expense_ratio": 0.61, "receivables_days": 43, "payables_days": 29, "cash_to_debt": 0.13, "promoter_pledge_pct": 0.22, "interest_coverage": 3.4},
        {"quarter": "2016Q3", "revenue_growth": 0.19, "expense_ratio": 0.63, "receivables_days": 46, "payables_days": 31, "cash_to_debt": 0.11, "promoter_pledge_pct": 0.25, "interest_coverage": 3.1},
        {"quarter": "2016Q4", "revenue_growth": 0.22, "expense_ratio": 0.60, "receivables_days": 44, "payables_days": 28, "cash_to_debt": 0.14, "promoter_pledge_pct": 0.28, "interest_coverage": 3.5},
        {"quarter": "2017Q1", "revenue_growth": 0.20, "expense_ratio": 0.62, "receivables_days": 47, "payables_days": 32, "cash_to_debt": 0.10, "promoter_pledge_pct": 0.30, "interest_coverage": 3.0},
        {"quarter": "2017Q2", "revenue_growth": 0.18, "expense_ratio": 0.64, "receivables_days": 50, "payables_days": 33, "cash_to_debt": 0.09, "promoter_pledge_pct": 0.35, "interest_coverage": 2.8},
        {"quarter": "2017Q3", "revenue_growth": 0.15, "expense_ratio": 0.66, "receivables_days": 55, "payables_days": 35, "cash_to_debt": 0.08, "promoter_pledge_pct": 0.40, "interest_coverage": 2.5},
        {"quarter": "2017Q4", "revenue_growth": 0.12, "expense_ratio": 0.68, "receivables_days": 60, "payables_days": 38, "cash_to_debt": 0.07, "promoter_pledge_pct": 0.45, "interest_coverage": 2.2},
        {"quarter": "2018Q1", "revenue_growth": 0.10, "expense_ratio": 0.72, "receivables_days": 68, "payables_days": 42, "cash_to_debt": 0.05, "promoter_pledge_pct": 0.55, "interest_coverage": 1.8},
        {"quarter": "2018Q2", "revenue_growth": 0.06, "expense_ratio": 0.78, "receivables_days": 80, "payables_days": 50, "cash_to_debt": 0.03, "promoter_pledge_pct": 0.65, "interest_coverage": 1.3},
        # Anomaly spike — 2018Q3 (IL&FS crisis trigger)
        {"quarter": "2018Q3", "revenue_growth": -0.15, "expense_ratio": 1.20, "receivables_days": 140, "payables_days": 95, "cash_to_debt": 0.01, "promoter_pledge_pct": 0.92, "interest_coverage": 0.4},
        {"quarter": "2018Q4", "revenue_growth": -0.30, "expense_ratio": 1.45, "receivables_days": 180, "payables_days": 120, "cash_to_debt": 0.005, "promoter_pledge_pct": 0.97, "interest_coverage": 0.1},
    ],
    "YESBANK": [
        {"quarter": "2017Q1", "revenue_growth": 0.25, "expense_ratio": 0.55, "receivables_days": 30, "payables_days": 20, "cash_to_debt": 0.18, "promoter_pledge_pct": 0.10, "interest_coverage": 4.5},
        {"quarter": "2017Q2", "revenue_growth": 0.23, "expense_ratio": 0.56, "receivables_days": 31, "payables_days": 21, "cash_to_debt": 0.17, "promoter_pledge_pct": 0.10, "interest_coverage": 4.3},
        {"quarter": "2017Q3", "revenue_growth": 0.22, "expense_ratio": 0.57, "receivables_days": 32, "payables_days": 22, "cash_to_debt": 0.16, "promoter_pledge_pct": 0.12, "interest_coverage": 4.2},
        {"quarter": "2017Q4", "revenue_growth": 0.20, "expense_ratio": 0.58, "receivables_days": 33, "payables_days": 22, "cash_to_debt": 0.15, "promoter_pledge_pct": 0.12, "interest_coverage": 4.0},
        {"quarter": "2018Q1", "revenue_growth": 0.18, "expense_ratio": 0.60, "receivables_days": 35, "payables_days": 23, "cash_to_debt": 0.14, "promoter_pledge_pct": 0.15, "interest_coverage": 3.8},
        {"quarter": "2018Q2", "revenue_growth": 0.15, "expense_ratio": 0.63, "receivables_days": 38, "payables_days": 25, "cash_to_debt": 0.12, "promoter_pledge_pct": 0.18, "interest_coverage": 3.4},
        {"quarter": "2018Q3", "revenue_growth": 0.10, "expense_ratio": 0.68, "receivables_days": 45, "payables_days": 28, "cash_to_debt": 0.10, "promoter_pledge_pct": 0.22, "interest_coverage": 2.9},
        {"quarter": "2018Q4", "revenue_growth": 0.05, "expense_ratio": 0.75, "receivables_days": 55, "payables_days": 35, "cash_to_debt": 0.07, "promoter_pledge_pct": 0.30, "interest_coverage": 2.2},
        # Stress begins 2019Q1
        {"quarter": "2019Q1", "revenue_growth": -0.08, "expense_ratio": 0.95, "receivables_days": 90, "payables_days": 60, "cash_to_debt": 0.04, "promoter_pledge_pct": 0.48, "interest_coverage": 1.1},
        {"quarter": "2019Q2", "revenue_growth": -0.20, "expense_ratio": 1.15, "receivables_days": 130, "payables_days": 90, "cash_to_debt": 0.02, "promoter_pledge_pct": 0.70, "interest_coverage": 0.5},
    ],
    "INFY": [
        {"quarter": "2021Q1", "revenue_growth": 0.12, "expense_ratio": 0.70, "receivables_days": 65, "payables_days": 40, "cash_to_debt": 0.85, "promoter_pledge_pct": 0.0, "interest_coverage": 25.0},
        {"quarter": "2021Q2", "revenue_growth": 0.14, "expense_ratio": 0.69, "receivables_days": 63, "payables_days": 38, "cash_to_debt": 0.88, "promoter_pledge_pct": 0.0, "interest_coverage": 26.5},
        {"quarter": "2021Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 64, "payables_days": 39, "cash_to_debt": 0.82, "promoter_pledge_pct": 0.0, "interest_coverage": 24.0},
        {"quarter": "2021Q4", "revenue_growth": 0.15, "expense_ratio": 0.68, "receivables_days": 62, "payables_days": 37, "cash_to_debt": 0.90, "promoter_pledge_pct": 0.0, "interest_coverage": 27.0},
        {"quarter": "2022Q1", "revenue_growth": 0.16, "expense_ratio": 0.69, "receivables_days": 61, "payables_days": 38, "cash_to_debt": 0.87, "promoter_pledge_pct": 0.0, "interest_coverage": 25.5},
        {"quarter": "2022Q2", "revenue_growth": 0.14, "expense_ratio": 0.70, "receivables_days": 64, "payables_days": 40, "cash_to_debt": 0.84, "promoter_pledge_pct": 0.0, "interest_coverage": 24.5},
        {"quarter": "2022Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 65, "payables_days": 41, "cash_to_debt": 0.83, "promoter_pledge_pct": 0.0, "interest_coverage": 23.5},
        {"quarter": "2022Q4", "revenue_growth": 0.12, "expense_ratio": 0.72, "receivables_days": 66, "payables_days": 42, "cash_to_debt": 0.80, "promoter_pledge_pct": 0.0, "interest_coverage": 22.0},
    ],
    "IBM": [
        {"quarter": "2021Q1", "revenue_growth": 0.12, "expense_ratio": 0.70, "receivables_days": 65, "payables_days": 40, "cash_to_debt": 0.85, "promoter_pledge_pct": 0.0, "interest_coverage": 25.0},
        {"quarter": "2021Q2", "revenue_growth": 0.14, "expense_ratio": 0.69, "receivables_days": 63, "payables_days": 38, "cash_to_debt": 0.88, "promoter_pledge_pct": 0.0, "interest_coverage": 26.5},
        {"quarter": "2021Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 64, "payables_days": 39, "cash_to_debt": 0.82, "promoter_pledge_pct": 0.0, "interest_coverage": 24.0},
        {"quarter": "2021Q4", "revenue_growth": 0.15, "expense_ratio": 0.68, "receivables_days": 62, "payables_days": 37, "cash_to_debt": 0.90, "promoter_pledge_pct": 0.0, "interest_coverage": 27.0},
        {"quarter": "2022Q1", "revenue_growth": 0.16, "expense_ratio": 0.69, "receivables_days": 61, "payables_days": 38, "cash_to_debt": 0.87, "promoter_pledge_pct": 0.0, "interest_coverage": 25.5},
        {"quarter": "2022Q2", "revenue_growth": 0.14, "expense_ratio": 0.70, "receivables_days": 64, "payables_days": 40, "cash_to_debt": 0.84, "promoter_pledge_pct": 0.0, "interest_coverage": 24.5},
        {"quarter": "2022Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 65, "payables_days": 41, "cash_to_debt": 0.83, "promoter_pledge_pct": 0.0, "interest_coverage": 23.5},
        {"quarter": "2022Q4", "revenue_growth": 0.12, "expense_ratio": 0.72, "receivables_days": 66, "payables_days": 42, "cash_to_debt": 0.80, "promoter_pledge_pct": 0.0, "interest_coverage": 22.0},
    ],
    "SANITY": [
        {"quarter": "2021Q1", "revenue_growth": 0.12, "expense_ratio": 0.70, "receivables_days": 65, "payables_days": 40, "cash_to_debt": 0.85, "promoter_pledge_pct": 0.0, "interest_coverage": 25.0},
        {"quarter": "2021Q2", "revenue_growth": 0.14, "expense_ratio": 0.69, "receivables_days": 63, "payables_days": 38, "cash_to_debt": 0.88, "promoter_pledge_pct": 0.0, "interest_coverage": 26.5},
        {"quarter": "2021Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 64, "payables_days": 39, "cash_to_debt": 0.82, "promoter_pledge_pct": 0.0, "interest_coverage": 24.0},
        {"quarter": "2021Q4", "revenue_growth": 0.15, "expense_ratio": 0.68, "receivables_days": 62, "payables_days": 37, "cash_to_debt": 0.90, "promoter_pledge_pct": 0.0, "interest_coverage": 27.0},
        {"quarter": "2022Q1", "revenue_growth": 0.16, "expense_ratio": 0.69, "receivables_days": 61, "payables_days": 38, "cash_to_debt": 0.87, "promoter_pledge_pct": 0.0, "interest_coverage": 25.5},
        {"quarter": "2022Q2", "revenue_growth": 0.14, "expense_ratio": 0.70, "receivables_days": 64, "payables_days": 40, "cash_to_debt": 0.84, "promoter_pledge_pct": 0.0, "interest_coverage": 24.5},
        {"quarter": "2022Q3", "revenue_growth": 0.13, "expense_ratio": 0.71, "receivables_days": 65, "payables_days": 41, "cash_to_debt": 0.83, "promoter_pledge_pct": 0.0, "interest_coverage": 23.5},
        {"quarter": "2022Q4", "revenue_growth": 0.12, "expense_ratio": 0.72, "receivables_days": 66, "payables_days": 42, "cash_to_debt": 0.80, "promoter_pledge_pct": 0.0, "interest_coverage": 22.0},
    ],
}


def get_demo_data(bse_code: str) -> List[Dict]:
    """Return demo quarterly data for a known company, or empty list."""
    return DEMO_COMPANIES.get(bse_code.upper(), [])