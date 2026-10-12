# AI Data Generation Prompt & Engineering Evidence
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

In accordance with the project guidelines ("Design the Data Lifecycle of a Real Company"), synthetic dataset schemas and generators were designed and synthesized using Artificial Intelligence. This document provides the **exact prompt delivered to the LLM** alongside architectural validation.

---

## 1. Exact Engineering Prompt Delivered to the LLM

```markdown
You are a data engineer at a retail bank. Design and write a Python 3.11 generator
for synthetic data to build a real-time fraud detection pipeline.

Datasets: transactions, transaction_history, customer_profile, access_logs (JSON Lines),
user_location (JSON), device_data (JSON), previous_fraud_alerts.

Requirements:
- Reproducible with a fixed seed.
- Configurable via a YAML file: number of customers, number of transactions, fraud rate.
- Fraud rate between 0.5% and 2%, with an is_fraud label and a fraud_type column.
- Inject these fraud patterns: impossible_travel, new_device_high_amount,
  velocity_burst, account_takeover, foreign_country.
- Include hard fraud cases that look similar to normal behavior.
- Realistic distributions: log-normal amounts, daily and weekly seasonality.
- Foreign keys must be consistent across datasets.
- previous_fraud_alerts must only reference the historical period.
- All code, variable names and column names in English, no comments.
- Output files: CSV for tabular data, JSON/JSONL for semi-structured data.
```

---

## 2. Engineering Decisions & Anti-Leakage Safeguards

The modular generation engine in `src/fraud_detection/generation/` satisfies strict production criteria:

1. **Strict Temporal Partitioning**:
   - `transaction_history.parquet`: Spans `2026-01-01` through `2026-06-30` (closed batch training set).
   - `transactions.csv`: Spans `2026-07-01` through `2026-07-31` (real-time streaming evaluation set).
   - `previous_fraud_alerts.csv`: **Exclusively** references transactions from the historical batch window. Referencing streaming transactions would introduce catastrophic target leakage.
2. **Referential Integrity**:
   - Every `customer_id` across transactions exists in `customer_profile.csv`.
   - Every `device_id` exists in `device_data.json` or is intentionally new for attack injection.
   - Location records in `user_location.json` and authentication traces in `access_logs.jsonl` align with valid customer IDs.
3. **Statistically Realistic Distributions**:
   - Transaction amounts follow a Log-Normal distribution ($\mu=3.8, \sigma=1.1$), modeling everyday retail purchases with a heavy tail of rare high-value transactions.
   - Diurnal and weekly seasonality patterns reflect consumer rhythms.
4. **Automated Verification**:
   - Automated test cases `test_referential_integrity` and `test_no_data_leakage_in_previous_alerts` in `tests/test_generation.py` enforce these constraints on every commit.
