# Metadata & Governance Strategy — Bank Fraud Detection Pipeline
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

Metadata provides audit provenance, technical context, and schema governance across the entire data lifecycle, ensuring compliance with strict retail banking regulations.

---

## 1. The 4 Mandatory Metadata Governance Elements

In accordance with enterprise data engineering standards, every record processed into the medallion lake is enriched with these standard metadata tags:

| Metadata Tag | Data Type | Requirement | Technical Description | Real-World Pipeline Value |
|---|---|---|---|---|
| `source_system` | `string` | **Mandatory** | Uniquely identifies the originating system/gateway prior to data lake arrival. Isolates upstream faults. | `core_banking_simulator`, `mobile_app_gateway`, `atm_switch_network` |
| `ingestion_timestamp` | `timestamp` (UTC ISO-8601) | **Mandatory** | The exact millisecond timestamp when the ingestion runner persisted the record into the Bronze layer. | `2026-07-03T10:16:11.240Z` |
| `schema_version` | `string` (SemVer) | **Mandatory** | Semantic version of the schema contract under which the record was generated. Enables backward compatibility. | `1.0.0` |
| `data_classification` | `string` | **Recommended** | Data security and confidentiality classification under corporate GDPR policy. | `PII_CONFIDENTIAL`, `RESTRICTED_FINANCIAL`, `PUBLIC` |

---

## 2. Technical Metadata Injection in the Bronze Layer

During ingestion (`batch_ingest.py` and `stream_ingest.py`), the PySpark engine injects these tags prior to Parquet serialization:

```python
from datetime import datetime, timezone
from pyspark.sql.functions import lit

current_utc = datetime.now(timezone.utc).isoformat()

# Append enterprise governance metadata
df_bronze = (
    df_raw.withColumn("source_system", lit("core_banking_simulator"))
    .withColumn("ingestion_timestamp", lit(current_utc))
    .withColumn("schema_version", lit("1.0.0"))
    .withColumn("data_classification", lit("PII_CONFIDENTIAL"))
)

# Immutable partitioned write
df_bronze.write.mode("overwrite").partitionBy("date").parquet(
    "data/bronze/transactions"
)
```

---

## 3. Schema Catalog & Evolution Management

To ensure pipeline stability against schema drifts, a strict SemVer contract is enforced:

### Schema Evolution Rules:
1. **Minor Versions (`1.0.0` $\to$ `1.1.0`) — Backward Compatibility**:
   - Optional fields or defaults can be introduced (e.g., adding `biometric_enrolled_flag`).
   - The streaming consumer ignores unexpected keys without halting real-time execution.
2. **Major Versions (`1.x.x` $\to$ `2.0.0`) — Breaking Changes**:
   - Changing primary key data types (e.g., from `integer` to `UUID`) or dropping features consumed by the ML model.
   - Requires side-by-side deployment of a new Bronze storage path (`data/bronze/v2/`) and model retraining.

---

## 4. Compliance Auditing & Forensic Traceability

Systematic metadata tracking enables automated audit verification:
- **Pipeline Latency Auditing**:
  - Comparing `event_timestamp` with `ingestion_timestamp` allows real-time telemetry on broker queue delays.
- **Forensic Dispute Defense**:
  - In disputed transaction declinations (*false positive claims*), the bank can prove exactly which schema contract (`schema_version`) and source feed (`source_system`) informed the decision at that millisecond.
