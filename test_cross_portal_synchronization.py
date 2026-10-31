import urllib.request
import urllib.error
import json
import sqlite3
import datetime
import random
import sys

BASE_URL = "http://localhost:8001"
results = []

def record(step_id, name, expected, actual, status, evidence=""):
    results.append({
        "step": step_id,
        "name": name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "evidence": str(evidence)[:300]
    })
    print(f"[{status}] {step_id}: {name} -> {actual}")

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
            except Exception:
                parsed = raw
            return res.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

print("\n" + "=" * 80)
print("STARTING CROSS-PORTAL DATA SYNCHRONIZATION INTEGRATION TEST SUITE")
print("=" * 80 + "\n")

rand = random.randint(10000, 99999)

# ------------------------------------------------------------------------------
# STEP 1: Register and authenticate a restaurant
# ------------------------------------------------------------------------------
rest_email = f"sync_rest_{rand}@jaipur-pilot.in"
rest_reg = {
    "email": rest_email,
    "phone": f"+9198{random.randint(100000, 999999)}",
    "password": "SecurePassword123!",
    "full_name": "Jaipur Maharaja Banquet Hall",
    "role": "donor",
    "business_or_org_name": "Maharaja Banquets & Catering",
    "fssai_number": f"122240260{rand}",
    "address": "MI Road, C-Scheme, Jaipur"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", rest_reg)
if code == 200 and body.get("access_token"):
    rest_token = body["access_token"]
    rest_user_id = body["user"]["id"]
    record("STEP 1", "Register & Authenticate Restaurant", "HTTP 200 & JWT", f"Authenticated as {rest_email} (User ID #{rest_user_id})", "PASS")
else:
    record("STEP 1", "Register & Authenticate Restaurant", "HTTP 200 & JWT", f"HTTP {code}: {body}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 2: Restaurant creates a donation containing 50 portions
# ------------------------------------------------------------------------------
now = datetime.datetime.utcnow()
donation_payload = {
    "food_name": f"Royal Paneer Tikka Masala Feast #{rand}",
    "food_category": "Cooked meals",
    "is_vegetarian": True,
    "quantity_kg": 20.0,
    "estimated_servings": 50,
    "preparation_time": now.isoformat() + "Z",
    "expiry_time": (now + datetime.timedelta(hours=6)).isoformat() + "Z",
    "storage_conditions": "Hot Insulated Container (>60°C)",
    "current_temperature": 64.5,
    "allergen_info": "Dairy (Paneer, Pure Ghee)",
    "ingredients": "Cottage cheese, tomatoes, capsicum, cream, spices",
    "pickup_address": "Maharaja Banquets, MI Road, Jaipur",
    "pickup_lat": 26.9180,
    "pickup_lng": 75.8010,
    "pickup_window_start": now.isoformat() + "Z",
    "pickup_window_end": (now + datetime.timedelta(hours=3)).isoformat() + "Z",
    "special_instructions": "Insulated gastro pack. Ready for vehicle pickup.",
    "image_urls": ["https://images.unsplash.com/photo-1546069901-ba9599a7e63c"]
}
code, body = http_call(f"{BASE_URL}/api/rescue/listings", "POST", donation_payload, headers={"Authorization": f"Bearer {rest_token}"})
new_listing_id = body.get("listing_id") if isinstance(body, dict) else None
if code == 200 and new_listing_id and body.get("food_status") == "available":
    record("STEP 2", "Restaurant Creates 50-Portion Donation", "HTTP 200 & status='available'", f"Created listing #{new_listing_id} with status='{body.get('food_status')}'", "PASS")
else:
    record("STEP 2", "Restaurant Creates 50-Portion Donation", "HTTP 200 & status='available'", f"HTTP {code}: {body}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 3: Verify record exists in shared SQLite database
# ------------------------------------------------------------------------------
conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT id, food_name, estimated_servings, status, donor_id FROM food_listings WHERE id = ?", (new_listing_id,))
row = cur.fetchone()
conn.close()
if row and row[0] == new_listing_id and row[2] == 50 and row[3] == "available":
    record("STEP 3", "Database Persistence Verification", "Row in food_listings with 50 servings & 'available'", f"Found in SQLite: ID={row[0]}, Name='{row[1]}', Servings={row[2]}, Status='{row[3]}'", "PASS")
else:
    record("STEP 3", "Database Persistence Verification", "Row in DB", f"DB row: {row}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 4: Authenticate an NGO
# ------------------------------------------------------------------------------
ngo_email = f"sync_ngo_{rand}@jaipur-relief.org"
ngo_reg = {
    "email": ngo_email,
    "phone": f"+9197{random.randint(100000, 999999)}",
    "password": "SecurePassword123!",
    "full_name": "Pratham Relief Society Jaipur",
    "role": "ngo",
    "business_or_org_name": "Pratham Food Relief Sansthan",
    "capacity_meals_per_day": 300,
    "address": "Bapu Nagar Community Kitchen, Jaipur"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", ngo_reg)
if code == 200 and body.get("access_token"):
    ngo_token = body["access_token"]
    ngo_user_id = body["user"]["id"]
    record("STEP 4", "Register & Authenticate NGO", "HTTP 200 & JWT", f"Authenticated as {ngo_email} (User ID #{ngo_user_id})", "PASS")
else:
    record("STEP 4", "Register & Authenticate NGO", "HTTP 200", f"HTTP {code}: {body}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 5: Fetch Available Donations as NGO
# ------------------------------------------------------------------------------
code, listings = http_call(f"{BASE_URL}/api/rescue/listings?status_filter=available", "GET", headers={"Authorization": f"Bearer {ngo_token}"})
matched_listing = next((l for l in listings if l["id"] == new_listing_id), None) if isinstance(listings, list) else None
if code == 200 and matched_listing and matched_listing["estimated_servings"] == 50:
    record("STEP 5", "NGO Discovers Newly Created Donation", "Listing #{new_listing_id} with 50 portions in feed", f"Found donation #{new_listing_id} ('{matched_listing['food_name']}') with {matched_listing['estimated_servings']} portions", "PASS")
else:
    record("STEP 5", "NGO Discovers Newly Created Donation", "Listing present", f"HTTP {code}, Matched: {matched_listing}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 6: NGO claims 30 portions out of 50
# ------------------------------------------------------------------------------
claim_payload = {
    "listing_id": new_listing_id,
    "claimed_servings": 30,
    "notes": "Night Shelter Distribution (Jaipur)"
}
code, claim_res = http_call(f"{BASE_URL}/api/matching/claim", "POST", claim_payload, headers={"Authorization": f"Bearer {ngo_token}"})
claim_id = claim_res.get("claim_id") if isinstance(claim_res, dict) else None
delivery_id = claim_res.get("delivery_id") if isinstance(claim_res, dict) else None
pickup_otp = claim_res.get("pickup_otp") if isinstance(claim_res, dict) else None
delivery_otp = claim_res.get("delivery_otp") if isinstance(claim_res, dict) else None

# Check database for portion decrement (50 original, 30 claimed, 20 remaining)
conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT estimated_servings, status FROM food_listings WHERE id = ?", (new_listing_id,))
listing_state = cur.fetchone()
cur.execute("SELECT claimed_servings, claim_status FROM donation_claims WHERE id = ?", (claim_id,))
claim_state = cur.fetchone()
conn.close()

if code == 200 and listing_state and listing_state[0] == 20 and claim_state and claim_state[0] == 30:
    record("STEP 6", "NGO Claims 30 Portions (Inventory Decrement)", "DB: 30 claimed, 20 remaining, status='available'", f"Claim #{claim_id} for 30 portions confirmed. Remaining in DB: {listing_state[0]} portions (status='{listing_state[1]}')", "PASS")
else:
    record("STEP 6", "NGO Claims 30 Portions (Inventory Decrement)", "DB reflects: 20 remaining, 30 claimed", f"Listing DB: {listing_state}, Claim DB: {claim_state}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 7: Authenticate a Volunteer
# ------------------------------------------------------------------------------
vol_email = f"sync_vol_{rand}@jaipur-dispatch.in"
vol_reg = {
    "email": vol_email,
    "phone": f"+9196{random.randint(100000, 999999)}",
    "password": "SecurePassword123!",
    "full_name": "Vikram Choudhary (Bike Courier)",
    "role": "volunteer",
    "vehicle_type": "bike",
    "address": "MI Road & C-Scheme"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", vol_reg)
if code == 200 and body.get("access_token"):
    vol_token = body["access_token"]
    vol_user_id = body["user"]["id"]
    record("STEP 7", "Register & Authenticate Volunteer", "HTTP 200 & JWT", f"Authenticated as {vol_email} (User ID #{vol_user_id})", "PASS")
else:
    record("STEP 7", "Register & Authenticate Volunteer", "HTTP 200", f"HTTP {code}: {body}", "FAIL")
    sys.exit(1)

# ------------------------------------------------------------------------------
# STEP 8: Assign Volunteer to Delivery Task
# ------------------------------------------------------------------------------
code, accept_res = http_call(f"{BASE_URL}/api/logistics/accept/{delivery_id}", "POST", headers={"Authorization": f"Bearer {vol_token}"})
if code == 200 and accept_res.get("status") == "success":
    record("STEP 8", "Volunteer Accepts Delivery Task", "HTTP 200 & status='in_progress'", f"Delivery #{delivery_id} accepted by volunteer (Status: {accept_res.get('new_status')})", "PASS")
else:
    record("STEP 8", "Volunteer Accepts Delivery Task", "HTTP 200", f"HTTP {code}: {accept_res}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 9: Confirm Pickup Using Authorized Donor Handoff Process
# ------------------------------------------------------------------------------
pickup_verify_payload = {
    "delivery_id": delivery_id,
    "otp": pickup_otp,
    "temperature_reading": 63.8
}
code, pickup_res = http_call(f"{BASE_URL}/api/logistics/confirm-pickup", "POST", pickup_verify_payload, headers={"Authorization": f"Bearer {vol_token}"})
if code == 200 and pickup_res.get("status") in ("picked_up", "success"):
    record("STEP 9", "Donor Handoff: Pickup Verification via OTP", "HTTP 200 & status='picked_up'", f"Verified with OTP {pickup_otp} at 63.8°C: {pickup_res.get('message')}", "PASS")
else:
    record("STEP 9", "Donor Handoff: Pickup Verification via OTP", "HTTP 200", f"HTTP {code}: {pickup_res}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 10: Confirm Delivery Using Authorized NGO Handoff Process
# ------------------------------------------------------------------------------
delivery_verify_payload = {
    "delivery_id": delivery_id,
    "otp": delivery_otp,
    "temperature_reading": 61.5
}
code, del_res = http_call(f"{BASE_URL}/api/logistics/confirm-delivery", "POST", delivery_verify_payload, headers={"Authorization": f"Bearer {vol_token}"})
if code == 200 and del_res.get("status") in ("delivered", "success"):
    record("STEP 10", "NGO Handoff: Delivery Verification via OTP", "HTTP 200 & status='delivered'", f"Verified with OTP {delivery_otp} at 61.5°C: {del_res.get('message')}", "PASS")
else:
    record("STEP 10", "NGO Handoff: Delivery Verification via OTP", "HTTP 200", f"HTTP {code}: {del_res}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 11: Cross-Portal Verification in All Dashboards
# ------------------------------------------------------------------------------
# 11A. Restaurant sees claim and delivery completed
code, rest_claims = http_call(f"{BASE_URL}/api/matching/claims", "GET", headers={"Authorization": f"Bearer {rest_token}"})
rest_has_completed_claim = any(c["id"] == claim_id and c["delivery"]["status"] == "delivered" for c in rest_claims) if isinstance(rest_claims, list) else False

# 11B. NGO sees claim completed in distribution records
code, ngo_claims = http_call(f"{BASE_URL}/api/matching/claims", "GET", headers={"Authorization": f"Bearer {ngo_token}"})
ngo_has_completed_claim = any(c["id"] == claim_id and c["claim_status"] == "completed" for c in ngo_claims) if isinstance(ngo_claims, list) else False

# 11C. Volunteer sees completed delivery in history
code, vol_history = http_call(f"{BASE_URL}/api/logistics/history", "GET", headers={"Authorization": f"Bearer {vol_token}"})
vol_has_history = any(h["delivery_id"] == delivery_id and h["status"] == "delivered" for h in vol_history) if isinstance(vol_history, list) else False

# 11D. Admin live metrics include rescued food
code, admin_login = http_call(f"{BASE_URL}/api/auth/login", "POST", {"email": "admin@jaipur-demo.in", "password": "password123"})
admin_token = admin_login["access_token"]
code, impact = http_call(f"{BASE_URL}/api/impact/metrics", "GET", headers={"Authorization": f"Bearer {admin_token}"})
admin_metrics_ok = "total_food_rescued_kg" in impact and impact["total_meals_redistributed"] > 0

if rest_has_completed_claim and ngo_has_completed_claim and vol_has_history and admin_metrics_ok:
    record("STEP 11", "Complete Cross-Portal Multi-Role Synchronization", "Synchronized in Restaurant, NGO, Volunteer & Admin", "Verified across all 4 role portals simultaneously", "PASS")
else:
    record("STEP 11", "Complete Cross-Portal Multi-Role Synchronization", "Synchronized everywhere", f"Rest: {rest_has_completed_claim}, NGO: {ngo_has_completed_claim}, Vol: {vol_has_history}, Admin: {admin_metrics_ok}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 12: Security Isolation & Boundary Validations
# ------------------------------------------------------------------------------
# 12A. Unrelated NGO cannot access private claims of another NGO
other_ngo_email = f"unrelated_ngo_{rand}@jaipur.in"
code, other_reg = http_call(f"{BASE_URL}/api/auth/register", "POST", {
    "email": other_ngo_email,
    "phone": f"+9195{random.randint(100000, 999999)}",
    "password": "Password123!",
    "full_name": "Unrelated NGO",
    "role": "ngo",
    "business_or_org_name": "Unrelated Trust",
    "address": "Jaipur"
})
other_ngo_token = other_reg["access_token"]
code, other_claims = http_call(f"{BASE_URL}/api/matching/claims", "GET", headers={"Authorization": f"Bearer {other_ngo_token}"})
other_cannot_see_private = not any(c["id"] == claim_id for c in other_claims) if isinstance(other_claims, list) else True
if other_cannot_see_private:
    record("STEP 12A", "Security: Unrelated NGO Privacy", "Cannot access other NGO's claims", "Isolated. Zero foreign claims exposed.", "PASS")
else:
    record("STEP 12A", "Security: Unrelated NGO Privacy", "Private claims hidden", "Foreign claims leaked!", "FAIL")

# 12B. Unrelated Restaurant cannot modify another donor's listings
other_rest_email = f"unrelated_rest_{rand}@jaipur.in"
code, other_rest_reg = http_call(f"{BASE_URL}/api/auth/register", "POST", {
    "email": other_rest_email,
    "phone": f"+9194{random.randint(100000, 999999)}",
    "password": "Password123!",
    "full_name": "Competitor Restaurant",
    "role": "donor",
    "business_or_org_name": "Competitor Foods",
    "address": "Jaipur"
})
other_rest_token = other_rest_reg["access_token"]
malicious_payload = donation_payload.copy()
malicious_payload["food_name"] = "Hacked Listing Name by Competitor"
code, mod_res = http_call(f"{BASE_URL}/api/rescue/listings/{new_listing_id}", "PUT", malicious_payload, headers={"Authorization": f"Bearer {other_rest_token}"})
if code == 403:
    record("STEP 12B", "Security: Foreign Restaurant Modification Blocked", "HTTP 403 Forbidden", f"HTTP {code}: {mod_res.get('detail')}", "PASS")
else:
    record("STEP 12B", "Security: Foreign Restaurant Modification Blocked", "HTTP 403", f"HTTP {code}: {mod_res}", "FAIL")

# 12C. Oversubscription Rejection (Claiming more than remaining 20 portions)
code, oversub_res = http_call(f"{BASE_URL}/api/matching/claim", "POST", {
    "listing_id": new_listing_id,
    "claimed_servings": 500,  # Only 20 remaining
    "notes": "Oversubscription test"
}, headers={"Authorization": f"Bearer {ngo_token}"})
if code in (400, 422):
    record("STEP 12C", "Business Rule: Prevent Oversubscription", "HTTP 400 Bad Request", f"HTTP {code}: {oversub_res.get('detail')}", "PASS")
else:
    record("STEP 12C", "Business Rule: Prevent Oversubscription", "HTTP 400", f"HTTP {code}", "FAIL")

# ------------------------------------------------------------------------------
# STEP 13: Database Durability & Persistence Across Queries
# ------------------------------------------------------------------------------
conn = sqlite3.connect("backend/anndaan.db")
cur = conn.cursor()
cur.execute("SELECT status, estimated_servings FROM food_listings WHERE id = ?", (new_listing_id,))
final_listing = cur.fetchone()
cur.execute("SELECT claim_status FROM donation_claims WHERE id = ?", (claim_id,))
final_claim = cur.fetchone()
cur.execute("SELECT status FROM deliveries WHERE id = ?", (delivery_id,))
final_delivery = cur.fetchone()
conn.close()

if final_listing and final_claim and final_claim[0] == "completed" and final_delivery and final_delivery[0] == "delivered":
    record("STEP 13", "SQLite Durability Verification", "All states persistent in SQLite tables", f"Listing: {final_listing}, Claim: {final_claim}, Delivery: {final_delivery}", "PASS")
else:
    record("STEP 13", "SQLite Durability Verification", "Persistent records in SQLite", f"States: {final_listing}, {final_claim}, {final_delivery}", "FAIL")

# ==============================================================================
# SUMMARY
# ==============================================================================
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print("\n" + "=" * 80)
print(f"CROSS-PORTAL SYNCHRONIZATION TEST SUMMARY: {total} executed, {passed} PASSED, {failed} FAILED")
print("=" * 80)

with open("cross_portal_synchronization_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results
    }, f, indent=2)

if failed > 0:
    sys.exit(1)
sys.exit(0)
