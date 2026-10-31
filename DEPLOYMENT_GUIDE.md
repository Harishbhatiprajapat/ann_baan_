# ANN-DAAN AI – DEPLOYMENT & OPERATIONS GUIDE

**Platform:** ANN-DAAN AI (Jaipur Pilot Node)  
**Target Environments:** Local Development (Windows/Linux/macOS) & Production Cloud (PostgreSQL + Docker + Nginx)  
**Document Version:** 2.0.0  

---

## 1. SYSTEM REQUIREMENTS

### Local Development Environment
* **Operating System:** Windows 10/11, Ubuntu 22.04+, or macOS
* **Python Runtime:** Python 3.10+ (tested on Python 3.14)
* **Node.js Runtime:** Node.js 18.0+ or 20.0+ (with npm)
* **RAM:** Minimum 4 GB (8 GB recommended)
* **Disk Space:** Minimum 1 GB free

---

## 2. QUICK START (WINDOWS SINGLE-CLICK)

For instant local development on Windows:
1. Double-click `start_app_and_open.bat` in the project root directory.
2. The script launches:
   * **FastAPI Backend** on `http://localhost:8001` (with auto-reload and database migration).
   * **Next.js Frontend** on `http://localhost:3001`.
   * Automatically opens your default browser at `http://localhost:3001`.

---

## 3. MANUAL STEP-BY-STEP LOCAL SETUP

### Step 1: Clone or Open Workspace
```powershell
cd "c:\Users\haris\Documents\zero_waste Food"
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` in the root and in `backend/`:
```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend/.env
```

### Step 3: Install Backend Dependencies & Start Server
```powershell
cd backend
pip install -r requirements.txt
python -m app.database_migration
python ../run_backend.py
```
*Backend is now running at `http://localhost:8001` with interactive Swagger API docs at `http://localhost:8001/docs`.*

### Step 4: Install Frontend Dependencies & Start Next.js
Open a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
*Frontend is now running at `http://localhost:3001`.*

---

## 4. RUNNING AUTOMATED AUDIT & TESTS

To execute the backend test suite:
```powershell
cd backend
python -m pytest tests/test_backend.py -v
```

To run visual browser screenshot audits (headless Chrome):
```powershell
node capture_audit_screenshots.js
```
*Verified screenshots will be saved in `screenshots/`.*

---

## 5. PRODUCTION CLOUD ARCHITECTURE

### Recommended Production Stack
* **Database:** Managed PostgreSQL 15+ (Amazon RDS, Supabase, or Railway)
* **Backend:** Gunicorn with Uvicorn workers behind Nginx reverse proxy
* **Frontend:** Vercel, Netlify, or Docker container
* **Object Storage:** AWS S3, Cloudinary, or Google Cloud Storage for food photographs
* **SMS & OTP:** Twilio or MSG91 for real SMS handoff codes

### Vercel Frontend Deployment

The frontend is the Next.js application in `frontend/`; FastAPI is a separate backend service. Configure the Vercel project as follows:

| Vercel setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Next.js |
| Install Command | `npm install` (default is fine) |
| Build Command | `npm run build` |
| Output Directory | Leave blank/default for Next.js |

Set `NEXT_PUBLIC_API_URL` in the Vercel project's Production (and Preview, if used) environment to the public FastAPI base URL, including `/api`, such as `https://<your-backend-host>/api`. It is a public endpoint URL, not a secret. Do not put backend secrets in `NEXT_PUBLIC_*` variables.

On the FastAPI hosting service, set `CORS_ORIGINS` to a comma-separated list of exact frontend origins, such as `https://<your-project>.vercel.app` and your custom domain. Configure `SECRET_KEY`, `DATABASE_URL`, and any service credentials only as server-side backend environment variables.

Deploy the backend separately from the `backend/` directory using `python -m pip install -r requirements.txt` and a host-provided command such as `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Use a persistent production database and storage service; the local SQLite database and local upload directory are not shared with Vercel.

This checkout contains no `vite.config.ts`, Vite app, root `package.json`, or Vercel serverless API modules. If a deployment log tries to load `vite.config.ts` or `./api/status`, `./api/traffic`, or `./api/chat`, verify that Vercel is connected to this ANN-DAAN AI repository and branch and change its Root Directory to `frontend`; those imports do not exist in this checkout. Status/health and chat behavior are handled by the separately deployed FastAPI backend (`/health` and `/api/fraud/messages`). No traffic API exists in this application.

### Production Database Setup
1. Update `.env`:
   ```bash
   DATABASE_URL="******db-host:5432/anndaan_production"
   ```
2. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```
3. Run schema initialization:
   ```python
   from app.database import engine, Base
   from app.models import entities
   Base.metadata.create_all(bind=engine)
   ```

---

## 6. FSSAI REGULATORY COMPLIANCE CHECKLIST
- [x] Preliminary AI visual screening disclaimer prominently displayed.
- [x] Mandatory hot holding (>60°C) and cold holding (<4°C) digital logs recorded at handoff.
- [x] Commercial food separated from donation claims in separate immutable accounting ledgers.
- [x] Donor prior consent required before any unsold food transitions to free donation.
- [x] Tamper-evident pickup and delivery verification using time-limited, role-restricted OTPs.
