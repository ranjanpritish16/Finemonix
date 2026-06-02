import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000/api/loan"

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            ms = (time.perf_counter() - t0) * 1000
            return json.loads(resp.read()), ms, resp.status
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        return json.loads(e.read()), ms, e.code

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

# -- Test 1: Prime the cache via eligibility call --------------
section("TEST 1 -- POST /eligibility (primes Redis cache)")
result, ms, status = post("/eligibility", {"business_id": 1})
print(f"  Status : {status}  |  Time: {ms:.0f}ms")
if status == 200:
    scores = result["lender_scores"]
    print(f"  PSU    : {scores['psu']['probability_pct']}%  ({scores['psu']['verdict']})")
    print(f"  Private: {scores['private']['probability_pct']}%  ({scores['private']['verdict']})")
    print(f"  NBFC   : {scores['nbfc']['probability_pct']}%  ({scores['nbfc']['verdict']})")
    print(f"  MFI    : {scores['mfi']['probability_pct']}%  ({scores['mfi']['verdict']})")
    print(f"  Best   : {result['best_lender_display']} @ {result['best_probability_pct']}%")
    print(f"  Top feature: {result['shap_attributions'][0]['display_name']}")
    print(f"  Cache  : [OK] Base data saved to Redis for business_id=1")
else:
    print(f"  ERROR: {result}")

# -- Test 2: What-if -- reduce client concentration -----------
section("TEST 2 -- /whatif: reduce client_concentration_pct -> 20%")
r, ms, s = post("/whatif", {"business_id": 1, "changed_feature": "client_concentration_pct", "new_value": 20.0})
speed = "[OK <100ms]" if ms < 100 else "[WARN >100ms]"
print(f"  Status : {s}  |  Time: {ms:.0f}ms  {speed}")
if s == 200:
    up = r["updated_probabilities"]
    dt = r["delta"]
    print(f"  PSU    : {up['psu']}%  (D {dt['psu']:+.1f}pp)")
    print(f"  Private: {up['private']}%  (D {dt['private']:+.1f}pp)")
    print(f"  NBFC   : {up['nbfc']}%  (D {dt['nbfc']:+.1f}pp)")
    print(f"  MFI    : {up['mfi']}%  (D {dt['mfi']:+.1f}pp)")

# -- Test 3: What-if -- improve CIBIL score -------------------
section("TEST 3 -- /whatif: raise cibil_score -> 750")
r, ms, s = post("/whatif", {"business_id": 1, "changed_feature": "cibil_score", "new_value": 750.0})
speed = "[OK <100ms]" if ms < 100 else "[WARN >100ms]"
print(f"  Status : {s}  |  Time: {ms:.0f}ms  {speed}")
if s == 200:
    up = r["updated_probabilities"]
    dt = r["delta"]
    print(f"  PSU    : {up['psu']}%  (D {dt['psu']:+.1f}pp)")
    print(f"  Private: {up['private']}%  (D {dt['private']:+.1f}pp)")
    print(f"  NBFC   : {up['nbfc']}%  (D {dt['nbfc']:+.1f}pp)")
    print(f"  MFI    : {up['mfi']}%  (D {dt['mfi']:+.1f}pp)")

# -- Test 4: What-if -- reduce debt-to-income ratio -----------
section("TEST 4 -- /whatif: reduce debt_to_income_ratio -> 0.2")
r, ms, s = post("/whatif", {"business_id": 1, "changed_feature": "debt_to_income_ratio", "new_value": 0.2})
speed = "[OK <100ms]" if ms < 100 else "[WARN >100ms]"
print(f"  Status : {s}  |  Time: {ms:.0f}ms  {speed}")
if s == 200:
    up = r["updated_probabilities"]
    dt = r["delta"]
    print(f"  PSU    : {up['psu']}%  (D {dt['psu']:+.1f}pp)")
    print(f"  Private: {up['private']}%  (D {dt['private']:+.1f}pp)")
    print(f"  NBFC   : {up['nbfc']}%  (D {dt['nbfc']:+.1f}pp)")
    print(f"  MFI    : {up['mfi']}%  (D {dt['mfi']:+.1f}pp)")

# -- Test 5: Error case -- unknown business (no cache) --------
section("TEST 5 -- /whatif with unknown business_id (no cache)")
r, ms, s = post("/whatif", {"business_id": 9999, "changed_feature": "cibil_score", "new_value": 750.0})
print(f"  Status : {s}  |  Time: {ms:.0f}ms")
print(f"  Error  : {r.get('detail')}")
print(f"  {'[OK] Correct 400 error' if s == 400 else '[FAIL] Wrong status'}")

# -- Test 6: Error case -- invalid feature name ---------------
section("TEST 6 -- /whatif with invalid feature name")
r, ms, s = post("/whatif", {"business_id": 1, "changed_feature": "fake_feature", "new_value": 50.0})
print(f"  Status : {s}  |  Time: {ms:.0f}ms")
print(f"  Error  : {r.get('detail')}")
print(f"  {'[OK] Correct 400 error' if s == 400 else '[FAIL] Wrong status'}")

print(f"\n{'='*60}")
print("  Day 16 -- What-if Delta Engine: ALL TESTS DONE")
print('='*60)
