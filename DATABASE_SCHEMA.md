# ANN-DAAN AI – DATABASE SCHEMA SPECIFICATION

**Database Engine (Dev):** SQLite with SQLAlchemy 2.0  
**Database Target (Prod):** PostgreSQL 15+ with PostGIS Extension  
**ORM:** SQLAlchemy Declarative Base (`backend/app/models/entities.py`)  
**Data Tiering Field:** `data_origin` (`REAL`, `TEST`, `DEMO`)  

---

## 1. ENTITY-RELATIONSHIP ARCHITECTURE

The ANN-DAAN AI database structure strictly separates Commercial Rescue transactions from Social Rescue donations while maintaining end-to-end traceability under FSSAI regulations.

```mermaid
erDiagram
    User ||--o| DonorProfile : has
    User ||--o| NgoProfile : has
    User ||--o| VolunteerProfile : has
    User ||--o| CustomerProfile : has
    User ||--o| TrustScore : has
    User ||--o{ FoodListing : creates_social
    User ||--o{ RescueListing : creates_commercial
    User ||--o{ CustomerOrder : places_orders
    User ||--o{ DonationClaim : claims_donations
    User ||--o{ Delivery : executes_deliveries
    
    FoodListing ||--o{ FoodImage : contains
    FoodListing ||--o| InspectionReport : evaluated_by
    FoodListing ||--o| OCRResult : verified_by
    FoodListing ||--o{ TemperatureLog : logs_temps
    FoodListing ||--o{ DonationClaim : claimed_via
    
    DonationClaim ||--o| Delivery : fulfills
    
    RescueListing ||--o{ CustomerOrder : orders
    RescueListing ||--o{ PriceAdjustmentLog : markdown_logs
    RescueListing ||--o{ RescueToDonationLog : transition_logs
    RescueListing ||--o| FoodListing : transitions_to
    
    CustomerOrder ||--o{ PaymentRecord : payments
    CustomerOrder ||--o| CustomerReview : reviews
```

---

## 2. DETAILED TABLE DEFINITIONS

### 2.1 Core Identity & Profiles

#### `users`
* `id` (INTEGER, Primary Key, Auto-increment)
* `email` (VARCHAR(255), Unique, Indexed, NOT NULL)
* `phone` (VARCHAR(20), Unique, Indexed, NOT NULL)
* `hashed_password` (VARCHAR(255), NOT NULL)
* `full_name` (VARCHAR(255), NOT NULL)
* `role` (VARCHAR(50), NOT NULL, Default: `'donor'`) — `admin`, `donor`/`restaurant`, `ngo`, `volunteer`, `customer`
* `is_verified` (BOOLEAN, Default: `FALSE`)
* `is_active` (BOOLEAN, Default: `TRUE`)
* `is_suspended` (BOOLEAN, Default: `FALSE`)
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`) — `REAL`, `TEST`, `DEMO`
* `created_at` (DATETIME, Default: UTC Now)
* `updated_at` (DATETIME, OnUpdate: UTC Now)

#### `donor_profiles`
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key &rarr; `users.id`, Unique, NOT NULL)
* `donor_type` (VARCHAR(50)) — `restaurant`, `hotel`, `hostel`, `caterer`, `mess`, `individual`
* `business_name` (VARCHAR(255), NOT NULL)
* `contact_person` (VARCHAR(255))
* `address` (VARCHAR(500), NOT NULL)
* `latitude` (FLOAT, Default: `26.9124`)
* `longitude` (FLOAT, Default: `75.7873`)
* `fssai_number` (VARCHAR(50))
* `fssai_verified` (BOOLEAN, Default: `FALSE`)
* `verification_status` (VARCHAR(50), Default: `'pending'`)

#### `ngo_profiles`
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key &rarr; `users.id`, Unique, NOT NULL)
* `org_name` (VARCHAR(255), NOT NULL)
* `registration_number` (VARCHAR(100), NOT NULL)
* `capacity_meals_per_day` (INTEGER, Default: `200`)
* `address` (VARCHAR(500), NOT NULL)
* `latitude` (FLOAT, Default: `26.9124`)
* `longitude` (FLOAT, Default: `75.7873`)
* `accepts_categories` (VARCHAR(500), Default: `'All'`)
* `dietary_preference` (VARCHAR(50), Default: `'any'`)
* `verification_status` (VARCHAR(50), Default: `'pending'`)

#### `volunteer_profiles`
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key &rarr; `users.id`, Unique, NOT NULL)
* `vehicle_type` (VARCHAR(50), Default: `'bike'`) — `bike`, `car`, `van`, `on_foot`
* `max_carrying_capacity_kg` (FLOAT, Default: `20.0`)
* `is_available` (BOOLEAN, Default: `TRUE`)
* `rating` (FLOAT, Default: `5.0`)
* `total_deliveries` (INTEGER, Default: `0`)

#### `customer_profiles`
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key &rarr; `users.id`, Unique, NOT NULL)
* `address` (VARCHAR(500))
* `dietary_preference` (VARCHAR(50), Default: `'any'`)
* `total_money_saved` (FLOAT, Default: `0.0`)
* `total_meals_purchased` (INTEGER, Default: `0`)

---

### 2.2 Commercial Rescue Marketplace (Channel A)

#### `rescue_listings`
* `id` (INTEGER, Primary Key)
* `restaurant_id` (INTEGER, Foreign Key &rarr; `users.id`, NOT NULL)
* `title` (VARCHAR(255), NOT NULL)
* `description` (TEXT)
* `food_category` (VARCHAR(100), NOT NULL)
* `is_vegetarian` (BOOLEAN, Default: `TRUE`)
* `is_rescue_bag` (BOOLEAN, Default: `FALSE`)
* `original_price` (FLOAT, NOT NULL)
* `current_rescue_price` (FLOAT, NOT NULL)
* `initial_rescue_price` (FLOAT, NOT NULL)
* `discount_percentage` (FLOAT, NOT NULL)
* `dynamic_price_factor` (FLOAT, Default: `0.50`)
* `price_explanation` (TEXT)
* `total_quantity` (INTEGER, NOT NULL)
* `sold_quantity` (INTEGER, Default: `0`)
* `reserved_quantity` (INTEGER, Default: `0`)
* `donated_quantity` (INTEGER, Default: `0`)
* `preparation_time` (DATETIME, NOT NULL)
* `pickup_start` (DATETIME, NOT NULL)
* `pickup_deadline` (DATETIME, NOT NULL)
* `storage_conditions` (VARCHAR(255))
* `current_temperature` (FLOAT)
* `allergen_info` (VARCHAR(500))
* `ingredients` (TEXT)
* `pickup_address` (VARCHAR(500), NOT NULL)
* `pickup_lat` (FLOAT, Default: `26.9124`)
* `pickup_lng` (FLOAT, Default: `75.7873`)
* `image_url` (VARCHAR(500), NOT NULL)
* `image_hash` (VARCHAR(64), Indexed)
* `status` (VARCHAR(50), Default: `'active'`) — `active`, `sold_out`, `transitioned_to_donation`, `completed`, `cancelled`
* `auto_donate_unsold` (BOOLEAN, Default: `TRUE`)
* `donation_transition_status` (VARCHAR(50), Default: `'eligible'`)
* `social_listing_id` (INTEGER, Foreign Key &rarr; `food_listings.id`, Nullable)
* `is_flagged` (BOOLEAN, Default: `FALSE`)
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`)

#### `customer_orders`
* `id` (INTEGER, Primary Key)
* `order_number` (VARCHAR(100), Unique, Indexed, NOT NULL)
* `customer_id` (INTEGER, Foreign Key &rarr; `users.id`, NOT NULL)
* `rescue_listing_id` (INTEGER, Foreign Key &rarr; `rescue_listings.id`, NOT NULL)
* `restaurant_id` (INTEGER, Foreign Key &rarr; `users.id`, NOT NULL)
* `quantity` (INTEGER, NOT NULL, Default: `1`)
* `total_original_amount` (FLOAT, NOT NULL)
* `total_rescue_amount` (FLOAT, NOT NULL)
* `customer_savings` (FLOAT, NOT NULL)
* `platform_fee` (FLOAT, Default: `0.0`)
* `restaurant_payout` (FLOAT, Default: `0.0`)
* `order_status` (VARCHAR(50), Default: `'reserved'`) — `reserved`, `paid`, `ready_for_pickup`, `collected`, `cancelled`, `refunded`
* `payment_status` (VARCHAR(50), Default: `'pending'`) — `pending`, `completed`, `failed`, `refunded`
* `payment_gateway` (VARCHAR(50), Default: `'razorpay_simulated'`)
* `transaction_id` (VARCHAR(100))
* `pickup_otp` (VARCHAR(6), NOT NULL)
* `otp_attempts` (INTEGER, Default: `0`)
* `otp_expires_at` (DATETIME, Nullable)
* `qr_code_hash` (VARCHAR(64))
* `collected_at` (DATETIME, Nullable)
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`)

#### `payment_records`
* `id` (INTEGER, Primary Key)
* `order_id` (INTEGER, Foreign Key &rarr; `customer_orders.id`, NOT NULL)
* `amount` (FLOAT, NOT NULL)
* `currency` (VARCHAR(10), Default: `'INR'`)
* `gateway_order_id` (VARCHAR(100))
* `gateway_payment_id` (VARCHAR(100))
* `gateway_signature` (VARCHAR(255))
* `status` (VARCHAR(50), Default: `'completed'`)

---

### 2.3 Social Rescue & Logistics (Channel B)

#### `food_listings`
* `id` (INTEGER, Primary Key)
* `donor_id` (INTEGER, Foreign Key &rarr; `users.id`, NOT NULL)
* `food_name` (VARCHAR(255), NOT NULL)
* `food_category` (VARCHAR(100), NOT NULL)
* `is_vegetarian` (BOOLEAN, Default: `TRUE`)
* `quantity_kg` (FLOAT, NOT NULL)
* `estimated_servings` (INTEGER, NOT NULL)
* `preparation_time` (DATETIME, NOT NULL)
* `expiry_time` (DATETIME, NOT NULL)
* `storage_conditions` (VARCHAR(255))
* `current_temperature` (FLOAT)
* `allergen_info` (VARCHAR(500))
* `ingredients` (TEXT)
* `pickup_address` (VARCHAR(500), NOT NULL)
* `pickup_lat` (FLOAT, Default: `26.9124`)
* `pickup_lng` (FLOAT, Default: `75.7873`)
* `pickup_window_start` (DATETIME, NOT NULL)
* `pickup_window_end` (DATETIME, NOT NULL)
* `status` (VARCHAR(50), Default: `'available'`) — `available`, `claimed`, `picked_up`, `delivered`, `rejected`
* `is_flagged` (BOOLEAN, Default: `FALSE`)
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`)

#### `donation_claims`
* `id` (INTEGER, Primary Key)
* `listing_id` (INTEGER, Foreign Key &rarr; `food_listings.id`, NOT NULL)
* `ngo_id` (INTEGER, Foreign Key &rarr; `users.id`, NOT NULL)
* `claimed_servings` (INTEGER, NOT NULL)
* `claim_status` (VARCHAR(50), Default: `'pending'`) — `pending`, `approved`, `scheduled`, `completed`, `cancelled`
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`)
* `claimed_at` (DATETIME, Default: UTC Now)

#### `deliveries`
* `id` (INTEGER, Primary Key)
* `claim_id` (INTEGER, Foreign Key &rarr; `donation_claims.id`, Unique, NOT NULL)
* `volunteer_id` (INTEGER, Foreign Key &rarr; `users.id`, Nullable)
* `status` (VARCHAR(50), Default: `'assigned'`) — `assigned`, `accepted`, `in_progress`, `picked_up`, `delivered`
* `pickup_otp` (VARCHAR(6), NOT NULL)
* `delivery_otp` (VARCHAR(6), NOT NULL)
* `pickup_otp_attempts` (INTEGER, Default: `0`)
* `delivery_otp_attempts` (INTEGER, Default: `0`)
* `otp_expires_at` (DATETIME, Nullable)
* `pickup_time` (DATETIME, Nullable)
* `delivery_time` (DATETIME, Nullable)
* `start_lat` (FLOAT, NOT NULL)
* `start_lng` (FLOAT, NOT NULL)
* `dest_lat` (FLOAT, NOT NULL)
* `dest_lng` (FLOAT, NOT NULL)
* `distance_km` (FLOAT, Default: `0.0`)
* `data_origin` (VARCHAR(20), Indexed, Default: `'REAL'`)

---

### 2.4 Safety, Quality, and Trust

* **`inspection_reports`:** Preliminary visual screening findings (`visual_mould_detected`, `presentation_score`, `packaging_condition`, `disclaimer_text`, `admin_reviewed`).
* **`ocr_results`:** Label text extraction (`extracted_food_name`, `extracted_mfg_date`, `extracted_expiry_date`, `mismatch_detected`).
* **`temperature_logs`:** Food holding temperature checkpoints (`temperature_celsius`, `stage`, `measurement_method`, `is_abnormal`).
* **`fraud_alerts`:** Security anomalies (`alert_type`, `severity`, `status`, `details`, `admin_notes`, `data_origin`).
* **`trust_scores`:** Reliability scoring (`phone_verified`, `fssai_checked`, `successful_donations`, `total_score`).
* **`audit_logs`:** Immutable administrative audit ledger (`user_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `data_origin`).
* **`price_adjustment_logs`:** Monotonic price markdown audit trail (`rescue_listing_id`, `old_price`, `new_price`, `trigger_reason`).
* **`rescue_to_donation_logs`:** Audit trail for unsold commercial food transitioning to social rescue.

---

## 3. POSTGRESQL PRODUCTION MIGRATION

To migrate from local development SQLite to PostgreSQL in production:
1. Set `DATABASE_URL="postgresql://user:password@localhost:5432/anndaan_db"` in `.env`.
2. Install asyncpg or psycopg2: `pip install psycopg2-binary`.
3. SQLAlchemy models automatically generate compliant DDL with standard relational types.

