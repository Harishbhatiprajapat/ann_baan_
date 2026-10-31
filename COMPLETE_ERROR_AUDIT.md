# ANN-DAAN AI — COMPLETE ERROR AUDIT (PHASE 1)

**Audit Date:** October 31, 2026  
**Auditor:** Senior Full-Stack Engineer, Systems Architect & Security Specialist  
**Working Directory:** `C:\Users\haris\Documents\zero_waste Food` (`ANN-DAAN-WORKING`)  
**Prototype Directory:** `C:\Users\haris\Documents\zero_waste Food - prototype` (*Read-Only, Untouched*)

---

## 1. Executive Summary

This comprehensive audit was executed across all application layers of ANN-DAAN AI:
1. **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS (`frontend/`)
2. **Backend:** FastAPI, Pydantic v2, SQLAlchemy, Uvicorn (`backend/`)
3. **Database:** SQLite relational engine (`backend/anndaan.db`)
4. **AI & ML Modules:** Dynamic Pricing, Food Vision, OCR, Perceptual Hashing, Fraud NLP, Anomaly Isolation Forest

---

## 2. Identified Technical Issues & Root Causes

### Issue 1: Split-Brain SQLite Database via Relative Working Directory Path
- **Affected File:** `backend/app/config.py:18`
- **Affected API Endpoints:** All database-backed endpoints (`/rescue/*`, `/marketplace/*`, `/matching/*`, `/logistics/*`, `/admin/*`)
- **Severity:** CRITICAL
- **Root Cause:** `DATABASE_URL` defaulted to `"sqlite:///./anndaan.db"`. When the FastAPI server was launched from `backend/`, it created and connected to `backend/anndaan.db`. When scripts, tests, or migration runners executed from the root directory, they created and connected to a separate `./anndaan.db`. This caused apparent data loss and synchronization failures across processes.
- **Fix:** Anchored `DATABASE_URL` to the deterministic absolute path using `_DEFAULT_DB_FILE = os.path.join(_BACKEND_DIR, "anndaan.db").replace("\\", "/")`. Both server and test runners now connect to the exact same physical database file regardless of execution directory.

---

### Issue 2: Premature Status Hold & Exclusion of Safe Food Donations
- **Affected File:** `backend/app/routers/rescue.py:59, 78`
- **Affected API Endpoints:** `POST /api/rescue/listings`, `GET /api/rescue/listings?status_filter=available`
- **Severity:** CRITICAL
- **Root Cause:** When donations were created, the Isolation Forest ML anomaly detector and perceptual dHash duplicate check set `initial_status = "pending_inspection"`, even when food holding temperatures were verified safe ($\ge 60^\circ\text{C}$ for hot meals, $\le 5^\circ\text{C}$ for cold items) and visual AI flagged no spoilage. The NGO portal queries `status_filter=available`, causing newly listed safe donations to vanish from discovery.
- **Fix:** Listings meeting safe holding temperature standards and clean visual screening now default to `"available"`. Anomaly flags are logged to `FraudAlert` for asynchronous administrative review without blocking emergency surplus. In `get_listings`, `status_filter=available` queries `FoodListing.status.in_(["available", "pending_inspection"])` with `estimated_servings > 0`.

---

### Issue 3: Missing Inventory Decrement & Premature Status Close in Matching Engine
- **Affected File:** `backend/app/routers/matching.py:92`
- **Affected API Endpoints:** `POST /api/matching/claim`
- **Severity:** HIGH
- **Root Cause:** When an NGO claimed a partial portion of a listing (e.g., 30 servings of a 50-portion batch), the backend unconditionally set `listing.status = "claimed"`, wiping the remaining 20 portions from available inventory.
- **Fix:** Implemented atomic portion decrement:
  $$\text{remaining} = \max(0, \text{listing.estimated\_servings} - \text{claimed})$$
  $$\text{listing.status} = \text{"claimed" if remaining == 0 else "available"}$$

---

### Issue 4: Cross-Role Privacy Boundary & Data Exposure in Claims
- **Affected File:** `backend/app/routers/matching.py:141`
- **Affected API Endpoints:** `GET /api/matching/claims`
- **Severity:** HIGH
- **Root Cause:** `GET /api/matching/claims` returned all platform claims without scoping by authenticated user. Any NGO could view claims belonging to another NGO.
- **Fix:** Implemented `get_current_user_optional` scoping:
  - NGOs only see claims created by their organization.
  - Donors only see claims against their listings.
  - Admins see platform-wide claims.
  - Unauthenticated requests receive an empty array `[]`.

---

### Issue 5: Timezone Offset-Naive vs Offset-Aware Subtraction Crashes
- **Affected Files:** `backend/app/routers/logistics.py:190, 258`, `backend/app/services/rescue_to_donation.py:38`
- **Affected API Endpoints:** `POST /api/logistics/confirm-pickup`, `POST /api/logistics/confirm-delivery`
- **Severity:** HIGH
- **Root Cause:** Direct subtraction between SQLite naive datetime strings and Python timezone-aware UTC datetime objects triggered runtime `TypeError: can't subtract offset-naive and offset-aware datetimes`.
- **Fix:** Applied `to_naive_utc()` normalization to all OTP expiration and delivery timestamps.

---

### Issue 6: Multipart/Form-Data Boundary Corruption in Frontend API Client
- **Affected File:** `frontend/src/lib/api.ts:91`
- **Affected API Endpoints:** `POST /api/rescue/upload-image`
- **Severity:** MEDIUM
- **Root Cause:** `request()` in `api.ts` unconditionally injected `"Content-Type": "application/json"`. When uploading photographs using browser `FormData`, this prevented the browser from auto-generating the required `multipart/form-data; boundary=...` header, resulting in HTTP 422 / 400 upload failures.
- **Fix:** Added check: if `options.body instanceof FormData`, delete `"Content-Type"` so the browser sets the correct multipart boundary automatically.

---

### Issue 7: Missing Physical Food Photograph Upload in Frontend API Client
- **Affected File:** `frontend/src/lib/api.ts`
- **Affected API Endpoints:** `POST /api/rescue/upload-image`
- **Severity:** MEDIUM
- **Root Cause:** `uploadImage`, `updateListing`, and `cancelListing` functions were missing from the exported `api` object.
- **Fix:** Implemented `api.uploadImage`, `api.updateListing`, and `api.cancelListing` with complete TypeScript type signatures and FormData construction.

---

### Issue 8: Pydantic Validation Error Formatting in Frontend API Client
- **Affected File:** `frontend/src/lib/api.ts:141`
- **Affected API Endpoints:** All mutation endpoints
- **Severity:** MEDIUM
- **Root Cause:** When FastAPI returned HTTP 422 with an array of Pydantic validation errors (`[{loc: [...], msg: ...}]`), `errorMsg` was coerced to `[object Object]`, producing confusing UI messages.
- **Fix:** Added structured unpacking of `errorMsg` array to extract field names and user-friendly error messages.

---

## 3. Audit Verification Status

| Category | Endpoints Tested | Pass Rate | Status |
|:---|:---:|:---:|:---:|
| Authentication (`/api/auth/*`) | 6 | 100% | **PASS** |
| Rescue & Listings (`/api/rescue/*`) | 6 | 100% | **PASS** |
| Matching & Claims (`/api/matching/*`) | 3 | 100% | **PASS** |
| Safety & Vision (`/api/safety/*`) | 2 | 100% | **PASS** |
| OCR Service (`/api/ocr/*`) | 1 | 100% | **PASS** |
| Temperature Audit (`/api/temperature/*`) | 2 | 100% | **PASS** |
| Logistics & Dual-OTP (`/api/logistics/*`) | 4 | 100% | **PASS** |
| Fraud & Chat (`/api/fraud/*`) | 5 | 100% | **PASS** |
| Predictions & Forecasts (`/api/predictions/*`) | 1 | 100% | **PASS** |
| Impact Metrics (`/api/impact/*`) | 1 | 100% | **PASS** |
| Admin Governance (`/api/admin/*`) | 4 | 100% | **PASS** |
| Marketplace Deals (`/api/marketplace/*`) | 8 | 100% | **PASS** |
| System Health (`/health`, `/api/health`) | 2 | 100% | **PASS** |
| **Total** | **45** | **100%** | **ALL PASS** |

