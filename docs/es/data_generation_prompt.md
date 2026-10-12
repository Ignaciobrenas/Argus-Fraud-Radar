# Evidencia y Documentación del Prompt de Generación de Datos con IA
**Datacycle · Unidad 1 · Caso 2: Retail Banking Real-Time Fraud Detection**

Tal como establece la actividad formativa ("Design the Data Lifecycle of a Real Company"), el diseño y síntesis de los datos sintéticos debe generarse utilizando Inteligencia Artificial, debiendo adjuntarse la **evidencia exacta del prompt utilizado** y los principios de ingeniería aplicados.

---

## 1. Prompt Exacto Utilizado con el LLM

El siguiente prompt fue diseñado y suministrado al modelo de lenguaje para obtener la arquitectura, esquemas de base de datos y scripts modulares de generación en Python:

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

## 2. Decisiones de Ingeniería y Garantías Anti-Leakage

La implementación del generador modular en `src/fraud_detection/generation/` sigue rigurosos principios técnicos:

1. **Partición Temporal Estricta**:
   - `transaction_history.parquet`: Cubre del `2026-01-01` al `2026-06-30` (periodo batch cerrado).
   - `transactions.csv`: Cubre del `2026-07-01` al `2026-07-31` (periodo streaming de evaluación).
   - `previous_fraud_alerts.csv`: **Solo** referencia transacciones del periodo histórico (`2026-01-01` a `2026-06-30`). Si contuviera transacciones del periodo de streaming, se provocaría una fuga de información (*target leakage*) que falsearía la evaluación del modelo.
2. **Integridad Referencial Completa**:
   - Cada `customer_id` en `transactions` existe en `customer_profile.csv`.
   - Cada `device_id` en `transactions` existe en `device_data.json` o está deliberadamente marcado como nuevo para inyectar vectores de ataque.
   - Las ubicaciones en `user_location.json` y las trazas en `access_logs.jsonl` correlacionan exactamente con los identificadores de cliente y transacción.
3. **Distribuciones Estadísticamente Verosímiles**:
   - Importes modelados mediante distribución Log-Normal ($\mu=3.8, \sigma=1.1$), reproduciendo la concentración típica de compras cotidianas pequeñas (10 € - 50 €) con cola pesada hacia importes excepcionales.
   - Variación estacional diurna/nocturna y semanal (sábados y domingos).
4. **Verificación Automatizada**:
   - El test unitario `test_referential_integrity` y `test_no_data_leakage_in_previous_alerts` en `tests/test_generation.py` validan de forma automática la consistencia en cada ejecución del pipeline de CI/CD.
