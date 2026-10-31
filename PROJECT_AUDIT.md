# ANN-DAAN AI – COMPREHENSIVE PROJECT AUDIT & ARCHITECTURAL ASSESSMENT

**Document Version:** 2.0.0  
**Audit Date:** October 31, 2026  
**Audited Directory:** `c:\Users\haris\Documents\zero_waste Food` (Working Tree: `ANN-DAAN-WORKING`)  
**Reference Prototype:** `c:\Users\haris\Documents\zero_waste Food - prototype` (Untouched Read-Only Reference: `ANN-DAAN-PROTOTYPE`)  
**Lead Auditor:** Senior Full-Stack Engineer, AI/ML Architect & Security Specialist  

---

## 1. EXECUTIVE SUMMARY

An extensive audit of the **ANN-DAAN AI** platform was conducted to evaluate its readiness for transition from a local demonstration prototype into a production-ready food rescue and smart redistribution system. 

ANN-DAAN AI is an intelligent ecosystem operating in Jaipur, Rajasthan, designed to address food waste across two synchronized channels:
1. **Commercial Rescue Channel (Channel A):** AI dynamic markdown pricing enabling local residents to purchase high-quality surplus banquet and restaurant meals at steep discounts.
2. **Social Rescue Channel (Channel B):** Seamless, consent-driven redistribution of unsold eligible food to verified NGOs and night shelters with GPS volunteer transport and strict FSSAI food safety verification.

The underlying Next.js (App Router), FastAPI, and SQLAlchemy architecture is sound, feature-rich, and adheres strictly to the emerald-green visual identity (`#14532D`, `#16A34A`, `#DCFCE7`, `#F8FAF8`). However, critical functional and security gaps were uncovered during this audit—most notably OTP leakage in volunteer task feeds, hardcoded bypass codes (`"123456"`), single-timer food expiry heuristics, and lack of strict data tier tagging (`REAL` vs. `TEST` vs. `DEMO`).

---

## 2. DETAILED AUDIT FINDINGS

### 2.1 Existing Functionality (Working & Verified)
* **Full-Stack Architecture:** Next.js 16.4 (React 19 + TypeScript + Tailwind CSS v4) communicating with a FastAPI backend (Uvicorn on port 8000).
* **Role-Based Access Control (RBAC):** Canonical roles (`admin`, `restaurant`/`donor`, `customer`, `ngo`, `volunteer`) with JWT bearer token validation and normalized role matching in `backend/app/services/auth_util.py`.
* **Commercial Rescue Marketplace:** Endpoints for browsing deals, dynamic pricing calculation based on shelf-life decay, order reservation, inventory reservation, and simulated Razorpay payments.
* **Rescue-to-Donation Engine:** `RescueToDonationEngine` verifies restaurant consent (`auto_donate_unsold`), safety status, and shelf-life buffers (>=45 mins), automatically generating non-profit social listings (`FoodListing`) for unsold quantities while isolating financial accounts.
* **NGO Redistribution & Matching:** Haversine distance calculation and capacity-based matching engine for NGOs (`backend/app/services/matching_engine.py`).
* **AI Safety & Quality Inspection:** Image analysis for visual mould detection, presentation scoring, and perceptual dHash image deduplication (`backend/app/services/image_hash.py`).
* **NLP Fraud Sentinel:** Real-time regex and NLP classification of chat messages (`backend/app/services/nlp_fraud.py`) to intercept credential phishing, OTP theft, and illegal fee solicitation.
* **Jaipur Demonstration Pilot:** End-to-end simulation script (`run_demo_scenario.py`) executing MNIT Hostel surplus listing &rarr; AI inspection &rarr; OCR label verification &rarr; Temperature check &rarr; NGO claim &rarr; Volunteer handoff.

---

### 2.2 Critical Security Vulnerabilities
1. **Volunteer Task Feed OTP Leakage (HIGH SEVERITY):**
   * *Location:* `backend/app/routers/logistics.py` &rarr; `get_available_volunteer_tasks()`
   * *Problem:* Both `d.pickup_otp` and `d.delivery_otp` were directly returned in the task JSON payload delivered to any authenticated volunteer.
   * *Risk:* A volunteer could verify pickup and delivery without physically visiting the donor or receiving NGO.
   * *Fix Required:* Redact `pickup_otp` and `delivery_otp` from volunteer task responses. Only the donor must see the pickup OTP, and only the NGO must see the delivery OTP.
2. **Hardcoded Bypass OTPs (CRITICAL SEVERITY):**
   * *Location:* `logistics.py` lines 170 & 220, `marketplace.py` line 528.
   * *Problem:* `req.otp != "123456"` was hardcoded as an emergency backdoor across pickup and delivery verifications.
   * *Risk:* Anyone knowing this constant could bypass physical verification.
   * *Fix Required:* Remove all hardcoded backdoor strings. Enforce 6-digit cryptographic verification with expiration (15 minutes) and attempt limits (max 3 failed tries).
3. **Missing File Upload Handling:**
   * *Location:* `safety.py` and `rescue.py`
   * *Problem:* Endpoints only accepted external image URLs (`image_url: str`) rather than handling multipart file uploads from local camera/files.
   * *Fix Required:* Implement `POST /api/rescue/upload-image` supporting direct file uploads (`UploadFile`) with MIME validation and secure local storage.

---

### 2.3 Database Deficiencies & Data Integrity
1. **Absence of Data Tier Tagging (`REAL`, `TEST`, `DEMO`):**
   * *Problem:* Seed data, test runs, and genuine user transactions all coexisted in the same database without a distinguishing `data_origin` column.
   * *Risk:* Automated test suites or demo resets could inadvertently corrupt or purge authentic user data.
   * *Fix Required:* Add `data_origin` (`REAL`, `TEST`, `DEMO`) with index to `User`, `FoodListing`, `RescueListing`, `CustomerOrder`, `DonationClaim`, and `Delivery`. Provide a designated `POST /api/demo/cleanup-test-data` that only cleans `TEST` records.
2. **Concurrency & Oversell Protection:**
   * *Current state:* Uses `.with_for_update()` in SQLite.
   * *Fix Required:* Ensure compatibility with PostgreSQL table-level locking and atomic inventory decrements.

---

### 2.4 Food Safety & Compliance (FSSAI Surplus Regulations 2019)
1. **Universal Expiry Timer vs. Category Heuristics:**
   * *Problem:* Current prototype applied similar expiry timers across disparate food categories.
   * *Requirement:* Different food types have radically different microbial risk profiles:
     - *Cooked hot meals:* Held at >60°C (max 4 hours); ambient consumption window max 2 hours.
     - *Chilled cooked meals:* Maintained at <4°C (max 24 hours).
     - *Bakery/Ambient:* Handcrafted baked goods max 12–24 hours.
     - *Fresh produce:* Uncut fruits/vegetables max 24–48 hours.
   * *Fix Required:* Implement `validate_food_safety_shelf_life()` in `safety.py` and `rescue.py` enforcing category-specific temperature and shelf-life thresholds.

---

### 2.5 Dynamic Pricing Engine Assessment
* **Explainability vs. ML:** The rule-based engine in `pricing_engine.py` calculates dynamic markdowns based on remaining hours, batch size, and category decay factors.
* **Enhancement:** Ensure transparent attribution indicating "Rule-Based Dynamic Pricing" with configurable administrator boundaries (e.g., minimum 20% discount, maximum 80% discount, price floors). Persist all adjustments into `price_adjustment_logs`.

---

## 3. REQUIRED IMPLEMENTATION PLAN (PHASE 2 - 20)

| Phase | Core Objective | Key Deliverables & Action Items |
|---|---|---|
| **Phase 2** | UI Preservation & Hardening | Maintain green/white branding (`#14532D`, `#16A34A`), verify all navigation buttons, remove fake timers and mock banners. |
| **Phase 3** | Robust Authentication & RBAC | Strict database-backed authentication, verified tokens, demo role accounts, complete permission isolation. |
| **Phase 4** | Data Schema & Tiering | Add `data_origin` (`REAL`, `TEST`, `DEMO`) across all key entities; ensure PostgreSQL schema compatibility. |
| **Phase 5** | Restaurant Management | Profile CRUD, FSSAI verification, photo uploads, listing management with ownership enforcement. |
| **Phase 6** | AI Dynamic Rescue Pricing | Category decay rules, markdown logs, admin price boundary controls, transparent factor explanations. |
| **Phase 7** | Customer Marketplace | Atomic cart reservation, oversell prevention, search/filter, cancellation policy with inventory release. |
| **Phase 8** | Payment Sandbox | Simulated Razorpay sandbox, idempotency, refund processing on cancellation, immutable payment logs. |
| **Phase 9** | Rescue-to-Donation Engine | Prior consent enforcement, safety hold checks, strict channel separation, auto-creation of social listings. |
| **Phase 10** | NGO Distribution Portal | Verified claims, duplicate-claim prevention via atomic transactions, collection scheduling. |
| **Phase 11** | Volunteer Logistics & OTP | Redact OTP from task feed, enforce 15-min expiry and max 3 attempts, separate pickup/delivery verification events. |
| **Phase 12** | Food Safety & Temperature | Category-specific expiry rules, digital probe logs, mandatory FSSAI preliminary screening disclaimer. |
| **Phase 13** | AI Vision & OCR Engine | File upload endpoint, perceptual dHash duplicate detection, OCR text extraction, admin quarantine workflow. |
| **Phase 14** | Fraud Sentinel | Phishing/OTP theft pattern matching, duplicate image alerts, price inflation flags, admin triage system. |
| **Phase 15** | Admin Control Centre | Real DB analytics (no hardcoded counts), user verification, fraud alert triage, audit logs. |
| **Phase 16** | Environmental Impact | Real DB aggregation of kg rescued and meals saved, separated commercial vs donation metrics, net CO2e calculations. |
| **Phase 17** | Data Isolation & Demo Mode | Clear UI badge for demo entities, isolated test data reset (`POST /api/demo/cleanup-test-data`). |
| **Phase 18** | End-to-End Automated Testing | 100% automated test coverage of Workflows A, B, C, and D in pytest. |
| **Phase 19** | Production Architecture | Configurable adapters, `.env.example`, database migration scripts. |
| **Phase 20** | Deliverables & Documentation | Generate all 9 mandatory documents and Windows startup scripts. |

---

*This audit concludes Phase 1. Implementation proceeds strictly within `ANN-DAAN-WORKING` without modifying `ANN-DAAN-PROTOTYPE`.*

