# ANN-DAAN AI: CROSS-PORTAL DATA FLOW AUDIT

**Audit Date:** October 31, 2026  
**Auditor:** Senior Full-Stack & Application Security Engineer  
**Scope:** Cross-Portal Data Synchronization & Multi-Role Pipeline Verification  
**Target Repository:** `c:\Users\haris\Documents\zero_waste Food` (`ANN-DAAN-WORKING`)  
**Reference Prototype:** `c:\Users\haris\Documents\zero_waste Food - prototype` (*Read-Only*)

---

## 1. Executive Summary of Root Causes

Our architectural audit traced the complete lifecycle of a food donation from creation in the Restaurant Portal to discovery and claiming in the NGO Portal, volunteer dispatch, and admin impact calculations.

We identified **4 concrete root causes** preventing newly created restaurant donations from synchronizing to the NGO portal:

1. **Premature Status Hold via Anomaly & Perceptual Hash Over-Triggering:**
   - In `backend/app/routers/rescue.py:59, 80, 156`, any listing evaluated by the Isolation Forest ML model or matching an existing demo image hash was forced to `status = "pending_inspection"`.
   - The NGO Portal strictly queries `GET /api/rescue/listings?status_filter=available`.
   - Because of this status mismatch, legitimate, food-safe donations (>60°C holding temperature, clean visual AI screening) were completely omitted from the NGO query response.
2. **Missing Inventory Decrement & Status Premature Close on Claims:**
   - In `backend/app/routers/matching.py:118`, when an NGO claimed a partial portion (e.g. 30 servings out of 50), the backend immediately changed `listing.status = "claimed"` without decrementing `listing.estimated_servings`.
   - This wiped the remaining 20 portions from available inventory instead of keeping them discoverable.
3. **Unfiltered Claims & Private Data Exposure:**
   - `GET /api/matching/claims` did not enforce role-based scoping using JWT `current_user`. Any user calling the endpoint could view all platform claims.
4. **Timezone Arithmetic Exceptions in Logistics Signoffs:**
   - In `backend/app/routers/logistics.py:180, 240`, `delivery.otp_expires_at` was compared directly with `now = datetime.datetime.utcnow()` without `to_naive_utc()`, risking runtime TypeErrors on offset-aware SQLite timestamps.

---

## 2. Complete Data Flow Mapping

### 2.1 Flow A: Restaurant Social Food Donation to NGO Redistribution

```
[ Restaurant UI ] (DonorDashboard.tsx - Modal "List Free Surplus for NGOs")
       │
       ▼  POST /api/rescue/listings (Authorization: Bearer <Donor JWT>)
[ Restaurant API ] (backend/app/routers/rescue.py: create_listing)
       │
       ├── Datetime normalization (to_naive_utc)
       ├── Food safety temperature check (>60°C or <5°C)
       ├── Anomaly Detection & Image dHash screening
       │
       ▼  SQL INSERT INTO food_listings (status="available", estimated_servings=50)
[ Shared SQLite DB ] (backend/anndaan.db)
       │
       ▼  GET /api/rescue/listings?status_filter=available
[ NGO API ] (backend/app/routers/rescue.py: get_listings)
       │
       ▼  Renders listings where status in ("available", "pending_inspection")
[ NGO Dashboard UI ] (NgoDashboard.tsx - Tab: "Available Food Donations")
       │
       ▼  POST /api/matching/claim (claimed_servings=30)
[ Matching Engine ] (backend/app/routers/matching.py: claim_food_listing)
       │
       ├── Inserts donation_claims (claimed_servings=30, status="approved")
       ├── Decrements listing.estimated_servings: 50 - 30 = 20 remaining
       ├── Updates listing.status: "available" (since 20 portions remain)
       ├── Generates pickup_otp (6 digits) & delivery_otp (6 digits)
       ├── Inserts deliveries (status="assigned")
       │
       ▼  DB Commit & Audit Log
[ Both Portals Refreshed ]
  ├── NGO sees 20 remaining servings in Available tab & 1 active claim in My Claims
  ├── Restaurant sees active claim and pickup notification
  └── Volunteer sees active delivery dispatch
```

### 2.2 Flow B: Commercial Rescue Deal to Customer Purchase

```
[ Restaurant UI ] (DonorDashboard.tsx - Modal "List Commercial Rescue Deal")
       │
       ▼  POST /api/marketplace/listings (Bearer <Donor JWT>)
[ Marketplace Router ] (backend/app/routers/marketplace.py: create_commercial_listing)
       │
       ├── Validates price > 0, total_quantity > 0, future deadline
       ├── AI Pricing Engine calculates dynamic markdown price
       ├── Records auto_donate_unsold consent
       ▼
[ Shared SQLite DB ] (rescue_listings table: status="active", available_quantity=20)
       │
       ▼  GET /api/marketplace/deals
[ Customer UI ] (MarketplaceView.tsx - "Rescue Deals")
       │
       ▼  POST /api/marketplace/orders/create (quantity=2)
[ Orders Engine ]
       ├── Concurrency lock (with_for_update)
       ├── Verifies 2 <= available (prevents overselling)
       ├── Inserts customer_orders (order_status="reserved")
       ├── Increments listing.reserved_quantity (+2)
       ▼
[ Sandbox Checkout ] POST /api/marketplace/orders/pay
       ├── Inserts payment_records (status="completed")
       ├── Transfers reserved_quantity to sold_quantity
       ├── Sets order_status="ready_for_pickup", generates Pickup OTP
       ▼
[ Order Fulfilled ]
  ├── Customer displays OTP at restaurant counter
  └── Restaurant calls POST /api/marketplace/orders/confirm-pickup with OTP
```

### 2.3 Flow C: Volunteer Task Pickup & Delivery Signoff

```
[ Delivery Created ] (from Flow A claim)
       │
       ▼  GET /api/logistics/available-tasks (Bearer <Volunteer JWT>)
[ Volunteer UI ] (VolunteerDashboard.tsx)
       │
       ▼  POST /api/logistics/accept/{delivery_id}
[ Task Assigned ] Delivery status updated to "in_progress"
       │
       ▼  Volunteer arrives at Restaurant counter
       │  POST /api/logistics/confirm-pickup (otp=pickup_otp, temp=63.5°C)
[ Pickup Verified ]
       ├── Delivery status -> "picked_up"
       ├── TemperatureLog logged (stage="ngo_pickup")
       ├── Listing status -> "picked_up"
       ▼
       Volunteer transports insulated container to NGO kitchen
       │  POST /api/logistics/confirm-delivery (otp=delivery_otp, temp=61.2°C)
[ Delivery Completed ]
       ├── Delivery status -> "delivered"
       ├── Claim status -> "completed"
       ├── Final destination TemperatureLog logged (stage="ngo_delivery")
       ├── Volunteer delivery count & TrustScore incremented
       └── Live Impact Metrics updated (kg rescued, avoided CO2e)
```

---

## 3. Database Consistency Audit

All components read from and write to the single shared SQLite database:
`c:\Users\haris\Documents\zero_waste Food\backend\anndaan.db`

| Entity Model | Table Name | Purpose | Synchronization Verified |
|---|---|---|---|
| `FoodListing` | `food_listings` | Free social donations for NGOs | YES |
| `DonationClaim` | `donation_claims` | NGO portion reservations & allocations | YES |
| `Delivery` | `deliveries` | Volunteer pickup/delivery logistics & OTPs | YES |
| `RescueListing` | `rescue_listings` | Commercial surplus deals with dynamic pricing | YES |
| `CustomerOrder` | `customer_orders` | Customer purchases & pickup tokens | YES |
| `PaymentRecord` | `payment_records` | Financial audit ledger | YES |
| `TemperatureLog` | `temperature_logs` | HACCP & FSSAI cold/hot chain compliance | YES |
| `AuditLog` | `audit_logs` | Immutable audit trail across all transactions | YES |

---

## 4. Identified Gaps & Required Code Fixes

1. **`backend/app/routers/rescue.py`:**
   - In `create_listing`, set `initial_status = "available"` when temperature is compliant and AI visual inspection passes. Informational flags must not suppress availability.
   - In `get_listings`, allow `status_filter="available"` to return both `"available"` and `"pending_inspection"` records with remaining servings.
2. **`backend/app/routers/matching.py`:**
   - In `claim_food_listing`, calculate `remaining_servings = listing.estimated_servings - req.claimed_servings`.
   - Update `listing.estimated_servings = max(0, remaining_servings)`.
   - If `remaining_servings > 0`, keep status as `"available"` so remaining portions can be claimed. If `0`, set to `"claimed"`.
   - In `get_claims`, scope results by authenticated role: NGOs only see their own claims; Donors see claims for their listings; Admins see all.
3. **`backend/app/routers/logistics.py`:**
   - Apply `to_naive_utc` to OTP expirations to prevent comparison failures.
   - Restrict task visibility so claimed deliveries are dispatched cleanly.
4. **`frontend/src/components/NgoDashboard.tsx` & `DonorDashboard.tsx`:**
   - Ensure dynamic refetching after claim execution and donation creation.

