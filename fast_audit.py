import urllib.request
import urllib.error
import json
import sys

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
            print(f"Failed to login {role}: {e}", flush=True)
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

def main():
    print("Fetching openapi.json...", flush=True)
    with urllib.request.urlopen(f"{BASE_URL}/openapi.json") as resp:
        spec = json.loads(resp.read().decode())

    tokens = get_tokens()
    print("Tokens retrieved successfully.", flush=True)

    paths = spec.get("paths", {})
    print(f"Found {len(paths)} paths in OpenAPI specification.", flush=True)

    results = []
    failures = []

    for path, methods in paths.items():
        for method, details in methods.items():
            method_upper = method.upper()
            if "{" in path:
                continue # Skip parameterized for mass test, we do targeted below

            # Determine best role
            token = tokens["admin"] # Admin has highest privilege
            if "customer" in path or "deals" in path:
                token = tokens["customer"]
            elif "volunteer" in path or "logistics" in path:
                token = tokens["volunteer"]
            elif "ngo" in path:
                token = tokens["ngo"]
            elif "restaurant" in path or "donor" in path:
                token = tokens["donor"]

            if method_upper == "GET":
                status, body = http_req(f"{BASE_URL}{path}", method="GET", token=token)
                item = {"path": path, "method": "GET", "status": status, "body": str(body)[:200]}
                results.append(item)
                if status >= 400:
                    failures.append(item)
                    print(f"[FAIL {status}] GET {path} -> {str(body)[:150]}", flush=True)
                else:
                    print(f"[PASS {status}] GET {path}", flush=True)

    # Now test all key POST/PUT APIs with genuine sample payloads
    custom_mutations = [
        # Auth
        ("POST", "/api/auth/verify-otp", {"phone": "9876543210", "otp": "123456"}, None),
        ("POST", "/api/auth/forgot-password", {"email": "customer@jaipur-demo.in"}, None),
        ("PUT", "/api/auth/profile", {"full_name": "Jaipur Chef", "phone": "9876543210"}, tokens["donor"]),
        # Rescue
        ("GET", "/api/rescue/listings/1", None, tokens["ngo"]),
        # Matching
        ("GET", "/api/matching/find-ngos/1", None, tokens["donor"]),
        # Temperature
        ("GET", "/api/temperature/history/1", None, tokens["donor"]),
        ("POST", "/api/temperature/log", {"listing_id": 1, "temperature_celsius": 63.5, "stage": "donor_prep", "measurement_method": "digital", "notes": "audit test"}, tokens["donor"]),
        # OCR
        ("POST", "/api/ocr/extract", {"listing_id": 1, "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"}, tokens["donor"]),
        # Safety
        ("POST", "/api/safety/inspect", {"listing_id": 1, "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"}, tokens["donor"]),
        ("POST", "/api/safety/admin-review/1?approve=true&notes=AuditApproved", None, tokens["admin"]),
        # Fraud
        ("GET", "/api/fraud/messages", None, tokens["donor"]),
        ("POST", "/api/fraud/messages", {"recipient_id": 3, "message_text": "Audit coordination message", "listing_id": 1}, tokens["donor"]),
        ("GET", "/api/fraud/alerts", None, tokens["admin"]),
        ("POST", "/api/fraud/triage/1", {"status": "reviewed", "admin_notes": "Audit triage resolution"}, tokens["admin"]),
        ("GET", "/api/fraud/trust-score/2", None, tokens["admin"]),
        # Admin
        ("GET", "/api/admin/overview", None, tokens["admin"]),
        ("GET", "/api/admin/users", None, tokens["admin"]),
        ("POST", "/api/admin/verify-user/2?approve=true", None, tokens["admin"]),
        ("GET", "/api/admin/audit-logs", None, tokens["admin"]),
        # Marketplace
        ("POST", "/api/marketplace/calculate-price", {"original_price": 200, "food_category": "Cooked meals", "total_quantity": 10, "hours_until_deadline": 3, "is_rescue_bag": False}, None),
        ("GET", "/api/marketplace/deals", None, None),
        ("GET", "/api/marketplace/deals/1", None, None),
        ("GET", "/api/marketplace/listings/restaurant", None, tokens["restaurant"]),
        ("GET", "/api/marketplace/orders/customer", None, tokens["customer"]),
        ("GET", "/api/marketplace/analytics/2", None, tokens["restaurant"]),
    ]

    print("\n--- TESTING MUTATION & PARAMETERIZED ENDPOINTS ---", flush=True)
    for method, path, body, token in custom_mutations:
        status, resp = http_req(f"{BASE_URL}{path}", method=method, data=body, token=token)
        item = {"path": path, "method": method, "status": status, "body": str(resp)[:200]}
        results.append(item)
        if status >= 400:
            failures.append(item)
            print(f"[FAIL {status}] {method} {path} -> {str(resp)[:150]}", flush=True)
        else:
            print(f"[PASS {status}] {method} {path}", flush=True)

    print(f"\n=======================================================", flush=True)
    print(f"TOTAL AUDITED: {len(results)} | SUCCESS: {len(results) - len(failures)} | FAILURES: {len(failures)}", flush=True)
    print(f"=======================================================", flush=True)

    with open("audit_summary.json", "w") as f:
        json.dump({"results": results, "failures": failures}, f, indent=2)

if __name__ == "__main__":
    main()
