"""
ANN-DAAN AI - Comprehensive API Endpoint Test Suite
Tests all registered API endpoints across all routers:
- Health & System
- Authentication & Profile
- Rescue & Food Listings
- NGO Matching & Claims
- Smart Logistics & Dual-OTP
- Food Safety & AI Vision
- OCR Extraction
- Temperature Logging
- Fraud Detection & Governance
- Impact & Predictive Forecasting
- Commercial Marketplace & Orders
"""

import urllib.request
import urllib.error
import json
import os
import sys

BASE_URL = "http://localhost:8001"

def get_auth_tokens():
    accounts = {
        "admin": ("admin@jaipur-demo.in", "password123"),
        "donor": ("hostel@jaipur-demo.in", "password123"),
        "restaurant": ("restaurant@jaipur-demo.in", "password123"),
        "ngo": ("ngo@jaipur-demo.in", "password123"),
        "volunteer": ("volunteer@jaipur-demo.in", "password123"),
        "customer": ("customer@jaipur-demo.in", "password123"),
    }
    tokens = {}
    for role, (email, pwd) in accounts.items():
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/login",
            data=json.dumps({"email": email, "password": pwd}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                tokens[role] = data.get("access_token")
        except Exception as e:
            tokens[role] = None
            print(f"Failed to authenticate {role}: {e}", flush=True)
    return tokens

def call_api(path, method="GET", data=None, token=None):
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
    except Exception as e:
        return 0, str(e)

def test_all_endpoints():
    print("=" * 80)
    print("STARTING TEST_ALL_API_ENDPOINTS: VALIDATING ALL PLATFORM ROUTERS")
    print("=" * 80)

    tokens = get_auth_tokens()
    passed = 0
    failed = 0

    endpoints_to_test = [
        # System Health
        ("GET", "/health", None, None, 200, "Root health check"),
        ("GET", "/api/health", None, None, 200, "API prefix health check"),
        
        # Authentication
        ("GET", "/api/auth/me", None, tokens["donor"], 200, "Get donor profile"),
        ("GET", "/api/auth/me", None, tokens["customer"], 200, "Get customer profile"),
        ("PUT", "/api/auth/profile", {"full_name": "Updated Jaipur Donor", "phone": "9829012345"}, tokens["donor"], 200, "Update profile"),
        ("POST", "/api/auth/verify-otp", {"phone": "9829012345", "otp": "123456"}, None, 200, "Verify phone OTP"),
        ("POST", "/api/auth/forgot-password", {"email": "customer@jaipur-demo.in"}, None, 200, "Request password reset"),
        
        # Rescue & Surplus Listings
        ("GET", "/api/rescue/listings", None, tokens["ngo"], 200, "Get available rescue listings"),
        ("GET", "/api/rescue/listings?status_filter=available", None, tokens["ngo"], 200, "Filter available rescue listings"),
        ("GET", "/api/rescue/listings/1", None, tokens["donor"], 200, "Get listing detail"),
        
        # Matching & Claims
        ("GET", "/api/matching/find-ngos/1", None, tokens["donor"], 200, "Find matching NGOs for listing"),
        ("GET", "/api/matching/claims", None, tokens["ngo"], 200, "Get scoped NGO claims"),
        ("GET", "/api/matching/claims", None, tokens["admin"], 200, "Admin view all claims"),
        
        # Temperature Audit
        ("GET", "/api/temperature/history/1", None, tokens["donor"], 200, "Get listing temperature history"),
        ("POST", "/api/temperature/log", {
            "listing_id": 1, "temperature_celsius": 62.5, "stage": "donor_prep",
            "measurement_method": "digital", "notes": "Automated endpoint test"
        }, tokens["donor"], 200, "Record temperature log"),
        
        # Safety & OCR
        ("POST", "/api/safety/inspect", {
            "listing_id": 1, "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
        }, tokens["donor"], 200, "AI visual food inspection"),
        ("POST", "/api/ocr/extract", {
            "listing_id": 1, "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe"
        }, tokens["donor"], 200, "OCR label text extraction"),
        ("POST", "/api/safety/admin-review/1?approve=true&notes=SafetyAudited", None, tokens["admin"], 200, "Admin food safety signoff"),
        
        # Logistics
        ("GET", "/api/logistics/available-tasks", None, tokens["volunteer"], 200, "Get available volunteer tasks"),
        ("GET", "/api/logistics/history", None, tokens["volunteer"], 200, "Get volunteer delivery history"),
        
        # Fraud & Chat
        ("GET", "/api/fraud/messages", None, tokens["donor"], 200, "Get donor coordination messages"),
        ("POST", "/api/fraud/messages", {
            "recipient_id": 3, "message_text": "Auditing message transport", "listing_id": 1
        }, tokens["donor"], 200, "Send coordination message"),
        ("GET", "/api/fraud/alerts", None, tokens["admin"], 200, "Admin get fraud alerts"),
        ("POST", "/api/fraud/triage/1", {
            "status": "reviewed", "admin_notes": "Triage verified"
        }, tokens["admin"], 200, "Admin triage fraud alert"),
        ("GET", "/api/fraud/trust-score/2", None, tokens["admin"], 200, "Get restaurant trust score"),
        
        # Predictions & Impact
        ("GET", "/api/impact/metrics", None, None, 200, "Public platform impact metrics"),
        ("GET", "/api/predictions/forecasts?day_name=Saturday", None, None, 200, "Predictive surplus forecasts"),
        
        # Admin Portal
        ("GET", "/api/admin/overview", None, tokens["admin"], 200, "Admin platform overview"),
        ("GET", "/api/admin/users", None, tokens["admin"], 200, "Admin get all users"),
        ("POST", "/api/admin/verify-user/2?approve=true", None, tokens["admin"], 200, "Admin approve business verification"),
        ("GET", "/api/admin/audit-logs", None, tokens["admin"], 200, "Admin fetch audit ledger"),
        
        # Commercial Marketplace
        ("GET", "/api/marketplace/deals", None, None, 200, "Customer browse rescue deals"),
        ("GET", "/api/marketplace/deals/1", None, None, 200, "Customer view deal detail"),
        ("POST", "/api/marketplace/calculate-price", {
            "original_price": 250, "food_category": "Cooked meals", "total_quantity": 15,
            "hours_until_deadline": 4, "is_rescue_bag": False
        }, None, 200, "Dynamic pricing calculation"),
        ("GET", "/api/marketplace/listings/restaurant", None, tokens["restaurant"], 200, "Restaurant view active rescue deals"),
        ("GET", "/api/marketplace/orders/customer", None, tokens["customer"], 200, "Customer view active orders"),
        ("GET", "/api/marketplace/analytics/2", None, tokens["restaurant"], 200, "Restaurant surplus analytics"),
        
        # Validation checks (Negative tests expecting 400 or 422)
        ("POST", "/api/auth/login", {"email": "nonexistent@demo.in", "password": "wrong"}, None, 401, "Expected 401 invalid login"),
        ("POST", "/api/marketplace/calculate-price", {"original_price": -10}, None, 422, "Expected 422 for missing required fields"),
        ("GET", "/api/admin/overview", None, tokens["customer"], 403, "Expected 403 when customer accesses admin endpoint"),
    ]

    for method, path, data, token, expected_status, description in endpoints_to_test:
        status, resp = call_api(path, method=method, data=data, token=token)
        if status == expected_status:
            passed += 1
            print(f"[PASS] {status} {method} {path} - {description}", flush=True)
        else:
            failed += 1
            print(f"[FAIL] Expected {expected_status}, got {status} on {method} {path} - {description}: {str(resp)[:150]}", flush=True)

    print("=" * 80)
    print(f"API TEST SUMMARY: {passed + failed} Executed | {passed} PASSED | {failed} FAILED")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_all_endpoints()
