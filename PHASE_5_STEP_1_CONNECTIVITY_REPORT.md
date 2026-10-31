# ANN-DAAN AI: PHASE 5 STEP 1 REPORT
## Critical Bug Fix: Commercial Rescue Deal Creation – "Failed to fetch"

**Report Date:** October 31, 2026  
**Status:** COMPLETED & VERIFIED  
**Target Environment:** `c:\Users\haris\Documents\zero_waste Food` (`ANN-DAAN-WORKING`)  
**Reference Prototype:** `c:\Users\haris\Documents\zero_waste Food - prototype` (*Preserved, Untouched*)

---

## 1. Executive Summary

When restaurant partners submitted the **"List Commercial Rescue Deal"** modal in the Donor / Restaurant Dashboard (`/dashboard`), the submission failed with an uninformative client-side error:
```
Error creating commercial rescue deal: Failed to fetch
```
An independent engineering investigation revealed that this was caused by an unhandled Python datetime timezone arithmetic exception on the backend (`TypeError: can't subtract offset-naive and offset-aware datetimes`). When this 500 Internal Server Error was raised, Starlette's default exception handler emitted a raw HTTP 500 response without CORS headers. As a result, modern browsers blocked the response under the Cross-Origin Resource Sharing policy, surfacing in the client JavaScript engine as a network `TypeError: Failed to fetch`.

Both the root-cause datetime mismatch, the CORS header propagation during 500 exceptions, backend input validations, client-side pre-validations, and UI feedback have been completely resolved and tested.

All 9/9 verification tests in the Phase 5 Step 1 test suite passed with 100% compliance.

---

## 2. Root Cause Analysis

### 2.1 The Datetime Subtraction Exception
1. The frontend (`DonorDashboard.tsx`) serialized the user's deadline into an ISO 8601 string with UTC indicator `"Z"` (e.g. `2026-10-30T22:26:59.509Z`).
2. Pydantic v2 deserialized this ISO string into an **offset-aware** `datetime.datetime` object (`tzinfo=datetime.timezone.utc`).
3. In `backend/app/routers/marketplace.py:232`, the backend dynamic pricing logic computed the time left before expiry:
   ```python
   now = datetime.datetime.utcnow()  # Offset-naive datetime
   hours_left = max(0.5, (req.pickup_deadline - now).total_seconds() / 3600.0)
   ```
4. In Python 3.12+, subtracting an offset-aware datetime from an offset-naive datetime raises:
   ```python
   TypeError: can't subtract offset-naive and offset-aware datetimes
   ```

### 2.2 The Starlette CORS Masking Effect
When an uncaught exception occurred in a FastAPI endpoint handler:
- Starlette's base `ServerErrorMiddleware` intercepted the exception and generated a default 500 internal server error.
- Because the exception bypassed outer application response middleware, `CORSMiddleware` never attached the `Access-Control-Allow-Origin: http://localhost:3000` header to the 500 response.
- The browser received an HTTP 500 lacking CORS credentials, considered it an illegal cross-origin request, and raised a generic `TypeError: Failed to fetch`, masking the true server-side stack trace.

---

## 3. Files Modified & Exact Changes

### 3.1 `backend/app/services/auth_util.py`
Created a universal, resilient timezone normalizer `to_naive_utc(dt)`:
```python
def to_naive_utc(dt: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """
    Safely normalizes incoming datetime (whether offset-aware or offset-naive)
    into a naive UTC datetime compatible with SQLite and Python arithmetic.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt
```

### 3.2 `backend/app/routers/marketplace.py`
1. **Datetime Normalization:**
   ```python
   safe_deadline = to_naive_utc(req.pickup_deadline)
   safe_prep = to_naive_utc(req.preparation_time)
   now = datetime.datetime.utcnow()
   hours_left = max(0.5, (safe_deadline - now).total_seconds() / 3600.0)
   ```
2. **Business Rule Validations:**
   - Ensured `original_price > 0`.
   - Ensured `total_quantity > 0`.
   - Verified `safe_deadline > now` (cannot publish expired deals).
   - Saved `auto_donate_unsold` boolean flag and initialized `donation_transition_status = "eligible" if auto_donate else "not_applicable"`.

### 3.3 `backend/app/routers/rescue.py`
Applied `to_naive_utc()` to `req.expiry_time` and `req.preparation_time` in free NGO rescue listing creation to eliminate identical comparison issues across the entire platform.

### 3.4 `backend/app/schemas/schemas.py`
Added Pydantic v2 schema constraints to `RescueListingCreate`:
```python
original_price: float = Field(..., gt=0, description="Original retail price before discount (must be > 0)")
total_quantity: int = Field(..., gt=0, description="Available portions (must be > 0)")
```

### 3.5 `backend/app/main.py`
Added a global exception handler to guarantee CORS headers on any unexpected 500 error:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later or contact support."}
    )
```

### 3.6 `frontend/src/lib/api.ts`
1. Replaced generic browser error messages with descriptive user-facing network feedback:
   ```typescript
   if (err instanceof TypeError && err.message.includes('fetch')) {
       throw new Error('Unable to connect to the server. Please check that the backend is running.');
   }
   ```
2. Formatted Pydantic validation error arrays into clear, human-readable strings (`"field: message"`).
3. Provided explicit status messages for 401 Unauthorized and 403 Forbidden responses.

### 3.7 `frontend/src/components/DonorDashboard.tsx`
1. Added modal error banner (`commModalError`) so validation and server messages render inside the modal instead of disruptive browser alert popups.
2. Added submit loading spinner state (`commSubmitting`) disabling double-submissions.
3. Added client-side pre-validation checking that `originalPrice > 0` and `portions >= 1` before triggering API calls.

---

## 4. Verification & Test Execution Results

### 4.1 Automated End-to-End Test Suite (`test_phase5_step1.py`)

| Test ID | Test Name | Expected Behavior | Actual Result | Status |
|---|---|---|---|---|
| **Test A** | Create Valid Commercial Deal | HTTP 200 OK & record created in SQLite | HTTP 200, Listing ID #43, Rescue Price = Rs. 115.0 | **PASS** |
| **Test B** | Page Refresh / Roster Query | Deal present in active listings | Deal #43 present in `/api/marketplace/listings/restaurant` | **PASS** |
| **Test C** | SQLite Durability Across Restarts | Record persisted in SQLite table with active status | Status='active', Original Price = Rs. 240.0 | **PASS** |
| **Test D** | Reject Negative or Zero Price | HTTP 422 Unprocessable Entity | HTTP 422 (`original_price: Input should be greater than 0`) | **PASS** |
| **Test E** | Reject Zero or Negative Quantity | HTTP 422 Unprocessable Entity | HTTP 422 (`total_quantity: Input should be greater than 0`) | **PASS** |
| **Test F** | Reject Unauthenticated Creation | HTTP 401 Unauthorized | HTTP 401 (`Authentication credentials not provided`) | **PASS** |
| **Test G** | Reject Customer Role | HTTP 403 Forbidden | HTTP 403 (`Operation requires roles: donor, admin`) | **PASS** |
| **Test H** | Automatic Donation Opt-In Isolation | Consent flags preserved (`1`/`0`) | Listing #43 (`auto_donate_unsold=1`, `eligible`), Listing #44 (`auto_donate_unsold=0`, `not_applicable`) | **PASS** |
| **Test I** | Marketplace Public Retrieval | Deal appears in customer feed with dynamic discount | Deal #43 visible at Rs. 100.0 (58.3% off) | **PASS** |

**Summary: 9 executed, 9 PASSED, 0 FAILED (100% Pass Rate)**

---

### 4.2 Browser Automation (Puppeteer Headless Chrome)
Executed full UI submission via headless browser (`test_deal_submit.js`):
- Logged in as `restaurant@jaipur-demo.in`.
- Opened `/dashboard` (Donor View).
- Clicked **"List Commercial Rescue Deal"** modal trigger.
- Filled Dish Title, Category, Original Price (`Rs. 250`), Portions (`10`), and submitted.
- Result: **HTTP 200 OK**, zero console errors, zero uncaught promise rejections. Deal successfully persisted into SQLite database.

---

### 4.3 Backend Pytest Suite
Ran the full backend test suite (`pytest`):
```
32 passed in 8.77s
```
Zero regressions detected across all 32 existing tests.

---

## 5. Remaining Items & Phase 5 Readiness

1. **Step 1 is completely resolved:** Commercial rescue deals create reliably, persist in SQLite, enforce RBAC, compute dynamic discounts, and display properly to customers.
2. **Phase 5 Step 2 Next:**
   - Proceed to **Commercial Deal Purchase Workflow** (Customer claim, Razorpay test payment integration, stock decrement, QR rescue code generation, and rescue completion).

