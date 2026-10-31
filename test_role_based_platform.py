import urllib.request
import urllib.error
import json
import sqlite3
import datetime
import random

BASE_URL = "http://localhost:8001"

results = []

def record(test_id, role, name, expected, actual, status, evidence=""):
    results.append({
        "id": test_id,
        "role": role,
        "name": name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "evidence": str(evidence)[:300]
    })
    print(f"[{status}] {test_id} [{role}] {name}: {actual}")

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

# ==============================================================================
# 1. SECURITY & ADMIN RESTRICTION TESTS
# ==============================================================================
print("\n--- RUNNING SECURITY & AUTH TESTS ---")

# Test 1.1: Public Registration as Admin MUST BE REJECTED (HTTP 403)
rand_num = random.randint(1000, 9999)
admin_reg_payload = {
    "email": f"hacker_admin_{rand_num}@test.in",
    "phone": f"+9198{rand_num}0011",
    "password": "SecretPassword123",
    "full_name": "Fake Admin User",
    "role": "admin"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", admin_reg_payload)
if code == 403:
    record("SEC-1", "Security", "Reject Public Admin Registration", "HTTP 403 Forbidden", f"HTTP {code}: {body.get('detail')}", "PASS", body)
else:
    record("SEC-1", "Security", "Reject Public Admin Registration", "HTTP 403 Forbidden", f"HTTP {code}: {body}", "FAIL", body)

# Test 1.2: Unauthenticated Access to Protected Endpoint
code, body = http_call(f"{BASE_URL}/api/admin/users", "GET")
if code == 401:
    record("SEC-2", "Security", "Reject Unauthenticated Request", "HTTP 401 Unauthorized", f"HTTP {code}: {body.get('detail')}", "PASS", body)
else:
    record("SEC-2", "Security", "Reject Unauthenticated Request", "HTTP 401 Unauthorized", f"HTTP {code}", "FAIL", body)

# ==============================================================================
# 2. CUSTOMER WORKFLOW TESTS
# ==============================================================================
print("\n--- RUNNING CUSTOMER ROLE TESTS ---")

# Test 2.1: Customer Registration with Locality
cust_email = f"customer_{rand_num}@jaipur-test.in"
cust_payload = {
    "email": cust_email,
    "phone": f"+9191{rand_num}2233",
    "password": "password123",
    "full_name": "Divya Rathore",
    "role": "customer",
    "address": "C-Scheme, Jaipur (Near Statue Circle)"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", cust_payload)
cust_token = body.get("access_token") if isinstance(body, dict) else None
if code == 200 and cust_token:
    record("CUST-1", "Customer", "Customer Registration with Locality", "HTTP 200 & JWT Token", f"HTTP 200, Token issued for {body['user']['email']}", "PASS", body)
else:
    record("CUST-1", "Customer", "Customer Registration with Locality", "HTTP 200", f"HTTP {code}: {body}", "FAIL", body)

# Test 2.2: Customer Login
code, body = http_call(f"{BASE_URL}/api/auth/login", "POST", {"email": cust_email, "password": "password123"})
if code == 200 and body.get("access_token"):
    cust_token = body["access_token"]
    record("CUST-2", "Customer", "Customer Authentication", "HTTP 200 & Valid Session", f"HTTP 200, Role: {body['user']['role']}", "PASS")
else:
    record("CUST-2", "Customer", "Customer Authentication", "HTTP 200", f"HTTP {code}", "FAIL")

# Test 2.3: Customer Role Forbidden from Admin Endpoint
code, body = http_call(f"{BASE_URL}/api/admin/overview", "GET", headers={"Authorization": f"Bearer {cust_token}"})
if code == 403:
    record("CUST-3", "Customer", "RBAC: Customer Forbidden from Admin", "HTTP 403 Forbidden", f"HTTP {code}: {body.get('detail')}", "PASS")
else:
    record("CUST-3", "Customer", "RBAC: Customer Forbidden from Admin", "HTTP 403", f"HTTP {code}", "FAIL")

# Test 2.4: Browse Rescue Deals Marketplace
code, deals = http_call(f"{BASE_URL}/api/marketplace/deals", "GET")
if code == 200 and isinstance(deals, list) and len(deals) > 0:
    target_deal = deals[0]
    deal_id = target_deal["id"]
    avail_qty = target_deal["available_quantity"]
    record("CUST-4", "Customer", "Browse Live Rescue Deals", "HTTP 200 & active deals list", f"HTTP 200, Found {len(deals)} deals. Target: #{deal_id} (Stock: {avail_qty})", "PASS")
else:
    record("CUST-4", "Customer", "Browse Live Rescue Deals", "HTTP 200", f"HTTP {code}: {deals}", "FAIL")
    target_deal = None
    deal_id = None
    avail_qty = 0

# Test 2.5: Prevent Overselling (Order quantity > Available stock)
if deal_id:
    excess_qty = avail_qty + 100
    code, body = http_call(f"{BASE_URL}/api/marketplace/orders/create", "POST", {
        "rescue_listing_id": deal_id,
        "quantity": excess_qty,
        "payment_method": "sandbox"
    }, headers={"Authorization": f"Bearer {cust_token}"})
    if code in (400, 422):
        record("CUST-5", "Customer", "Prevent Overselling", "HTTP 400 (exceeds stock)", f"HTTP {code}: {body.get('detail')}", "PASS")
    else:
        record("CUST-5", "Customer", "Prevent Overselling", "HTTP 400", f"HTTP {code}", "FAIL")

# Test 2.6: Create Valid Order & Reserve Inventory
created_order_id = None
if deal_id and avail_qty >= 1:
    code, body = http_call(f"{BASE_URL}/api/marketplace/orders/create", "POST", {
        "rescue_listing_id": deal_id,
        "quantity": 1,
        "payment_method": "sandbox"
    }, headers={"Authorization": f"Bearer {cust_token}"})
    if code == 200 and body.get("order_id"):
        created_order_id = body["order_id"]
        pickup_otp = body.get("pickup_otp")
        record("CUST-6", "Customer", "Order Creation & Inventory Reservation", "HTTP 200, Order Reserved & OTP", f"HTTP 200, Order #{body['order_number']}, OTP: {pickup_otp}", "PASS", body)
    else:
        record("CUST-6", "Customer", "Order Creation & Inventory Reservation", "HTTP 200", f"HTTP {code}: {body}", "FAIL", body)

# Test 2.7: Payment Verification in Sandbox
if created_order_id:
    code, body = http_call(f"{BASE_URL}/api/marketplace/orders/pay", "POST", {
        "order_id": created_order_id,
        "gateway_payment_id": f"pay_sandbox_{rand_num}",
        "gateway_signature": "sig_sandbox_valid"
    }, headers={"Authorization": f"Bearer {cust_token}"})
    if code == 200 and body.get("status") == "success":
        record("CUST-7", "Customer", "Payment Sandbox Verification", "HTTP 200 & Order Ready for Pickup", f"HTTP 200, Status: {body['order_status']}, Amount: Rs.{body['amount_paid']}", "PASS", body)
    else:
        record("CUST-7", "Customer", "Payment Sandbox Verification", "HTTP 200", f"HTTP {code}: {body}", "FAIL", body)

# Test 2.8: Fetch Customer Orders & Tracking
code, body = http_call(f"{BASE_URL}/api/marketplace/orders/customer", "GET", headers={"Authorization": f"Bearer {cust_token}"})
if code == 200 and isinstance(body.get("orders"), list) and any(o["id"] == created_order_id for o in body["orders"]):
    record("CUST-8", "Customer", "Customer Order History & OTP Tracking", "Order present with status 'ready_for_pickup'", f"HTTP 200, Orders count: {len(body['orders'])}, Savings: Rs.{body.get('total_money_saved')}", "PASS")
else:
    record("CUST-8", "Customer", "Customer Order History & OTP Tracking", "Order in list", f"HTTP {code}: {body}", "FAIL")

# ==============================================================================
# 3. RESTAURANT / DONOR WORKFLOW TESTS
# ==============================================================================
print("\n--- RUNNING RESTAURANT / DONOR ROLE TESTS ---")

# Test 3.1: Restaurant Registration with FSSAI & Kitchen Address
rest_email = f"restaurant_{rand_num}@jaipur-test.in"
rest_payload = {
    "email": rest_email,
    "phone": f"+9198{rand_num}4455",
    "password": "password123",
    "full_name": "Royal Treat Banquets",
    "role": "donor",
    "business_or_org_name": "Royal Treat Fine Dining & Banquets",
    "fssai_number": "12224026000999",
    "address": "MI Road, C-Scheme, Jaipur"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", rest_payload)
rest_token = body.get("access_token") if isinstance(body, dict) else None
if code == 200 and rest_token:
    record("REST-1", "Restaurant", "Restaurant Registration with FSSAI & Address", "HTTP 200 & Token", f"HTTP 200, Restaurant profile created with FSSAI: {rest_payload['fssai_number']}", "PASS")
else:
    record("REST-1", "Restaurant", "Restaurant Registration", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# Test 3.2: Create Commercial Deal with Dynamic Pricing
now = datetime.datetime.utcnow()
comm_deal_payload = {
    "title": "Chef Special Biryani & Raita Feast",
    "description": "Authentic dum cooked vegetable biryani box with burani raita",
    "food_category": "Cooked meals",
    "is_vegetarian": True,
    "is_rescue_bag": False,
    "original_price": 280.0,
    "total_quantity": 20,
    "preparation_time": now.isoformat() + "Z",
    "pickup_deadline": (now + datetime.timedelta(hours=4)).isoformat() + "Z",
    "storage_conditions": "Hot Insulated Case (>60°C)",
    "current_temperature": 65.0,
    "allergen_info": "Dairy, Nuts",
    "ingredients": "Basmati rice, Vegetables, Ghee, Saffron, Spices",
    "pickup_address": "MI Road, C-Scheme, Jaipur",
    "pickup_lat": 26.9180,
    "pickup_lng": 75.8010,
    "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8",
    "auto_donate_unsold": True
}
code, body = http_call(f"{BASE_URL}/api/marketplace/listings", "POST", comm_deal_payload, headers={"Authorization": f"Bearer {rest_token}"})
new_deal_id = body.get("listing_id") if isinstance(body, dict) else None
if code == 200 and new_deal_id:
    record("REST-2", "Restaurant", "Create Commercial Rescue Listing", "HTTP 200 & Deal Created", f"HTTP 200, Listing ID #{new_deal_id}, Rescue Price: Rs.{body.get('initial_rescue_price')}", "PASS")
else:
    record("REST-2", "Restaurant", "Create Commercial Rescue Listing", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# Test 3.3: Create Social Donation (Free for NGOs)
soc_donation_payload = {
    "food_name": "Dal Makhani & Roti Platters (Fresh Banquet Surplus)",
    "food_category": "Cooked meals",
    "is_vegetarian": True,
    "quantity_kg": 25.0,
    "estimated_servings": 75,
    "preparation_time": now.isoformat() + "Z",
    "expiry_time": (now + datetime.timedelta(hours=5)).isoformat() + "Z",
    "storage_conditions": "Thermal Warmer Container",
    "current_temperature": 63.5,
    "allergen_info": "Dairy (Ghee, Butter)",
    "ingredients": "Black lentils, Butter, Cream, Spices",
    "pickup_address": "MI Road, C-Scheme, Jaipur",
    "pickup_lat": 26.9180,
    "pickup_lng": 75.8010,
    "pickup_window_start": now.isoformat() + "Z",
    "pickup_window_end": (now + datetime.timedelta(hours=4)).isoformat() + "Z",
    "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d"
}
code, body = http_call(f"{BASE_URL}/api/rescue/listings", "POST", soc_donation_payload, headers={"Authorization": f"Bearer {rest_token}"})
soc_listing_id = body.get("listing_id") or body.get("id") if isinstance(body, dict) else None
if code == 200 and soc_listing_id:
    record("REST-3", "Restaurant", "Create Social Food Donation for NGOs", "HTTP 200 & Listing created", f"HTTP 200, Social Listing ID #{soc_listing_id}", "PASS")
else:
    record("REST-3", "Restaurant", "Create Social Food Donation", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# Test 3.4: Confirm Customer Pickup with OTP at Restaurant
if created_order_id and pickup_otp:
    code, body = http_call(f"{BASE_URL}/api/marketplace/orders/confirm-pickup", "POST", {
        "order_id": created_order_id,
        "pickup_otp": pickup_otp
    }, headers={"Authorization": f"Bearer {rest_token}"})
    if code == 200 and body.get("status") == "success":
        record("REST-4", "Restaurant", "Customer Order Pickup Confirmation via OTP", "HTTP 200 & Order Completed", f"HTTP 200: {body.get('message')}", "PASS")
    else:
        record("REST-4", "Restaurant", "Customer Order Pickup Confirmation", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# ==============================================================================
# 4. NGO WORKFLOW TESTS
# ==============================================================================
print("\n--- RUNNING NGO ROLE TESTS ---")

# Test 4.1: NGO Registration with Capacity & Address
ngo_email = f"ngo_{rand_num}@jaipur-test.in"
ngo_payload = {
    "email": ngo_email,
    "phone": f"+9198{rand_num}6677",
    "password": "password123",
    "full_name": "Jaipur Compassion Food Bank",
    "role": "ngo",
    "business_or_org_name": "Jaipur Compassion Relief Society",
    "capacity_meals_per_day": 350,
    "address": "Gandhi Nagar Shelter Kitchen, Jaipur"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", ngo_payload)
ngo_token = body.get("access_token") if isinstance(body, dict) else None
if code == 200 and ngo_token:
    record("NGO-1", "NGO", "NGO Registration with Capacity & Address", "HTTP 200 & Token", f"HTTP 200, Capacity: {ngo_payload['capacity_meals_per_day']} meals/day", "PASS")
else:
    record("NGO-1", "NGO", "NGO Registration", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# Test 4.2: Discover Available Free Food Donations
code, listings = http_call(f"{BASE_URL}/api/rescue/listings", "GET", headers={"Authorization": f"Bearer {ngo_token}"})
if code == 200 and isinstance(listings, list):
    record("NGO-2", "NGO", "Discover Available Free Donations", "HTTP 200 & available donations list", f"HTTP 200, Found {len(listings)} donations available", "PASS")
else:
    record("NGO-2", "NGO", "Discover Available Free Donations", "HTTP 200", f"HTTP {code}", "FAIL")

# Test 4.3: Claim Social Donation (Prevent oversubscription)
if soc_listing_id:
    # Attempt claim exceeding servings
    code, body = http_call(f"{BASE_URL}/api/matching/claim", "POST", {
        "listing_id": soc_listing_id,
        "claimed_servings": 9999,
        "notes": "Excessive request"
    }, headers={"Authorization": f"Bearer {ngo_token}"})
    if code in (400, 422):
        record("NGO-3", "NGO", "Prevent Oversubscription of Donation", "HTTP 400 (exceeds servings)", f"HTTP {code}: {body.get('detail')}", "PASS")
    else:
        record("NGO-3", "NGO", "Prevent Oversubscription", "HTTP 400", f"HTTP {code}", "FAIL")

    # Valid Claim
    code, body = http_call(f"{BASE_URL}/api/matching/claim", "POST", {
        "listing_id": soc_listing_id,
        "claimed_servings": 50,
        "notes": "Gandhi Nagar Shelter Dinner Distribution"
    }, headers={"Authorization": f"Bearer {ngo_token}"})
    claim_id = body.get("claim_id") if isinstance(body, dict) else None
    if code == 200 and claim_id:
        record("NGO-4", "NGO", "Claim Free Donation for Beneficiaries", "HTTP 200 & Claim Created", f"HTTP 200, Claim ID #{claim_id}, Delivery OTP: {body.get('delivery_otp')}", "PASS")
    else:
        record("NGO-4", "NGO", "Claim Free Donation", "HTTP 200", f"HTTP {code}: {body}", "FAIL")
else:
    claim_id = None

# ==============================================================================
# 5. VOLUNTEER WORKFLOW TESTS
# ==============================================================================
print("\n--- RUNNING VOLUNTEER ROLE TESTS ---")

# Test 5.1: Volunteer Registration with Vehicle & Locality
vol_email = f"volunteer_{rand_num}@jaipur-test.in"
vol_payload = {
    "email": vol_email,
    "phone": f"+9198{rand_num}8899",
    "password": "password123",
    "full_name": "Suresh Meena",
    "role": "volunteer",
    "vehicle_type": "bike",
    "address": "Malviya Nagar & C-Scheme"
}
code, body = http_call(f"{BASE_URL}/api/auth/register", "POST", vol_payload)
vol_token = body.get("access_token") if isinstance(body, dict) else None
if code == 200 and vol_token:
    record("VOL-1", "Volunteer", "Volunteer Registration with Vehicle & Locality", "HTTP 200 & Token", f"HTTP 200, Vehicle: {vol_payload['vehicle_type']}, Locality: {vol_payload['address']}", "PASS")
else:
    record("VOL-1", "Volunteer", "Volunteer Registration", "HTTP 200", f"HTTP {code}: {body}", "FAIL")

# Test 5.2: View Assigned Delivery Tasks
code, tasks = http_call(f"{BASE_URL}/api/logistics/available-tasks", "GET", headers={"Authorization": f"Bearer {vol_token}"})
if code == 200 and isinstance(tasks, list):
    record("VOL-2", "Volunteer", "Fetch Volunteer Delivery Tasks", "HTTP 200 & Tasks Array", f"HTTP 200, Active Tasks: {len(tasks)}", "PASS")
else:
    record("VOL-2", "Volunteer", "Fetch Tasks", "HTTP 200", f"HTTP {code}", "FAIL")

# ==============================================================================
# 6. ADMIN WORKFLOW TESTS
# ==============================================================================
print("\n--- RUNNING ADMIN ROLE TESTS ---")

# Test 6.1: Admin Login with provisioned admin credentials
code, body = http_call(f"{BASE_URL}/api/auth/login", "POST", {"email": "admin@jaipur-demo.in", "password": "password123"})
admin_token = body.get("access_token") if isinstance(body, dict) else None
if code == 200 and admin_token and body["user"]["role"] == "admin":
    record("ADM-1", "Admin", "Admin Authentication with Provisioned Account", "HTTP 200 & Admin Role", f"HTTP 200, User: {body['user']['full_name']}, Role: {body['user']['role']}", "PASS")
else:
    record("ADM-1", "Admin", "Admin Authentication", "HTTP 200 & role=admin", f"HTTP {code}: {body}", "FAIL")

# Test 6.2: Admin Fetch Users Management Roster
code, users = http_call(f"{BASE_URL}/api/admin/users", "GET", headers={"Authorization": f"Bearer {admin_token}"})
if code == 200 and isinstance(users, list) and len(users) > 0:
    record("ADM-2", "Admin", "User Management & Verification Review", "HTTP 200 & Complete User Roster", f"HTTP 200, Total Platform Users: {len(users)}", "PASS")
else:
    record("ADM-2", "Admin", "User Management Roster", "HTTP 200", f"HTTP {code}", "FAIL")

# Test 6.3: Admin Live Impact Metrics Calculation
code, metrics = http_call(f"{BASE_URL}/api/impact/metrics", "GET", headers={"Authorization": f"Bearer {admin_token}"})
if code == 200 and "total_food_rescued_kg" in metrics:
    record("ADM-3", "Admin", "Live Platform Impact Calculation", "HTTP 200 & Live Metrics", f"Food Rescued: {metrics['total_food_rescued_kg']} kg, Meals: {metrics['total_meals_redistributed']}, CO2e Avoided: {metrics['avoided_ghg_emissions_co2e_kg']} kg", "PASS")
else:
    record("ADM-3", "Admin", "Live Impact Metrics", "HTTP 200", f"HTTP {code}", "FAIL")

# Test 6.4: Admin Audit Log Review
code, audits = http_call(f"{BASE_URL}/api/admin/audit-logs", "GET", headers={"Authorization": f"Bearer {admin_token}"})
if code == 200 and isinstance(audits, list):
    record("ADM-4", "Admin", "System Audit Logs Access", "HTTP 200 & Audit Trail", f"HTTP 200, Audit Records: {len(audits)}", "PASS")
else:
    record("ADM-4", "Admin", "Audit Logs", "HTTP 200", f"HTTP {code}", "FAIL")

# ==============================================================================
# SUMMARY
# ==============================================================================
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print("\n" + "=" * 80)
print(f"ROLE-BASED PLATFORM TEST SUITE SUMMARY: {total} executed, {passed} PASSED, {failed} FAILED")
print("=" * 80)

with open("role_based_platform_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results
    }, f, indent=2)
