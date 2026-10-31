# ANN-DAAN AI: Initial Technical Audit Report (Phase 1)
**Date:** October 30, 2026  
**Auditor:** Senior QA Engineer, Security Auditor & Full-Stack Evaluator  
**Status:** Pre-Remediation Inspection Complete

---

## 1. Executive Summary

ANN-DAAN AI is an intelligent surplus food redistribution platform engineered for the Jaipur, Rajasthan pilot node under FSSAI (Recovery and Distribution of Surplus Food) Regulations 2019. The application implements a dual-channel architecture:
1. **Commercial Rescue:** Affordable meals for consumers at dynamic discounts (50-70% off) through restaurants with simulated Razorpay payments.
2. **Social Rescue:** 100% free food donation through verified NGOs and shelters.

An end-to-end inspection of the repository was conducted before applying modifications.

---

## 2. Architecture & Component Inventory

| Layer | Technology | Key Components | Connection Status |
|---|---|---|---|
| **Frontend** | Next.js 16.4.3 (Webpack), React 19, TypeScript, Tailwind CSS | App Router (`page.tsx`), 10 Core Views & Dashboards | **Connected** to FastAPI backend |
| **Backend API** | Python FastAPI, Uvicorn, Pydantic v2 | 13 Routers (`auth`, `rescue`, `matching`, `safety`, `ocr`, `temperature`, `fraud`, `logistics`, `predictions`, `impact`, `admin`, `demo`, `marketplace`) | **Connected** via REST + CORS |
| **Database** | SQLite + C-Level Haversine SQL extensions | 20 Relational Models in `entities.py`, SQLite session pooling | **Connected** to `anndaan.db` |
| **AI / ML** | Scikit-Learn, Pillow, Heuristic Spectral Vision | `IsolationForest`, `RandomForestRegressor`, perceptual `dHash`, label OCR parser, dynamic pricing engine | **Operational** with local fallbacks |

---

## 3. Findings & Discovered Gaps (Pre-Remediation)

### Critical & High Severity Issues
1. **Missing Interactive Auth UI:**
   - While the navbar supported instant role-switching, there was no user-facing UI modal/view for interactive **Registration** (with Indian mobile OTP), **Login** (with validation error feedback), or **Forgot Password / Password Reset**.
2. **Missing Auth Endpoints:**
   - In `backend/app/routers/auth.py`, no endpoints existed for `POST /auth/forgot-password` and `POST /auth/reset-password`.
   - In `backend/app/routers/auth.py`, registering as a `"customer"` did not automatically instantiate a `CustomerProfile`, nor did `/auth/me` return customer profile fields.
   - No `PUT /auth/profile` endpoint existed for profile updates.
3. **Missing Order Cancellation & Refund Workflow:**
   - In `backend/app/routers/marketplace.py`, no endpoint existed to cancel an order (`POST /marketplace/orders/cancel`).
   - Customers could not cancel an accidental reservation or view refund status (`rfnd_rzp_...`), nor was inventory restored to the `RescueListing`.

### Medium Severity Issues
1. **Missing Profile Management Modal:**
   - Users had no way to view and edit their address, dietary preferences, or vehicle/capacity parameters from the UI.
2. **Deprecation Warnings:**
   - Extensive warnings regarding `datetime.datetime.utcnow()` in Python 3.14.
   - Pydantic V2 class-based `Config` deprecation warning in `FoodListingResponse`.
   - FastAPI `@app.on_event("startup")` deprecation warning in `main.py`.

### Low Severity Issues
1. **Console Output Character Encoding:**
   - Windows console `cp1252` encoding threw `UnicodeEncodeError` when printing currency symbol `₹` from CLI scripts (resolved in `run_demo_scenario.py` with UTF-8 reconfigure).

---

## 4. Planned Remediation Plan

1. **Backend Enhancements:**
   - Add `POST /api/auth/forgot-password` and `POST /api/auth/reset-password`.
   - Add `PUT /api/auth/profile` to allow updating profile data.
   - Add `POST /api/marketplace/orders/cancel` to cancel orders, release reserved/sold inventory, and issue simulated refunds.
   - Ensure `CustomerProfile` is created and returned across all auth routes.
2. **Frontend Enhancements:**
   - Build a comprehensive, modern **`AuthModal.tsx`** supporting Login, Registration (with Indian phone & OTP), and Forgot Password.
   - Build a **`ProfileModal.tsx`** allowing users to inspect and update their active profile settings.
   - Wire up cancellation & refund status display in `CustomerDashboard.tsx`.
   - Add "Sign In / Register" and "Profile Settings" buttons to `Navbar.tsx`.
3. **Automated Testing & Screenshots:**
   - Spin up backend on port 8000 and frontend on port 3000.
   - Run headless Chrome automation to test and take high-resolution screenshots of all 10 views/pages across desktop and mobile viewports.
   - Execute all AI feature tests, database checks, security tests, and Section 16/20 end-to-end workflows.
   - Compile findings into `ANN_DAAN_AI_FINAL_QA_REPORT.md`.

