# 🛡️ Bank Fraud Detection Pipeline (End-to-End)
**Datacycle · Unidad 1 · Grupo 4 · Caso 2: Retail Banking Real-Time Fraud Detection**

This repository implements a production-grade, end-to-end data pipeline and machine learning scoring engine to detect fraudulent banking transactions in real time ($N \le 2.0$ seconds).

---

## 🎯 Objective & Key Performance Indicator (KPI)

A retail bank requires sub-second fraud detection on high-velocity transactional payment streams before funds leave the institution.

**Regulatory Lineage KPI:** `Percentage of Fraud Detected in Real Time`

$$\text{Real-Time Fraud \%} = \frac{\text{Frauds Alerted within } N \text{ seconds}}{\text{Total Frauds}} \times 100$$

- **$N$ (Real-time latency SLA threshold):** $2.0\text{ seconds}$
- **Target Fraud Rate:** $0.5\% - 2.0\%$ (empirical: $1.52\% - 1.55\%$)
- **Temporal Partitioning:** Batch historical period (`2026-01-01` to `2026-06-30`) strictly separated from streaming evaluation period (`2026-07-01` to `2026-07-31`).

---

## 🕵️‍♂️ Multi-Pattern Fraud Detection (Covered Use Cases)

The pipeline explicitly models and detects **8 distinct banking fraud patterns / use cases**:

1. **`impossible_travel`**: Physical teleportation anomaly where consecutive transactions or IP and GPS locations diverge at speeds $> 800\text{ km/h}$ or distances $> 1,000\text{ km}$.
2. **`new_device_high_amount`**: Rogue/unregistered device executing a transaction with an amount $> 5\times$ the customer's average monthly spending.
3. **`velocity_burst`**: High-frequency card testing burst ($4 - 7$ transactions within $3 - 10$ minutes) from the same source account.
4. **`account_takeover` (ATO)**: Brute-force credential stuffing ($3 - 6$ consecutive `login_failed` events in access logs), followed by a successful login from a new device/IP and an immediate high-value transfer.
5. **`foreign_country`**: Cross-border transaction executed in an uncharacteristic foreign jurisdiction without travel notice.
6. **`atm_nocturnal_drain`**: Nocturnal ATM cash withdrawal ($02:00\text{ AM} - 04:30\text{ AM}$) near daily limits.
7. **`phishing_mule_transfer`**: Rapid online transfer towards an unverified mule account.
8. **`hard_subtle_fraud`**: Subtle fraud cases with moderate amounts and standard mobile channel that evade simple threshold rules, but are captured by multi-dimensional ML inference.

---

## 🏗️ Architecture & Medallion Pipeline

```
Raw Sources ➔ Bronze (Raw + Metadata) ➔ Silver (Clean & Validated) ➔ Gold (19 Features) ➔ Streaming Scoring ➔ Alerts Parquet ➔ KPI Dashboard
```

| Layer | Path | Format | Description |
|---|---|---|---|
| **Raw** | `data/raw/` | CSV, JSON, JSONL | 7 synthetic datasets generated with seed `42`. |
| **Bronze** | `data/bronze/` | Parquet (partitioned by date) | Ingested data with lineage metadata (`source_system`, `ingestion_timestamp`, `schema_version`). |
| **Silver** | `data/silver/` | Parquet | Cleaned, typed, deduplicated, and validated through data quality assertions. |
| **Gold** | `data/gold/features.parquet` | Parquet | 19 multidimensional features (geo, velocity, behavior, profile risk). |
| **Alerts** | `data/alerts.parquet` | Parquet | Scored transactions with ML probability, rule flags, and measured latency. |

---

## 📊 Experimental Results (Scenarios A, B & C)

Evaluated across the 5,000 streaming transactions ($N = 2.0\text{s}$):

| Scenario | Architecture | Real-Time KPI (%) | Recall (%) | Precision (%) | False Positives | Mean Latency |
|---|---|---|---|---|---|---|
| **A** | **Nightly Batch Rules** | **0.00%** | 65.79% | 52.63% | 45 | ~4.0 hours |
| **B** | **Streaming Rules** | **60.53%** | 65.79% | 52.63% | 45 | 1.039 s |
| **C** | **Streaming LightGBM** | **92.11%** | **100.00%** | **100.00%** | **0** | **1.039 s** |

### Per-Pattern Recall Comparison:
- **Baseline Rules**: Missed $60.6\%$ of `velocity_burst` events and $50.0\%$ of `hard_subtle_fraud` cases, while triggering 45 false positives.
- **Machine Learning (LightGBM)**: Reached $100\%$ recall across all 8 fraud types with $0$ false positives at the calibrated optimal decision threshold ($\theta = 0.654$).

---

## 📁 Comprehensive Documentation (Bilingual: ES & EN)

The project includes an exhaustive, professional documentation suite organized into both Spanish and English:

- 🇪🇸 **[Documentación en Español (`docs/es/`)](docs/es/index.md)**:
  - [Arquitectura del Sistema](docs/es/architecture.md)
  - [Clasificación de Datos y RGPD](docs/es/data_classification.md)
  - [Modelo Pirámide DIKW](docs/es/dikw.md)
  - [Ciclo de Vida del Dato](docs/es/lifecycle.md)
  - [Linaje y Trazabilidad del Dato](docs/es/lineage.md)
  - [Estrategia de Metadatos y Gobernanza](docs/es/metadata.md)
  - [Patrones de Fraude y Vectores de Ataque](docs/es/fraud_patterns.md)
  - [Comparativa de Escenarios y KPI](docs/es/scenarios_and_kpi.md)
  - [Prompt de Generación con IA](docs/es/data_generation_prompt.md)

- 🇬🇧 **[English Documentation (`docs/en/`)](docs/en/index.md)**:
  - [System Architecture](docs/en/architecture.md)
  - [Data Classification & GDPR](docs/en/data_classification.md)
  - [DIKW Pyramid Model](docs/en/dikw.md)
  - [Data Lifecycle](docs/en/lifecycle.md)
  - [Data Lineage & Traceability](docs/en/lineage.md)
  - [Metadata Strategy & Governance](docs/en/metadata.md)
  - [Fraud Patterns & Attack Vectors](docs/en/fraud_patterns.md)
  - [Scenario Benchmarks & Real-Time KPI](docs/en/scenarios_and_kpi.md)
  - [AI Data Generation Prompt](docs/en/data_generation_prompt.md)

- 📊 **[Informe Ejecutivo de Conclusiones Finales](reports/final_conclusions.md)**: ROI financiero, matrices de confusión y propuesta arquitectónica de producción.

---

## 🚀 How to Run the Project

### 1. Execute Entire Pipeline End-to-End
Run the unified pipeline runner:
```powershell
python main.py
```
Or execute each stage individually:
```powershell
make generate   # Step 1: Generate 7 synthetic datasets
make bronze     # Step 2: Batch ingestion with metadata (PySpark)
make silver     # Step 3: Cleaning, quality assertions & joins
make gold       # Step 4: Multi-dimensional feature engineering
make train      # Step 5: Temporal split ML model training (LightGBM)
make stream     # Step 6: Streaming consumer & real-time latency scoring
make kpi        # Step 7: Scenario evaluation & KPI report
```

### 2. Launch Interactive Dashboard (Streamlit)
```powershell
streamlit run src/fraud_detection/dashboard/app.py
```
The dashboard provides interactive sliders for latency threshold $N$ and decision threshold, financial impact cards, per-pattern detection bars, latency histograms, and alert drill-down.

### 3. Run Automated Unit Tests
```powershell
pytest -v
```
All 17 tests validate data generation, referential integrity, data leakage prevention, Haversine geo calculations, rolling velocity, behavior features, baseline rules, and financial KPIs.
