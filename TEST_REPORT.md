# ANN-DAAN AI – AUTOMATED TEST EXECUTION REPORT

**Test Runner:** `pytest 9.2.0` with Python 3.14.3  
**Test Suite Path:** `backend/tests/test_backend.py`  
**Total Tests Collected:** 34  
**Total Tests Passed:** 34 (100% Pass Rate)  
**Total Tests Failed:** 0  
**Execution Time:** 5.50 seconds  
**Audit Date:** October 31, 2026  

---

## 1. COMPREHENSIVE TEST RESULTS TABLE

| # | Test Case Identifier | Category | Status | Verified Assertion |
|---|---|---|---|---|
| 1 | `test_root_and_health` | System Health | **PASS** | Returns HTTP 200, App name, and Jaipur pilot city |
| 2 | `test_auth_login_donor` | Authentication | **PASS** | Authentic JWT bearer token and user profile returned |
| 3 | `test_auth_login_invalid` | Security | **PASS** | HTTP 401 Unauthorized on incorrect credentials |
| 4 | `test_get_listings` | Core API | **PASS** | HTTP 200 with active surplus listings |
| 5 | `test_ai_visual_inspection_disclaimer` | Compliance | **PASS** | Mandatory FSSAI preliminary screening disclaimer present |
| 6 | `test_ai_visual_inspection_mould_detection` | AI Quality | **PASS** | Potential concern flagged when visual mould detected |
| 7 | `test_food_label_ocr_mismatch` | AI OCR | **PASS** | Detects packaging use-by expiration date mismatch |
| 8 | `test_nlp_fraud_suspicious_message` | NLP Sentinel | **PASS** | Intercepts OTP solicitation and fees with risk score > 0.8 |
| 9 | `test_temperature_logging_abnormal` | Food Safety | **PASS** | Flags abnormal temperature (<60°C hot, >4°C cold) |
| 10 | `test_ngo_matching_engine` | Matching AI | **PASS** | Haversine distance, capacity, and dietary ranking |
| 11 | `test_impact_metrics` | Impact Engine | **PASS** | WRI India GHG avoided emissions calculation verified |
| 12 | `test_run_jaipur_scenario_end_to_end` | Pilot Scenario | **PASS** | 120 hostel meals &rarr; 80 claimed &rarr; OTP volunteer handoff |
| 13 | `test_dynamic_pricing_calculation` | Pricing Engine | **PASS** | Monotonic markdown, category factors, and 20-80% bounds |
| 14 | `test_marketplace_browse_deals` | Marketplace | **PASS** | Deal browsing and surprise bag inventory verified |
| 15 | `test_marketplace_customer_order_and_oversell_prevention` | Marketplace | **PASS** | Atomic stock reservation and oversell rejection verified |
| 16 | `test_marketplace_restaurant_analytics` | Commercial | **PASS** | Revenue recovered and sell-through velocity verified |
| 17 | `test_marketplace_hybrid_scenario` | Hybrid Engine | **PASS** | 18 commercial meals sold + 12 meals donated to shelter |
| 18 | `test_auth_forgot_and_reset_password` | Auth Security | **PASS** | OTP generation and password reset verified |
| 19 | `test_auth_register_customer_and_profile_update` | Customer Profile| **PASS** | User registration and dietary preference updates |
| 20 | `test_marketplace_order_cancellation_and_inventory_release` | Transactions | **PASS** | Refund issued and inventory atomically restored |
| 21 | `test_security_customer_cannot_access_admin_overview` | RBAC Audit | **PASS** | Asserts HTTP 403 Forbidden for Customer role |
| 22 | `test_security_ngo_cannot_access_admin_overview` | RBAC Audit | **PASS** | Asserts HTTP 403 Forbidden for NGO role |
| 23 | `test_security_volunteer_cannot_access_admin_overview` | RBAC Audit | **PASS** | Asserts HTTP 403 Forbidden for Volunteer role |
| 24 | `test_security_restaurant_cannot_modify_another_restaurant_listing`| RBAC Audit | **PASS** | Asserts HTTP 403 Forbidden on foreign listing PUT/DELETE |
| 25 | `test_security_unauthenticated_request_rejected` | Security | **PASS** | Asserts HTTP 401 Unauthorized on missing token |
| 26 | `test_security_valid_admin_token_succeeds` | RBAC Audit | **PASS** | Asserts HTTP 200 with full admin analytics metrics |
| 27 | `test_security_expired_token_rejected` | Security | **PASS** | Asserts HTTP 401 with explicit expired signature message |
| 28 | `test_security_manipulated_role_claim_rejected` | Security | **PASS** | Asserts HTTP 401 on tampered signature role claim |
| 29 | `test_e2e_workflow_a_commercial_rescue_complete` | Workflow A | **PASS** | Registration &rarr; Listing &rarr; Pricing &rarr; Order &rarr; Pay &rarr; OTP Pickup |
| 30 | `test_e2e_workflow_b_rescue_to_donation_and_volunteer` | Workflow B | **PASS** | Surplus &rarr; Donation Transition &rarr; NGO Claim &rarr; Volunteer &rarr; Delivery |
| 31 | `test_e2e_workflow_c_fraud_detection_and_admin_triage` | Workflow C | **PASS** | Phishing message &rarr; Alert created &rarr; Admin review &rarr; Triaged |
| 32 | `test_e2e_workflow_d_safety_inspection_and_admin_decision` | Workflow D | **PASS** | Mould detection &rarr; Safety flag &rarr; Admin review &rarr; Approved/Quarantined |
| 33 | `test_demo_seed_preserves_marketplace_inventory` | Regression | **PASS** | Demo refresh leaves deal stock and status unchanged |
| 34 | `test_social_claims_preserve_inventory_and_limit_otp_access` | Social Rescue | **PASS** | Prevents overclaims, blocks pending listings, and limits OTP visibility by role |

---

## 2. REPRODUCTION INSTRUCTIONS

To re-run the complete automated test suite locally:

```powershell
# Navigate to backend directory
cd backend

# Execute pytest suite
python -m pytest tests/test_backend.py -v
```
