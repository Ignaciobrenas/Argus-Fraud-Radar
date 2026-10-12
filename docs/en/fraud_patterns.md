# Injected Fraud Patterns — Attack Vectors & Technical Specifications
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

To rigorously evaluate the bank's fraud detection capabilities, the synthetic generator injects a realistic blend of **blatant, easy-to-catch frauds** (which simple rules can intercept) and **subtle, sophisticated frauds** (which require multivariate machine learning to separate from normal consumer behavior).

---

## 1. Summary of the 8 Injected Attack Vectors

| `fraud_type` | Attack Vector | Detection Criteria | Captured by Rules | Captured by ML |
|---|---|---|---|---|
| `impossible_travel` | Session Hijacking / Teleportation | $\Delta \text{distance} > 800\text{ km}$ or speed $> 800\text{ km/h}$ between consecutive events | ✅ Yes (if rule exists) | ✅ Yes (100% recall) |
| `new_device_high_amount` | Cloned Card High-Value Spend | Unrecognized device fingerprint + amount $> 3\times$ customer daily spend | ✅ Yes | ✅ Yes (100% recall) |
| `velocity_burst` | Automated Card Testing (*Botnet*) | $\ge 3$ transactions in $< 10$ minutes by the same cardholder | ✅ Yes (window rule) | ⚠️ Threshold dependent |
| `account_takeover` (ATO) | Credential Stuffing / Phishing | Preceding failed logins in `access_logs`, login success, new device, high transfer | ⚠️ Partial | ✅ Yes (high precision) |
| `foreign_country` | Cross-Border Fraudulent Spend | Transaction IP/terminal in a different country than customer residence | ⚠️ High false positives | ✅ Yes (100% recall) |
| `atm_nocturnal_drain` | Nocturnal ATM Cash Drain | Physical ATM withdrawal between 02:00 and 04:30 at max limit | ❌ No | ✅ Yes (seasonality features) |
| `phishing_mule_transfer` | Rapid Transfer to Money Mule | Web channel, unusual beneficiary, rapid drain post-login | ❌ No | ✅ Yes (risk score) |
| `hard_subtle_fraud` | Low-and-Slow Sophisticated Fraud | Moderate amounts without violating fixed hard thresholds | ❌ No (invisible to rules) | ✅ Yes |

---

## 2. Technical Specifications of Attack Vectors

### 1. `impossible_travel` (Impossible Travel)
- **Mechanism**: The user authorizes a card purchase in Madrid at 10:00, and 15 minutes later, an e-commerce payment or ATM withdrawal occurs in Moscow. The physical speed required exceeds $1,000\text{ km/h}$, an impossible velocity for commercial aviation.
- **Key Features**:
  - `distance_from_home_km`
  - `travel_speed_kmh`
  - `geo_distance_ip_gps_km`

### 2. `new_device_high_amount` (New Device + High Amount)
- **Mechanism**: A malicious actor authenticates using hardware or browser fingerprints never before registered on the customer profile and executes a payment substantially above the customer's historical average.
- **Key Features**:
  - `is_new_device`
  - `amount_zscore_customer`
  - `amount_to_spend_ratio`

### 3. `velocity_burst` (Rapid Card Testing Burst)
- **Mechanism**: An automated script rapidly fires multiple transactions in seconds or minutes to verify stolen card numbers before the victim notices and freezes the card.
- **Key Features**:
  - `txn_count_10min`
  - `txn_count_1h`
  - `amount_sum_1h`

### 4. `account_takeover` (Account Takeover)
- **Mechanism**: An attacker carries out multiple failed login attempts (`access_logs`), finally breaches the credentials, and transfers money from an unrecognized device.
- **Key Features**:
  - `has_failed_login_history`
  - `is_new_device`
  - `amount_zscore_customer`

### 5. `foreign_country` (Foreign Country Transaction)
- **Mechanism**: Payment executed from an IP or terminal geolocated outside the customer's resident country.
- **Heuristic Rule Flaw**: Static rules blocking all foreign transactions cause severe **false positives** whenever genuine customers travel for tourism or business.
- **ML Advantage**: LightGBM balances foreign location against merchant category, channel, spend ratio, and hour to differentiate legitimate travelers from fraud rings.

### 6. `atm_nocturnal_drain` (Late-Night ATM Drain)
- **Mechanism**: Cash withdrawal at an ATM between 02:00 and 05:00 while the victim sleeps.
- **Key Features**:
  - `channel == "atm"`
  - `is_night == 1`
  - `hour_of_day`

### 7. `phishing_mule_transfer` (Phishing Transfer to Mule)
- **Mechanism**: Attacker uses phished credentials to transfer funds to a domestic money mule.
- **Key Features**:
  - `channel == "web"`
  - `amount_to_spend_ratio`
  - `risk_level_code`

### 8. `hard_subtle_fraud` (Subtle Camouflaged Fraud)
- **Mechanism**: Frauds intentionally tuned to look like normal retail purchases (e.g., 80 € to 120 €) avoiding static rule thresholds.
- **ML Advantage**: The non-linear gradient boosted tree combines subtle interactions across all 19 dimensions to isolate the fraud signature.
