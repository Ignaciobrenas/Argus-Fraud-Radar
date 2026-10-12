# Data Classification — Bank Fraud Detection Pipeline
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

This document details the taxonomy, structural classification, ingestion mode, and privacy/governance treatment (PII / GDPR / PSD2) for all 7 datasets in the real-time fraud detection pipeline.

---

## 1. Dataset Classification Matrix

| Dataset | Raw Format | Structural Classification | Ingestion Mode | Technical Rationale |
|---|---|---|---|---|
| `transactions` | CSV / Parquet | **Structured** | Streaming | Rigid tabular schema with typed columns (`transaction_id`, `amount`, `channel`, etc.). Represents real-time transaction events during the evaluation window. |
| `transaction_history` | Parquet | **Structured** | Batch | Identical columnar schema as live transactions, partitioned and stored historically for model training. |
| `customer_profile` | CSV | **Structured** | Batch | Master customer profile table with static or low-volatility financial and demographic attributes (`risk_level`, `avg_monthly_spend`, home GPS coordinates). |
| `previous_fraud_alerts` | CSV | **Structured** | Batch | Historical record of generated fraud alerts. Strictly limited to the historical batch window to eliminate *data leakage*. |
| `user_location` | JSON | **Semi-Structured** | Streaming | Contains nested attributes (nested `gps` object with latitude and longitude) and optional fields based on mobile client telemetry. |
| `access_logs` | JSON Lines (`.jsonl`) | **Semi-Structured** | Streaming | High-throughput authentication event stream with polymorphic payloads depending on event type (`login_failed`, `login_success`, dynamic user agents). |
| `device_data` | JSON | **Semi-Structured** | Batch / Micro-batch | Inventory of recognized hardware devices and web browsers with schemas varying by operating system (iOS, Android, Windows) and security flags (`is_rooted`). |

---

## 2. Ingestion Modes: Streaming vs. Batch

### A. Real-Time Streaming Streams
- **`transactions`**: Dispatched as discrete financial payment/transfer attempts with an authorization SLA under 2 seconds ($N=2s$).
- **`user_location`**: Telemetry emitted alongside the payment from the mobile app or browser for instant geolocation verification.
- **`access_logs`**: Continuous authentication telemetry fed into the stream processor to identify brute-force attacks and account takeover attempts.

### B. Batch Datasets
- **`customer_profile`**: Nightly batch extraction from core banking systems (daily ETL).
- **`transaction_history`**: Massive cold partitions in the data lake for periodic offline ML retraining.
- **`previous_fraud_alerts`**: Periodic exports from the bank's fraud case management CRM.
- **`device_data`**: Recognized hardware registry updated periodically.

---

## 3. Privacy, PII Protection, and Regulatory Compliance (GDPR)

In a commercial banking institution governed by the **General Data Protection Regulation (GDPR)** and the **Payment Services Directive (PSD2/PSD3)**, personal data protection requires strict technical controls:

### 1. Identified Direct and Indirect PII
- **`customer_id` and Account Numbers (`source_account`, `destination_account`)**: Critical banking identifiers that link directly to an individual.
- **IP Addresses (`ip_address`)**: Considered personal data under European jurisprudence due to subscriber linkage through ISPs.
- **GPS Coordinates (`home_lat`, `home_lon`, `gps.lat`, `gps.lon`)**: Allow precise tracking of user physical residence and real-time movement.
- **Device Fingerprints (`device_id`, User Agents)**: Facilitate cross-session device identification.

### 2. Security & Privacy Safeguards Applied in Pipeline
- **Pseudonymization and Salted Hashing**:
  - Customer and account identifiers are cryptographically hashed using *HMAC-SHA-256* before entering analytical and ML layers.
  - The secret key lookup table is restricted to an isolated hardware security module (*HSM*).
- **Spatial Aggregation (Coarse-Graining)**:
  - Raw high-precision GPS coordinates are aggregated into distance metrics (`distance_from_home_km`, `travel_speed_kmh`) rather than keeping raw coordinates in the feature store.
- **IP Masking**:
  - IPv4 addresses have the last octet truncated (e.g., `192.168.1.xxx`) to retain country/city geolocation without tracking the exact subscriber terminal.
- **End-to-End Encryption**:
  - **AES-256-GCM** encryption at rest on all Parquet lake partitions.
  - **TLS 1.3 / mTLS** encryption in transit between streaming producers, brokers, and scoring consumers.
- **Right to be Forgotten & Retention**:
  - Bronze raw data is retained for 30 days before migration to cold storage or purge.
  - The decoupled medallion lake supports customer record deletion requests (*Right to Erasure*) across all layers.
