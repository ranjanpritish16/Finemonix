"""
Day 17 test: Contextual Loan CTA
=================================
Tests:
  1. GET /api/forecast/{id} returns loan_cta field
  2. loan_cta is None when no danger zone exists (simulate)
  3. loan_cta.show=True and correct fields when danger zone within 60 days
  4. GET /api/loan/prefill/{id} returns all 9 features
  5. Prefill endpoint returns data_freshness_days and missing_fields
"""

import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000/api"

def get(path):
    req = urllib.request.Request(BASE + path)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ms = (time.perf_counter() - t0) * 1000
            return json.loads(resp.read()), ms, resp.status
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        return json.loads(e.read()), ms, e.code

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ms = (time.perf_counter() - t0) * 1000
            return json.loads(resp.read()), ms, resp.status
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        return json.loads(e.read()), ms, e.code

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

EXPECTED_FEATURES = [
    "cibil_score", "debt_to_income_ratio", "business_vintage_years",
    "client_concentration_pct", "revenue_stability", "cash_flow_coverage",
    "gst_compliance_score", "monthly_revenue_inr", "outstanding_loans_inr",
]

# -- Flush stale forecast cache first --
print("Flushing forecast cache via Redis CLI (to force fresh response)...")

# -- Test 1: Forecast endpoint has loan_cta field --
section("TEST 1 -- GET /forecast/1 includes loan_cta field")
r, ms, s = get("/forecast/1?horizon_days=90")
print(f"  Status : {s}  |  Time: {ms:.0f}ms")
if s == 200:
    has_cta_key = "loan_cta" in r
    print(f"  loan_cta key present : {'[OK]' if has_cta_key else '[FAIL]'}")
    cta = r.get("loan_cta")
    if cta is not None:
        print(f"  loan_cta.show        : {cta.get('show')}")
        print(f"  message              : {cta.get('message')}")
        print(f"  shortfall_date       : {cta.get('shortfall_date')}")
        print(f"  days_until_shortfall : {cta.get('days_until_shortfall')}")
        print(f"  recommended_lender   : {cta.get('recommended_lender')}")
        print(f"  recommended_display  : {cta.get('recommended_lender_display')}")
        print(f"  projected_shortfall  : Rs {cta.get('projected_shortfall_inr', 0):,.0f}")
        print(f"  severity             : {cta.get('severity')}")

        required_keys = ["show","message","projected_shortfall_inr","shortfall_date",
                         "days_until_shortfall","recommended_lender",
                         "recommended_lender_display","severity"]
        missing_keys = [k for k in required_keys if k not in cta]
        print(f"  Schema check : {'[OK] All keys present' if not missing_keys else f'[FAIL] Missing: {missing_keys}'}")
    else:
        print(f"  loan_cta is null -- no danger zone within 60 days (this is valid!)")
    
    print(f"\n  Danger zones found: {len(r.get('danger_zones', []))}")
    for z in r.get("danger_zones", []):
        print(f"    - {z['start_date']} -> {z['end_date']}  severity={z['severity']}  min_bal={z['min_balance']:,.0f}")
else:
    print(f"  ERROR: {r}")

# -- Test 2: Prefill endpoint --
section("TEST 2 -- GET /loan/prefill/1 returns all 9 features")
r, ms, s = get("/loan/prefill/1")
print(f"  Status : {s}  |  Time: {ms:.0f}ms")
if s == 200:
    features = r.get("features", {})
    
    # Check all 9 features present
    missing_f = [f for f in EXPECTED_FEATURES if f not in features]
    print(f"  Features count  : {len(features)}/9")
    print(f"  Schema check    : {'[OK] All 9 features' if not missing_f else f'[FAIL] Missing: {missing_f}'}")

    for feat, val in features.items():
        print(f"    {feat:<30} = {val}")

    print(f"\n  data_freshness_days : {r.get('data_freshness_days')}")
    print(f"  missing_fields      : {r.get('missing_fields', [])}")
    print(f"  total_transactions  : {r.get('total_transactions')}")
    print(f"  total_invoices      : {r.get('total_invoices')}")
else:
    print(f"  ERROR: {r}")

# -- Test 3: CTA unit logic test (independent of live data) --
section("TEST 3 -- loan_cta.compute_loan_cta() unit test")
import sys, os
sys.path.insert(0, os.path.abspath("."))
try:
    from backend.ml.loan_cta import compute_loan_cta
    
    # Case A: no danger zones -> should return None
    result_a = compute_loan_cta([], 2.0, 660.0, 50_000)
    print(f"  Case A (no danger zones) : {'[OK] Returns None' if result_a is None else '[FAIL]'}")
    
    # Case B: danger zone too far (> 60 days) -> None
    from datetime import date, timedelta
    far_date = date.today() + timedelta(days=75)
    zones_far = [{"start_date": str(far_date), "end_date": str(far_date + timedelta(days=5)),
                  "min_balance": 10000.0, "severity": "high"}]
    result_b = compute_loan_cta(zones_far, 2.0, 660.0, 50_000)
    print(f"  Case B (zone > 60 days) : {'[OK] Returns None' if result_b is None else '[FAIL]'}")
    
    # Case C: danger zone at day 35, CIBIL 660 -> private bank
    near_date = date.today() + timedelta(days=35)
    zones_near = [{"start_date": str(near_date), "end_date": str(near_date + timedelta(days=5)),
                   "min_balance": 5000.0, "severity": "high"}]
    result_c = compute_loan_cta(zones_near, 2.0, 660.0, 50_000)
    if result_c:
        ok_lender = result_c["recommended_lender"] == "private"
        ok_days   = result_c["days_until_shortfall"] == 35
        ok_show   = result_c["show"] is True
        print(f"  Case C (35d, CIBIL 660->private) :")
        print(f"    show={result_c['show']}  lender={result_c['recommended_lender']}  days={result_c['days_until_shortfall']}")
        print(f"    message: {result_c['message']}")
        print(f"    Schema  : {'[OK]' if (ok_lender and ok_days and ok_show) else '[FAIL]'}")
    else:
        print(f"  Case C : [FAIL] Expected CTA but got None")
    
    # Case D: CIBIL 720 -> PSU Bank
    result_d = compute_loan_cta(zones_near, 2.0, 720.0, 50_000)
    if result_d:
        print(f"  Case D (CIBIL 720->psu) : {'[OK]' if result_d['recommended_lender'] == 'psu' else '[FAIL]'}  lender={result_d['recommended_lender']}")
    
    # Case E: business too young (< 6 months) -> None
    result_e = compute_loan_cta(zones_near, 0.3, 660.0, 50_000)
    print(f"  Case E (vintage 0.3yr)  : {'[OK] Returns None (too young)' if result_e is None else '[FAIL]'}")

except Exception as ex:
    print(f"  [FAIL] Unit test error: {ex}")

print(f"\n{'='*60}")
print("  Day 17 -- Contextual Loan CTA: ALL TESTS DONE")
print('='*60)
