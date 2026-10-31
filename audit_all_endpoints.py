import os
import sys
import json
import urllib.request
import urllib.error

# Set up python path for backend
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from app.main import app

BASE_URL = "http://localhost:8001"

def get_tokens():
    roles = {
        "admin": ("admin@jaipur-demo.in", "password123"),
        "donor": ("hostel@jaipur-demo.in", "password123"),
        "restaurant": ("restaurant@jaipur-demo.in", "password123"),
        "ngo": ("ngo@jaipur-demo.in", "password123"),
        "volunteer": ("volunteer@jaipur-demo.in", "password123"),
        "customer": ("customer@jaipur-demo.in", "password123"),
    }
    tokens = {}
    for role, (email, pwd) in roles.items():
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/login",
            data=json.dumps({"email": email, "password": pwd}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                tokens[role] = data.get("access_token")
        except Exception as e:
            tokens[role] = None
            print(f"Failed to login {role}: {e}")
    return tokens

def http_req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err_json = json.loads(e.read().decode())
        except Exception:
            err_json = e.read().decode()
        return e.code, err_json
    except Exception as e:
        return 0, str(e)

def audit():
    tokens = get_tokens()
    print("Tokens retrieved:", {k: (v[:10] + "..." if v else None) for k, v in tokens.items()})

    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for m in route.methods:
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    routes.append({
                        "path": route.path,
                        "method": m,
                        "name": route.name,
                        "endpoint": route.endpoint.__name__ if hasattr(route, "endpoint") else ""
                    })

    print(f"\nTotal registered routes: {len(routes)}")

    results = []

    # Test GET routes (without path variables)
    for r in routes:
        path = r["path"]
        method = r["method"]
        if "{" in path:
            continue # Needs specific ID

        # Determine best token to test
        tested_token = None
        if "admin" in path or "audit" in path or "alerts" in path or "triage" in path:
            tested_token = tokens.get("admin")
        elif "volunteer" in path or "logistics" in path:
            tested_token = tokens.get("volunteer")
        elif "ngo" in path:
            tested_token = tokens.get("ngo")
        elif "restaurant" in path or "donor" in path:
            tested_token = tokens.get("restaurant")
        elif "customer" in path or "orders" in path:
            tested_token = tokens.get("customer")
        else:
            tested_token = tokens.get("admin")

        if method == "GET":
            status, resp = http_req(f"{BASE_URL}{path}", method="GET", token=tested_token)
            results.append({
                "path": path,
                "method": method,
                "status": status,
                "response": resp,
                "token_used": "authenticated" if tested_token else "none"
            })
            if status >= 400:
                print(f"[FAIL {status}] GET {path} -> {str(resp)[:150]}")
            else:
                print(f"[OK {status}] GET {path}")

    # Specific tests for parameterized and POST routes
    custom_tests = [
        # Health
        ("GET", "/health", None, None),
        ("GET", "/api/health", None, None),
        # Auth
        ("GET", "/api/auth/me", None, tokens["donor"]),
        ("GET", "/api/auth/me", None, tokens["customer"]),
        ("PUT", "/api/auth/profile", {"full_name": "Updated Name", "phone": "9876543210"}, tokens["donor"]),
        # Rescue
        ("GET", "/api/rescue/listings", None, tokens["ngo"]),
        ("GET", "/api/rescue/listings/1", None, tokens["ngo"]),
        # Matching
        ("GET", "/api/matching/find-ngos/1", None, tokens["donor"]),
        ("GET", "/api/matching/claims", None, tokens["ngo"]),
        # Temperature
        ("GET", "/api/temperature/history/1", None, tokens["donor"]),
        ("POST", "/api/temperature/log", {"listing_id": 1, "temperature_celsius": 62.0, "stage": "donor_prep", "measurement_method": "digital", "notes": "audit"}, tokens["donor"]),
        # OCR
        ("POST", "/api/ocr/extract", {"listing_id": 1, "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"}, tokens["donor"]),
        # Safety
        ("POST", "/api/safety/inspect", {"listing_id": 1, "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"}, tokens["donor"]),
        ("POST", "/api/safety/admin-review/1?approve=true&notes=Approved", None, tokens["admin"]),
        # Logistics
        ("GET", "/api/logistics/available-tasks", None, tokens["volunteer"]),
        ("GET", "/api/logistics/history", None, tokens["volunteer"]),
        # Fraud
        ("GET", "/api/fraud/messages", None, tokens["donor"]),
        ("POST", "/api/fraud/messages", {"recipient_id": 3, "message_text": "Hello NGO", "listing_id": 1}, tokens["donor"]),
        ("GET", "/api/fraud/alerts", None, tokens["admin"]),
        ("POST", "/api/fraud/triage/1", {"status": "reviewed", "admin_notes": "Audit triage"}, tokens["admin"]),
        ("GET", "/api/fraud/trust-score/2", None, tokens["admin"]),
        # Predictions & Impact
        ("GET", "/api/impact/metrics", None, None),
        ("GET", "/api/predictions/forecasts?day_name=Saturday", None, None),
        # Admin
        ("GET", "/api/admin/overview", None, tokens["admin"]),
        ("GET", "/api/admin/users", None, tokens["admin"]),
        ("POST", "/api/admin/verify-user/2?approve=true", None, tokens["admin"]),
        ("GET", "/api/admin/audit-logs", None, tokens["admin"]),
        # Marketplace
        ("GET", "/api/marketplace/deals", None, None),
        ("GET", "/api/marketplace/deals/1", None, None),
        ("POST", "/api/marketplace/calculate-price", {"original_price": 200, "food_category": "Cooked meals", "total_quantity": 10, "hours_until_deadline": 3, "is_rescue_bag": False}, None),
        ("GET", "/api/marketplace/listings/restaurant", None, tokens["restaurant"]),
        ("GET", "/api/marketplace/orders/customer", None, tokens["customer"]),
        ("GET", "/api/marketplace/analytics/2", None, tokens["restaurant"]),
    ]

    print("\n--- RUNNING CUSTOM PARAMETERIZED & POST ROUTE AUDITS ---")
    for method, path, body, token in custom_tests:
        status, resp = http_req(f"{BASE_URL}{path}", method=method, data=body, token=token)
        results.append({
            "path": path,
            "method": method,
            "status": status,
            "response": resp,
            "token_used": "authenticated" if token else "none"
        })
        if status >= 400:
            print(f"[FAIL {status}] {method} {path} -> {str(resp)[:200]}")
        else:
            print(f"[OK {status}] {method} {path}")

    # Write results to json
    with open("endpoint_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nAudit written to endpoint_audit_results.json")

if __name__ == "__main__":
    audit()
