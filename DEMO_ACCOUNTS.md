# ANN-DAAN AI – DEMO ACCOUNTS & CREDENTIALS DIRECTORY

**Environment:** Jaipur Demonstration Pilot  
**Default Password for all Demo Accounts:** `password123`  
**Security Note:** These accounts are pre-configured test fixtures (`data_origin = 'DEMO'`). Do not use these passwords in a public production deployment.

---

## 1. PRE-CONFIGURED DEMO ACCOUNTS

| Role | User Name | Email Address | Password | Typical Testing Purpose |
|---|---|---|---|---|
| **Admin** | FSSAI Regional Officer (Jaipur Node) | `admin@jaipur-demo.in` | `password123` | High-level analytics, fraud alert triage, AI safety reviews, FSSAI verification approval, and audit logs. |
| **Donor / Restaurant** | MNIT Jaipur Hostel Mess No. 4 | `hostel@jaipur-demo.in` | `password123` | Institutional surplus donation, preparation logging, temperature recording, and handoff pickup verification. |
| **Donor / Restaurant** | Jaipur Heritage Banquet & Dining | `restaurant@jaipur-demo.in` | `password123` | Commercial rescue listing creation, dynamic discount management, revenue analytics, and unsold auto-donation consent. |
| **Customer** | Aditi Sharma (Jaipur Resident) | `customer@jaipur-demo.in` | `password123` | Browsing discounted rescue deals, surprise bags, checkout with simulated Razorpay, and pickup OTP redemption. |
| **NGO** | Jaipur Annapurna Seva Sansthan | `ngo@jaipur-demo.in` | `password123` | Browsing free surplus food, AI matching engine recommendations, claiming batches, and receiving handoffs. |
| **Volunteer** | Rahul Meena (Jaipur Logistics) | `volunteer@jaipur-demo.in` | `password123` | On-duty toggle, accepting dispatch tasks, physical OTP verification at donor pickup and NGO drop-off. |

---

## 2. ROLE ACCESS & PERMISSION MATRIX

| Capability / Endpoint | Admin | Restaurant / Donor | Customer | NGO | Volunteer |
|---|:---:|:---:|:---:|:---:|:---:|
| View Home / Landing / Deals | Yes | Yes | Yes | Yes | Yes |
| Purchase Commercial Rescue Deals | Yes | Yes | **Yes** | Yes | Yes |
| Create Surplus / Rescue Listings | Yes | **Yes** | No (403) | No (403) | No (403) |
| Modify / Cancel Own Listings | Yes | **Yes** | No (403) | No (403) | No (403) |
| Modify Another Establishment's Listing | Yes | **No (403)** | No (403) | No (403) | No (403) |
| Claim Free Social Surplus | Yes | No (403) | No (403) | **Yes** | No (403) |
| Accept Volunteer Delivery Task | Yes | No (403) | No (403) | No (403) | **Yes** |
| Verify Delivery Task Hand-off OTP | Yes | Donor only | No (403) | NGO only | **Yes** |
| Access Admin Overview & Analytics | **Yes** | No (403) | No (403) | No (403) | No (403) |
| Triage Fraud Sentinel Alerts | **Yes** | No (403) | No (403) | No (403) | No (403) |
| Override Food Safety AI Flags | **Yes** | No (403) | No (403) | No (403) | No (403) |

---

## 3. HOW TO SWITCH ROLES ON THE FRONTEND

1. Navigate to `http://localhost:3000`.
2. Click the **Role Switcher** in the top navigation bar.
3. Select any role (**Customer**, **Restaurant / Donor**, **NGO Portal**, **Volunteer**, **Admin Control**).
4. The frontend automatically initiates an authenticated session with the backend using the respective demo account token.

