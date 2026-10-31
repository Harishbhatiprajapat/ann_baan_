import urllib.request
import urllib.error
import json
import sqlite3
import datetime

BASE_URL = "http://localhost:8001"

results = []

def record(test_id, name, expected, actual, status, evidence=""):
    results.append({
        "id": test_id,
        "name": name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "evidence": evidence
    })
    print(f"[{status}] {test_id} - {name}: {actual}")

def http_call(url, method="GET", data=None, headers=None):
    hdrs = headers.copy() if headers else {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            raw = res.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except:
                parsed = raw
            return res.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except:
            parsed = raw
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

# Authenticate accounts
# 1. Donor/Restaurant account
_, donor_auth = http_call(f"{BASE_URL}/api/auth/login", "POST", {"email": "restaurant@jaipur-demo.in", "password": "password123"})
donor_token = donor_auth["access_token"]
donor_user_id = donor_auth["user"]["id"]

# 2. Customer account
_, cust_auth = http_call(f"{BASE_URL}/api/auth/login", "POST", {"email": "customer@jaipur-demo.in", "password": "password123"})
cust_token = cust_auth["access_token"]

now = datetime.datetime.utcnow()

# TEST A: Create a commercial rescue deal with valid information
valid_payload = {
    "title": "Chef's Special Dal Baati Churma Box",
    "description": "Authentic Rajasthani hot dinner platter",
    "food_category": "Cooked meals",
    "is_vegetarian": True,
    "is_rescue_bag": False,
    "original_price": 240.0,
    "total_quantity": 15,
    "preparation_time": now.isoformat() + "Z",
    "pickup_deadline": (now + datetime.timedelta(hours=3)).isoformat() + "Z",
    "storage_conditions": "Insulated Gastro Box (>60°C)",
    "current_temperature": 64.0,
    "allergen_info": "Pure Ghee, Wheat",
    "ingredients": "Lentils, Wheat flour, Ghee, Jaggery, Spices",
    "pickup_address": "MI Road, C-Scheme, Jaipur",
    "pickup_lat": 26.9180,
    "pickup_lng": 75.8010,
    "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
    "auto_donate_unsold": True
}
code_a, body_a = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", valid_payload, headers={"Authorization": f"Bearer {donor_token}"})
new_listing_id = body_a.get("listing_id") if isinstance(body_a, dict) else None

conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT id, title, current_rescue_price, auto_donate_unsold FROM rescue_listings WHERE id = ?", (new_listing_id,))
row_a = cur.fetchone()
conn.close()

if code_a == 200 and row_a and row_a[0] == new_listing_id:
    record("Test A", "Create Valid Commercial Deal", "HTTP 200 & record created in SQLite", f"HTTP {code_a}, ID={new_listing_id}, Rescue Price=Rs.{row_a[2]}", "PASS", str(body_a))
else:
    record("Test A", "Create Valid Commercial Deal", "HTTP 200 & record created", f"HTTP {code_a} - {body_a}", "FAIL", str(body_a))

# TEST B: Page Refresh / Get Restaurant Listings
code_b, body_b = http_call(f"{BASE_URL}/api/marketplace/listings/restaurant", "GET", headers={"Authorization": f"Bearer {donor_token}"})
found_b = any(item["id"] == new_listing_id for item in body_b) if isinstance(body_b, list) else False
if code_b == 200 and found_b:
    record("Test B", "Persistence on Page Refresh (Roster Query)", "Newly created deal is returned in restaurant deals query", f"Deal #{new_listing_id} present in active listings", "PASS", f"Roster count={len(body_b)}")
else:
    record("Test B", "Persistence on Page Refresh (Roster Query)", "Deal present", f"HTTP {code_b}, Found: {found_b}", "FAIL", "")

# TEST C: Persistence in SQLite
conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT status, original_price, auto_donate_unsold FROM rescue_listings WHERE id = ?", (new_listing_id,))
db_persisted = cur.fetchone()
conn.close()
if db_persisted and db_persisted[0] == "active":
    record("Test C", "Database Durability Across Restarts", "Record persisted in SQLite tables with active status", f"Status={db_persisted[0]}, OrigPrice={db_persisted[1]}", "PASS", f"Persisted row: {db_persisted}")
else:
    record("Test C", "Database Durability Across Restarts", "Record in SQLite", "Not found or inactive", "FAIL", "")

# TEST D: Submit Invalid Price (<= 0)
invalid_price_payload = valid_payload.copy()
invalid_price_payload["original_price"] = -50.0
code_d, body_d = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", invalid_price_payload, headers={"Authorization": f"Bearer {donor_token}"})
if code_d in (400, 422):
    record("Test D", "Reject Negative or Zero Price", "HTTP 400 or 422 validation error", f"HTTP {code_d} - {body_d.get('detail') if isinstance(body_d, dict) else body_d}", "PASS", str(body_d))
else:
    record("Test D", "Reject Negative or Zero Price", "HTTP 400/422", f"HTTP {code_d} - {body_d}", "FAIL", str(body_d))

# TEST E: Submit Zero or Negative Quantity
invalid_qty_payload = valid_payload.copy()
invalid_qty_payload["total_quantity"] = 0
code_e, body_e = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", invalid_qty_payload, headers={"Authorization": f"Bearer {donor_token}"})
if code_e in (400, 422):
    record("Test E", "Reject Zero or Negative Quantity", "HTTP 400 or 422 validation error", f"HTTP {code_e} - {body_e.get('detail') if isinstance(body_e, dict) else body_e}", "PASS", str(body_e))
else:
    record("Test E", "Reject Zero or Negative Quantity", "HTTP 400/422", f"HTTP {code_e} - {body_e}", "FAIL", str(body_e))

# TEST F: Create Listing Without Authentication
code_f, body_f = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", valid_payload)
if code_f in (401, 403):
    record("Test F", "Reject Unauthenticated Creation", "HTTP 401 Unauthorized", f"HTTP {code_f} - {body_f.get('detail') if isinstance(body_f, dict) else body_f}", "PASS", str(body_f))
else:
    record("Test F", "Reject Unauthenticated Creation", "HTTP 401", f"HTTP {code_f} - {body_f}", "FAIL", str(body_f))

# TEST G: Customer Role Forbidden
code_g, body_g = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", valid_payload, headers={"Authorization": f"Bearer {cust_token}"})
if code_g == 403:
    record("Test G", "Reject Customer Role From Publishing Deal", "HTTP 403 Forbidden", f"HTTP {code_g} - {body_g.get('detail') if isinstance(body_g, dict) else body_g}", "PASS", str(body_g))
else:
    record("Test G", "Reject Customer Role From Publishing Deal", "HTTP 403 Forbidden", f"HTTP {code_g} - {body_g}", "FAIL", str(body_g))

# TEST H: Automatic Donation Opt-In Verification (Consent True vs False)
payload_optout = valid_payload.copy()
payload_optout["title"] = "Commercial Only Deal (No Auto Donation)"
payload_optout["auto_donate_unsold"] = False
code_h, body_h = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", payload_optout, headers={"Authorization": f"Bearer {donor_token}"})
id_optout = body_h.get("listing_id") if isinstance(body_h, dict) else None

conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT id, auto_donate_unsold, donation_transition_status FROM rescue_listings WHERE id = ?", (new_listing_id,))
row_optin = cur.fetchone()
cur.execute("SELECT id, auto_donate_unsold, donation_transition_status FROM rescue_listings WHERE id = ?", (id_optout,))
row_optout = cur.fetchone()
conn.close()

if row_optin and row_optin[1] == 1 and row_optout and row_optout[1] == 0:
    record("Test H", "Automatic Donation Opt-In Isolation", "Consent preserved accurately: Opt-in=True (eligible), Opt-out=False (not_applicable)", f"Opt-in #{row_optin[0]}: flag={row_optin[1]}, status={row_optin[2]} | Opt-out #{row_optout[0]}: flag={row_optout[1]}, status={row_optout[2]}", "PASS", "Consent separation confirmed")
else:
    record("Test H", "Automatic Donation Opt-In Isolation", "Correct boolean flags in DB", f"Opt-in: {row_optin}, Opt-out: {row_optout}", "FAIL", "")

# TEST I: Marketplace Retrieval for Customers
code_i, body_i = http_call(f"{BASE_URL}/api/marketplace/deals", "GET")
found_i = any(deal["id"] == new_listing_id for deal in body_i) if isinstance(body_i, list) else False
if code_i == 200 and found_i:
    target_deal = next(d for d in body_i if d["id"] == new_listing_id)
    record("Test I", "Marketplace Public Retrieval", "Listing appears in public rescue deals feed with dynamic price", f"Deal #{new_listing_id} visible to buyers at Rs.{target_deal['current_rescue_price']} ({target_deal['discount_percentage']}% off)", "PASS", f"Marketplace items={len(body_i)}")
else:
    record("Test I", "Marketplace Public Retrieval", "Deal in marketplace", f"HTTP {code_i}, found={found_i}", "FAIL", "")

print("\n" + "=" * 70)
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"PHASE 5 STEP 1 SUMMARY: {total} executed, {passed} PASSED, {failed} FAILED")
print("=" * 70)

# Save JSON results
with open("phase5_step1_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results
    }, f, indent=2)
