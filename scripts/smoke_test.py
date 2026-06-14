"""
Full endpoint smoke test — Days 1-18
Checks every route is reachable and returns expected status codes.
"""
import urllib.request
import json, time

BASE = "http://127.0.0.1:8000/api"
BUSINESS_ID = 1
PASS = 0
FAIL = 0

def req(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method,
        headers={"Content-Type": "application/json"} if body else {})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            ms = (time.perf_counter()-t0)*1000
            return resp.status, json.loads(resp.read()), ms
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter()-t0)*1000
        return e.code, {}, ms

def check(label, status, got, expected_statuses, ms, key_check=None):
    global PASS, FAIL
    status_ok = got in expected_statuses
    key_ok = True
    if key_check and status_ok:
        key_ok = all(k in status for k in key_check)
    ok = status_ok and key_ok
    tag = "[PASS]" if ok else "[FAIL]"
    if ok: PASS += 1
    else:   FAIL += 1
    keys_info = ""
    if key_check:
        found = [k for k in key_check if k in status]
        keys_info = f"  keys={len(found)}/{len(key_check)}"
    print(f"  {tag} {label:<48} HTTP {got}  {ms:.0f}ms{keys_info}")

print("\n" + "="*65)
print("  NeevFinance API Smoke Test — All Endpoints (Days 1-18)")
print("="*65)

# ── Auth ──────────────────────────────────────────────────────────
print("\n[AUTH]")
s,b,ms = req("POST","/auth/register",{"email":"smoke@test.com","password":"Test1234","business_name":"Smoke Co"})
check("POST /auth/register", b, s, [200,201,400,409], ms)   # 400/409 if already exists
s,b,ms = req("POST","/auth/login",{"email":"smoke@test.com","password":"Test1234"})
check("POST /auth/login", b, s, [200,400,401], ms, ["access_token"] if s==200 else None)

# ── Health ────────────────────────────────────────────────────────
print("\n[HEALTH]")
s,b,ms = req("GET","/health")
check("GET /health", b, s, [200], ms)

# ── Data Upload ───────────────────────────────────────────────────
print("\n[DATA]")
s,b,ms = req("GET","/data/status")
check("GET /data/status", b, s, [200,404], ms)

# ── Forecast ──────────────────────────────────────────────────────
print("\n[FORECAST]")
s,b,ms = req("GET",f"/forecast/{BUSINESS_ID}?horizon_days=90")
check("GET /forecast/{id}", b, s, [200,404], ms,
      ["forecast","danger_zones","loan_cta"] if s==200 else None)
s,b,ms = req("POST","/forecast/scenario",{"business_id":BUSINESS_ID,"client_id":1,"delay_days":10})
check("POST /forecast/scenario", b, s, [200,400,404], ms)

# ── Loan ──────────────────────────────────────────────────────────
print("\n[LOAN]")
s,b,ms = req("GET","/loan/status")
check("GET /loan/status", b, s, [200], ms, ["all_models_ready"])
s,b,ms = req("POST","/loan/eligibility",{"business_id":BUSINESS_ID})
check("POST /loan/eligibility", b, s, [200,404,500], ms,
      ["lender_scores","shap_attributions","top_actions","loan_cta" if False else "best_lender"] if s==200 else None)
# prime cache first, then whatif
if s == 200:
    s2,b2,ms2 = req("POST","/loan/whatif",{"business_id":BUSINESS_ID,"changed_feature":"cibil_score","new_value":720.0})
    check("POST /loan/whatif (cached)", b2, s2, [200], ms2, ["updated_probabilities","delta"])
else:
    print(f"  [SKIP] POST /loan/whatif   (eligibility returned {s}, skipping)")
s,b,ms = req("GET",f"/loan/prefill/{BUSINESS_ID}")
check("GET /loan/prefill/{id}", b, s, [200,404], ms,
      ["features","data_freshness_days","missing_fields"] if s==200 else None)
# error cases
s,b,ms = req("POST","/loan/whatif",{"business_id":99999,"changed_feature":"cibil_score","new_value":750.0})
check("POST /loan/whatif (no cache -> 400)", b, s, [400], ms)
s,b,ms = req("POST","/loan/whatif",{"business_id":BUSINESS_ID,"changed_feature":"bad_feature","new_value":1.0})
check("POST /loan/whatif (bad feature -> 400)", b, s, [400], ms)

# ── Clients ───────────────────────────────────────────────────────
print("\n[CLIENTS]")
s,b,ms = req("GET",f"/clients/{BUSINESS_ID}/risk")
check("GET /clients/{id}/risk", b, s, [200,404], ms)

# ── Dashboard ─────────────────────────────────────────────────────
print("\n[DASHBOARD]")
s,b,ms = req("GET","/dashboard/status")
check("GET /dashboard/status", b, s, [200], ms)
s,b,ms = req("GET",f"/dashboard/{BUSINESS_ID}")
check("GET /dashboard/{id}", b, s, [200,404,500], ms)

# ── Graph / Watchlist stubs ───────────────────────────────────────
print("\n[STUBS - Phase 4]")
s,b,ms = req("GET","/watchlist/status")
check("GET /watchlist/status", b, s, [200,501,503], ms)
s,b,ms = req("GET","/graph/status")
check("GET /graph/status", b, s, [200,501,503], ms)

# ── Summary ───────────────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{'='*65}")
print(f"  Result: {PASS}/{total} passed  |  {FAIL} failed")
print(f"{'='*65}\n")
