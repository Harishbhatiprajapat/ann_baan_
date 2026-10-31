# ANN-DAAN AI: AI-Powered Food Rescue, Safety, Fraud Detection & Smart Redistribution Platform

**Pilot Regional Node:** Jaipur, Rajasthan, India  
**Compliance Standard:** FSSAI (Recovery and Distribution of Surplus Food) Regulations, 2019 (Schedule I & II)  
**Core Innovations:** Dual-Channel Architecture (Commercial Rescue + Social Rescue), AI Dynamic Rescue Pricing, Surprise Rescue Bags, Rescue-to-Donation Engine  
**Status:** Functional local pilot; production use still requires PostgreSQL/PostGIS, external maps, and deployment hardening.

---

## 1. Quick Start & Execution

To launch both backend and frontend servers simultaneously and open the application in your browser:

### Option A: Windows Single-Click (Recommended)
Double-click `start_app_and_open.bat` in the root folder.
* **Frontend:** `http://localhost:3001`
* **Backend API & Swagger Docs:** `http://localhost:8001/docs`

### Option B: Manual Command Line
```powershell
# 1. Start FastAPI Backend Service (from root; uses port 8001)
python run_backend.py

# 2. Start Next.js Frontend (in separate terminal)
cd frontend
npm.cmd run dev -- --port 3001
```

### Option C: Run Full Automated Test Suite (34 Tests)
```powershell
cd backend
python -m pytest tests/test_backend.py -v
```

---

## 2. System Architecture & The Core Engines

ANN-DAAN AI operates across two strictly separated channels powered by intelligent engines:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                       ANN-DAAN AI                                      │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│         A. COMMERCIAL RESCUE              │             B. SOCIAL RESCUE               │
│ - Affordable surplus meals for customers  │ - 100% Free redistribution to verified NGOs│
│ - AI Dynamic Markdown (50-70% off)        │ - Shelter meal deficits matching           │
│ - Surprise Rescue Bags (delightful value) │ - 80G compliant donation audit trail       │
│ - Digital payment (simulated Razorpay)    │ - Strictly zero commercial monetization    │
├───────────────────────────────────────────┴────────────────────────────────────────────┤
│                         SHARED SAFETY & VERIFICATION ENGINES                           │
├─────────────────────┬──────────────────────────┬───────────────────────────────────────┤
│ 1. AI Food Rescue   │ 2. AI Safety & Vision    │ 3. AI Fraud & Trust                   │
│ - Surplus schemas   │ - Mould & discoloration  │ - NLP scam & extortion detection      │
│ - Temp thresholds   │ - Seal breach inspection │ - Perceptual dHash photo deduplication│
│ - FSSAI Schedule I  │ - Label OCR & mismatch   │ - Price inflation detection           │
├─────────────────────┴──────────────────────────┴───────────────────────────────────────┤
│ 4. Smart Logistics & Delivery Engine           │ 5. Predictive AI & Pricing Engine     │
│ - PostGIS / Haversine 2-stage matching         │ - AI Dynamic Pricing Formula          │
│ - Dual OTP pickup & drop off verification      │ - Random Forest Surplus & Demand ML   │
│ - Digital thermometer cold-chain telemetry     │ - WRI India GHG Carbon Accounting     │
├────────────────────────────────────────────────┴───────────────────────────────────────┤
│ 6. RESCUE-TO-DONATION ENGINE: Automatically transitions unsold commercial surplus      │
│    (with ≥45m safe shelf-life and restaurant consent) into Social Rescue for NGOs.     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

* **Frontend:** Next.js 16 (App Router, Webpack), React 19, TypeScript, Tailwind CSS v4, Lucide Icons, Recharts.
* **Backend:** Python FastAPI, Pydantic v2, PyJWT (HS256), bcrypt password hashing, SQLAlchemy ORM, Uvicorn ASGI server.
* **Database:** Relational schema supporting SQLite (development) and PostgreSQL + PostGIS (production) with automated migration runner (`database_migration.py`) and data tiering (`REAL`, `TEST`, `DEMO`).
* **AI & Machine Learning:** Scikit-Learn (`RandomForestRegressor`), Pillow (`dHash`), NLP regex/text classification.
* **Security & Compliance:** Role-Based Access Control (RBAC), ownership checks on food listings, single-use 15-minute OTPs with attempt limiting, FSSAI temperature logging (>60°C hot, <4°C cold).

### How this differs from the original proposal

The working implementation uses **FastAPI/Python**, not Node.js. Local development uses **SQLite with Haversine distance calculations**; PostgreSQL/PostGIS is a production direction, not the database currently running. The app includes a commercial discounted-food marketplace alongside the core free NGO donation flow, so keep donations—not paid deals—as the primary zero-waste path. The current local setup does not require Google Maps credentials. Volunteers can open pickup-to-dropoff directions in Google Maps, but the app does not use the Google Maps API or PostGIS geofenced matching.

### Deploying the frontend to Vercel

Deploy [frontend/](./frontend/) as the Vercel project root with the Next.js preset, default install command, `npm run build`, and default Next.js output directory. Set `NEXT_PUBLIC_API_URL` to the separately deployed FastAPI base URL ending in `/api`; configure backend `CORS_ORIGINS` with the Vercel site origin. See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for all settings. This repository does not contain a Vite config or Vercel serverless API handlers.

---

## 4. Demo Accounts & Credentials

| Role | Name | Email | Password |
|---|---|---|---|
| **Admin** | FSSAI Regional Officer (Jaipur Node) | `admin@jaipur-demo.in` | `password123` |
| **Donor / Hostel** | MNIT Jaipur Hostel Mess No. 4 | `hostel@jaipur-demo.in` | `password123` |
| **Restaurant** | Jaipur Heritage Banquet & Dining | `restaurant@jaipur-demo.in` | `password123` |
| **Customer** | Aditi Sharma (Jaipur Resident) | `customer@jaipur-demo.in` | `password123` |
| **NGO** | Jaipur Annapurna Seva Sansthan | `ngo@jaipur-demo.in` | `password123` |
| **Volunteer** | Rahul Meena (Jaipur Logistics) | `volunteer@jaipur-demo.in` | `password123` |

---

## 5. Project Deliverables

1. [PROJECT_AUDIT.md](file:///c:/Users/haris/Documents/zero_waste%20Food/PROJECT_AUDIT.md) – Comprehensive Phase 1 architectural and security audit.
2. [IMPLEMENTATION_REPORT.md](file:///c:/Users/haris/Documents/zero_waste%20Food/IMPLEMENTATION_REPORT.md) – Full implementation report covering all 20 phases.
3. [DATABASE_SCHEMA.md](file:///c:/Users/haris/Documents/zero_waste%20Food/DATABASE_SCHEMA.md) – Complete database schema specification (26 entities and PostgreSQL migration guide).
4. [API_DOCUMENTATION.md](file:///c:/Users/haris/Documents/zero_waste%20Food/API_DOCUMENTATION.md) – REST API documentation with endpoint parameters, authorization, and responses.
5. [TEST_REPORT.md](file:///c:/Users/haris/Documents/zero_waste%20Food/TEST_REPORT.md) – Automated test execution report (32 tests, 100% pass rate).
6. [DEPLOYMENT_GUIDE.md](file:///c:/Users/haris/Documents/zero_waste%20Food/DEPLOYMENT_GUIDE.md) – Local development and production cloud deployment instructions.
7. [DEMO_ACCOUNTS.md](file:///c:/Users/haris/Documents/zero_waste%20Food/DEMO_ACCOUNTS.md) – Directory of pre-configured demo accounts, credentials, and permission matrix.
8. [.env.example](file:///c:/Users/haris/Documents/zero_waste%20Food/.env.example) – Environment variable configuration template.
9. [start_app_and_open.bat](file:///c:/Users/haris/Documents/zero_waste%20Food/start_app_and_open.bat) – Reliable Windows single-click startup script.
