# ANN-DAAN AI – REST API DOCUMENTATION

**Base URL (Local):** `http://localhost:8001/api`
**Swagger Interactive Docs:** `http://localhost:8001/docs`
**OpenAPI Specification:** `http://localhost:8001/openapi.json`
**Authentication Scheme:** HTTP Bearer Header (`Authorization: Bearer <JWT_ACCESS_TOKEN>`)  

---

## 1. AUTHENTICATION & PROFILES (`/api/auth`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register new user (`admin`, `restaurant`/`donor`, `customer`, `ngo`, `volunteer`). |
| `POST` | `/auth/login` | Public | Authenticate user with email and password; returns JWT token. |
| `GET` | `/auth/me` | Authenticated | Retrieve current user profile and role details. |
| `PUT` | `/auth/profile` | Authenticated | Update user name, phone, address, and profile settings. |
| `POST` | `/auth/forgot-password` | Public | Request demo OTP for password reset. |
| `POST` | `/auth/reset-password` | Public | Reset password using valid OTP and new password. |

---

## 2. COMMERCIAL RESCUE MARKETPLACE (`/api/marketplace`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/marketplace/deals` | Public | Browse active discounted surplus deals and surprise bags. |
| `GET` | `/marketplace/deals/{deal_id}` | Public | Retrieve full detail, nutrition, temperature, and restaurant info. |
| `POST` | `/marketplace/calculate-price` | Public | Preview AI dynamic pricing for food parameters. |
| `POST` | `/marketplace/listings` | Restaurant, Admin | Create a discounted rescue listing with automated AI markdown pricing. |
| `POST` | `/marketplace/orders/create` | Customer, Admin | Reserve portions atomically with oversell prevention. |
| `POST` | `/marketplace/orders/pay` | Customer, Admin | Verify simulated Razorpay payment and generate pickup OTP. |
| `POST` | `/marketplace/orders/confirm-pickup` | Restaurant, Admin | Physical handoff verification using customer pickup OTP. |
| `POST` | `/marketplace/orders/cancel` | Customer, Admin | Cancel active order, issue simulated refund, restore inventory. |
| `GET` | `/marketplace/orders/my-orders` | Customer, Admin | View customer's purchase history and cumulative savings. |
| `POST` | `/marketplace/rescue-to-donation/{deal_id}` | Donor, Admin | Transition unsold commercial food into free social donation. |
| `GET` | `/marketplace/analytics/{restaurant_id}` | Donor, Admin | View commercial revenue recovered, sales conversion, and AI velocity. |

---

## 3. SOCIAL RESCUE & FOOD LISTINGS (`/api/rescue`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/rescue/listings` | Public | List available surplus food donations for humanitarian distribution. |
| `GET` | `/rescue/listings/{id}` | Public | Detailed food safety, temperature, and visual inspection report. |
| `POST` | `/rescue/listings` | Donor, Admin | Create a free donation listing with safety and anomaly screening. |
| `PUT` | `/rescue/listings/{id}` | Donor, Admin | Update existing listing (enforces restaurant ownership). |
| `DELETE` | `/rescue/listings/{id}` | Donor, Admin | Cancel existing listing (enforces restaurant ownership). |
| `POST` | `/rescue/upload-image` | Donor, Admin | Upload physical food photograph with size, MIME, and dHash deduplication. |

---

## 4. NGO MATCHING & CLAIMS (`/api/matching`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/matching/recommendations/{id}` | NGO, Admin | Get AI ranked NGO matches based on capacity, distance, and dietary preferences. |
| `POST` | `/matching/claim` | NGO, Admin | Atomically claim donation servings and create logistics delivery dispatch. |
| `GET` | `/matching/my-claims` | NGO, Admin | Retrieve active and completed claims for an authenticated NGO. |
| `POST` | `/matching/cancel-claim/{id}` | NGO, Admin | Cancel claim and release quantity back to available status. |

---

## 5. SMART LOGISTICS & VOLUNTEER (`/api/logistics`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/logistics/available-tasks` | Volunteer, Admin | Retrieve active pickup and delivery tasks (OTPs securely redacted). |
| `GET` | `/logistics/history` | Volunteer, Admin | Retrieve completed volunteer deliveries and transit distance. |
| `POST` | `/logistics/accept/{id}` | Volunteer, Admin | Accept delivery task and initiate navigation. |
| `POST` | `/logistics/confirm-pickup` | Volunteer, Donor | Confirm physical food pickup with donor OTP and temperature reading. |
| `POST` | `/logistics/confirm-delivery` | Volunteer, NGO | Confirm physical food delivery with NGO OTP and temperature reading. |

---

## 6. FOOD SAFETY, TEMPERATURE & AI VISION (`/api/safety`, `/api/temperature`, `/api/ocr`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/safety/inspect` | Public | Preliminary AI screening for mould, discoloration, and packaging damage. |
| `POST` | `/safety/admin-review/{id}` | Admin | Administrative override: approve or quarantine flagged listing. |
| `POST` | `/ocr/extract` | Public | Extract packaging text, manufacturer, and verify use-by expiration dates. |
| `POST` | `/temperature/log` | Authenticated | Record physical thermometer readings with abnormal temperature flagging. |
| `GET` | `/temperature/history/{id}` | Public | Trace continuous cold/hot chain temperature logs for a food batch. |

---

## 7. FRAUD SENTINEL & TRUST ENGINE (`/api/fraud`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/fraud/messages` | Authenticated | Send message scanned by NLP classifier for phishing, OTP theft, and fees. |
| `GET` | `/fraud/messages` | Authenticated | Retrieve message history between two users. |
| `GET` | `/fraud/alerts` | Admin | Retrieve all open and triaged security alerts. |
| `POST` | `/fraud/triage/{id}` | Admin | Triage fraud alert (`under_investigation`, `resolved`, `false_positive`). |
| `GET` | `/fraud/trust-score/{user_id}` | Public | View trust profile, verification badges, and calculated trust score. |

---

## 8. PREDICTIONS, IMPACT & ADMIN CENTRE (`/api/predictions`, `/api/impact`, `/api/admin`, `/api/demo`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/predictions/forecasts` | Public | AI predictive surplus forecast calibrated to Jaipur municipal banquet cycles. |
| `GET` | `/impact/metrics` | Public | Dual-channel impact metrics (commercial sales vs. donations, net CO2e). |
| `GET` | `/admin/overview` | Admin | Aggregate analytics calculated strictly from real database records. |
| `GET` | `/admin/users` | Admin | List all registered platform users with verification status and role filter. |
| `POST` | `/admin/verify-user/{id}` | Admin | Approve or reject FSSAI organisation verification. |
| `GET` | `/admin/audit-logs` | Admin | Retrieve immutable audit trail of all administrative and security actions. |
| `POST` | `/demo/seed` | Public | Seed default demonstration dataset for Jaipur pilot. |
| `POST` | `/demo/run-jaipur-scenario` | Public | Execute end-to-end Section 20 demonstration simulation. |
| `POST` | `/demo/cleanup-test-data` | Public | Purge only `TEST` records without affecting `REAL` or `DEMO` data. |
