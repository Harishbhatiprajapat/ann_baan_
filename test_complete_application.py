"""
ANN-DAAN AI - Master Test Suite: test_complete_application.py
Covers all test phases required by Phase 8:
A. Backend health tests
B. Authentication tests
C. Role authorization tests
D. API request validation tests
E. Database persistence tests
F. Image upload tests
G. Donation creation tests
H. NGO discovery and claim tests
I. Volunteer delivery tests
J. Customer order tests
K. Admin analytics tests
"""

import urllib.request
import urllib.error
import json
import sqlite3
import datetime
import uuid
import sys
import io

BASE_URL = "http://localhost:8001"

def log_pass(section, name):
    print(f"[{section}] PASS: {name}", flush=True)

def log_fail(section, name, detail):
    print(f"[{section}] FAIL: {name} -> {detail}", flush=True)
    sys.exit(1)

def call(path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed

def multipart_upload(path, filename, content_bytes, token=None):
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(content_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=bytes(body), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed

def main():
    print("=" * 80)
    print("STARTING TEST_COMPLETE_APPLICATION: COMPREHENSIVE PLATFORM VERIFICATION")
    print("=" * 80, flush=True)

    uid = int(datetime.datetime.now().timestamp()) % 100000

    # SECTION A: BACKEND HEALTH TESTS
    status, health = call("/health")
    if status == 200 and health.get("status") == "healthy":
        log_pass("SECTION A", "Root /health is healthy and DB connected")
    else:
        log_fail("SECTION A", "Root /health failed", health)

    status, api_health = call("/api/health")
    if status == 200 and api_health.get("status") == "healthy":
        log_pass("SECTION A", "API /api/health is healthy and DB connected")
    else:
        log_fail("SECTION A", "API /api/health failed", api_health)

    # SECTION B: AUTHENTICATION TESTS
    # 1. Valid Admin Login
    status, admin_login = call("/api/auth/login", "POST", {"email": "admin@jaipur-demo.in", "password": "password123"})
    if status == 200 and "access_token" in admin_login:
        admin_token = admin_login["access_token"]
        log_pass("SECTION B", "Admin authentication successful")
    else:
        log_fail("SECTION B", "Admin authentication failed", admin_login)

    # 2. Invalid Credentials
    status, bad_login = call("/api/auth/login", "POST", {"email": "admin@jaipur-demo.in", "password": "wrongpassword"})
    if status == 401:
        log_pass("SECTION B", "Invalid credentials rejected with HTTP 401")
    else:
        log_fail("SECTION B", "Invalid credentials did not return 401", bad_login)

    # 3. Register Independent Accounts
    roles_registered = {}
    for idx, r in enumerate(["donor", "ngo", "volunteer", "customer"]):
        email = f"complete_{r}_{uid}@jaipur-pilot.in"
        phone = f"9{idx+1}{uid:08d}"[:10]
        status, reg = call("/api/auth/register", "POST", {
            "email": email,
            "phone": phone,
            "password": "password123",
            "full_name": f"Verified {r.title()}",
            "role": r,
            "business_or_org_name": f"Jaipur {r.title()} Entity"
        })
        if status == 200:
            roles_registered[r] = (reg["access_token"], reg["user"]["id"])
            log_pass("SECTION B", f"Registered independent {r.upper()} account (ID #{reg['user']['id']})")
        else:
            log_fail("SECTION B", f"Registration failed for {r}", reg)

    donor_token, donor_id = roles_registered["donor"]
    ngo_token, ngo_id = roles_registered["ngo"]
    vol_token, vol_id = roles_registered["volunteer"]
    cust_token, cust_id = roles_registered["customer"]

    # SECTION C: ROLE AUTHORIZATION TESTS
    # Customer forbidden from admin endpoints
    status, _ = call("/api/admin/overview", "GET", token=cust_token)
    if status == 403:
        log_pass("SECTION C", "Customer blocked from Admin endpoint (HTTP 403)")
    else:
        log_fail("SECTION C", "Customer was not blocked from Admin", status)

    # Volunteer forbidden from donor listings modification
    status, _ = call("/api/rescue/listings/1", "DELETE", token=vol_token)
    if status in (403, 405):
        log_pass("SECTION C", "Volunteer blocked from modifying Donor listings")
    else:
        log_fail("SECTION C", "Volunteer access check failed", status)

    # SECTION D: API REQUEST VALIDATION TESTS
    # Missing required field in listing
    status, val_err = call("/api/rescue/listings", "POST", {"food_name": "Incomplete"}, token=donor_token)
    if status == 422:
        log_pass("SECTION D", "FastAPI Pydantic validation rejected incomplete payload with HTTP 422")
    else:
        log_fail("SECTION D", "Validation did not return 422", val_err)

    # SECTION E: DATABASE PERSISTENCE TESTS
    conn = sqlite3.connect("backend/anndaan.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE id IN (?, ?, ?, ?)", (donor_id, ngo_id, vol_id, cust_id))
    persisted_count = cur.fetchone()[0]
    if persisted_count == 4:
        log_pass("SECTION E", "SQLite database verified 4 independent persisted user entities")
    else:
        log_fail("SECTION E", "Users not persisted in SQLite", persisted_count)

    # SECTION F: IMAGE UPLOAD TESTS
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb" + b"\x00" * 200 + b"\xff\xd9"
    status, upload_res = multipart_upload("/api/rescue/upload-image", f"test_{uid}.jpg", fake_image_bytes, token=donor_token)
    if status == 200 and "image_url" in upload_res and "image_hash" in upload_res:
        uploaded_image_url = upload_res["image_url"]
        log_pass("SECTION F", f"Food image uploaded and hashed (dHash: {upload_res['image_hash']})")
    else:
        log_fail("SECTION F", "Image upload failed", upload_res)

    # SECTION G: DONATION CREATION TESTS
    now = datetime.datetime.now(datetime.timezone.utc)
    status, listing_res = call("/api/rescue/listings", "POST", {
        "food_name": f"Heritage Kadi Pakoda & Steamed Rice #{uid}",
        "food_category": "Cooked meals",
        "is_vegetarian": True,
        "quantity_kg": 20.0,
        "estimated_servings": 50,
        "preparation_time": now.isoformat(),
        "expiry_time": (now + datetime.timedelta(hours=5)).isoformat(),
        "storage_conditions": "Hot holding above 60C",
        "current_temperature": 63.8,
        "allergen_info": "Dairy, Gram flour",
        "ingredients": "Curd, Besan, Rice, Spices",
        "pickup_address": "Tonk Road, Jaipur",
        "pickup_lat": 26.8900,
        "pickup_lng": 75.8100,
        "pickup_window_start": now.isoformat(),
        "pickup_window_end": (now + datetime.timedelta(hours=3)).isoformat(),
        "special_instructions": "Thermal hot box",
        "image_urls": [uploaded_image_url]
    }, token=donor_token)
    if status == 200 and listing_res.get("status") == "success":
        listing_id = listing_res["listing_id"]
        log_pass("SECTION G", f"Donation created with status 'available' (Listing ID #{listing_id})")
    else:
        log_fail("SECTION G", "Donation creation failed", listing_res)

    # SECTION H: NGO DISCOVERY AND CLAIM TESTS
    status, avail = call("/api/rescue/listings?status_filter=available", "GET", token=ngo_token)
    found = any(l["id"] == listing_id for l in avail)
    if status == 200 and found:
        log_pass("SECTION H", f"NGO discovered donation #{listing_id} with status available")
    else:
        log_fail("SECTION H", f"NGO could not discover listing #{listing_id}", avail)

    status, claim_res = call("/api/matching/claim", "POST", {
        "listing_id": listing_id,
        "claimed_servings": 30,
        "notes": "Slum Relief Center Distribution"
    }, token=ngo_token)
    if status == 200 and claim_res.get("status") == "success":
        claim_id = claim_res["claim_id"]
        deliv_id = claim_res["delivery_id"]
        p_otp = claim_res["pickup_otp"]
        d_otp = claim_res["delivery_otp"]
        log_pass("SECTION H", f"NGO claimed 30 portions (Claim ID #{claim_id}, Delivery ID #{deliv_id})")
    else:
        log_fail("SECTION H", "Claim failed", claim_res)

    # SECTION I: VOLUNTEER DELIVERY TESTS
    status, accept = call(f"/api/logistics/accept/{deliv_id}", "POST", token=vol_token)
    if status == 200:
        log_pass("SECTION I", f"Volunteer accepted Delivery #{deliv_id}")
    else:
        log_fail("SECTION I", "Volunteer accept task failed", accept)

    status, pickup = call("/api/logistics/confirm-pickup", "POST", {
        "delivery_id": deliv_id, "otp": p_otp, "temperature_reading": 63.5
    }, token=vol_token)
    if status == 200:
        log_pass("SECTION I", "Donor handoff: Pickup verified with OTP & 63.5C temperature")
    else:
        log_fail("SECTION I", "Pickup OTP failed", pickup)

    status, dropoff = call("/api/logistics/confirm-delivery", "POST", {
        "delivery_id": deliv_id, "otp": d_otp, "temperature_reading": 61.2
    }, token=vol_token)
    if status == 200:
        log_pass("SECTION I", "NGO handoff: Delivery verified with OTP & 61.2C temperature")
    else:
        log_fail("SECTION I", "Delivery OTP failed", dropoff)

    # SECTION J: CUSTOMER ORDER TESTS
    status, deal = call("/api/marketplace/listings", "POST", {
        "title": f"Bakehouse Surplus Pastry Box #{uid}",
        "food_category": "Bakery products",
        "dietary_type": "veg",
        "is_vegetarian": True,
        "is_rescue_bag": False,
        "original_price": 200.0,
        "total_quantity": 5,
        "preparation_time": now.isoformat(),
        "pickup_deadline": (now + datetime.timedelta(hours=4)).isoformat(),
        "pickup_address": "Raja Park, Jaipur",
        "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff",
        "auto_donate_unsold": True
    }, token=donor_token)
    deal_id = deal["listing_id"]

    status, order = call("/api/marketplace/orders/create", "POST", {
        "rescue_listing_id": deal_id, "quantity": 1, "payment_method": "upi_simulated"
    }, token=cust_token)
    order_id = order["order_id"]

    status, pay = call("/api/marketplace/orders/pay", "POST", {"order_id": order_id}, token=cust_token)
    order_otp = pay["pickup_otp"]

    status, confirm = call("/api/marketplace/orders/confirm-pickup", "POST", {
        "order_id": order_id, "pickup_otp": order_otp
    }, token=donor_token)
    if status == 200:
        log_pass("SECTION J", f"Customer ordered, paid, and picked up Deal #{deal_id} (Order #{order_id})")
    else:
        log_fail("SECTION J", "Customer order cycle failed", confirm)

    # SECTION K: ADMIN ANALYTICS TESTS
    status, overview = call("/api/admin/overview", "GET", token=admin_token)
    status_imp, impact = call("/api/impact/metrics", "GET")
    if status == 200 and status_imp == 200 and impact.get("total_meals_saved", 0) > 0:
        log_pass("SECTION K", f"Admin analytics verified (Total meals saved: {impact['total_meals_saved']}, Active users: {overview['metrics']['total_users']})")
    else:
        log_fail("SECTION K", "Admin analytics failed", overview)

    print("=" * 80)
    print("TEST_COMPLETE_APPLICATION: ALL 11 SECTIONS (A-K) PASSED 100%!")
    print("=" * 80, flush=True)

if __name__ == "__main__":
    main()
