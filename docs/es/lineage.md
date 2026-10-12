# Linaje del Dato (Data Lineage) — Bank Fraud Detection Pipeline
**Datacycle · Unidad 1 · Caso 2: Retail Banking Real-Time Fraud Detection**

El **linaje del dato** describe la trazabilidad completa, el ciclo de vida de transformaciones y el flujo de dependencias desde las fuentes transaccionales originales hasta los paneles analíticos de control en tiempo real.

---

## 1. Flujo Simplificado de Linaje (Requisito de la Actividad)

Tal como solicita el enunciado de la actividad formativa, el flujo fundamental se define en cuatro fases continuas:

```mermaid
flowchart LR
    S["Source\n(Sistemas de Origen:\nCore, Terminales, Apps)"] --> C["Cleaning\n(Bronze a Silver:\nDeduplicación, Tipado, Quality)"]
    C --> T["Target Table\n(Gold Features &\nAlerts Scoring)"]
    T --> D["Dashboard\n(Streamlit Control Center &\nKPI de Tiempo Real)"]
```

---

## 2. Linaje Detallado Multi-Capa (Arquitectura Medallion)

El pipeline integra los 7 datasets a través de las capas de refinamiento progresivo:

```mermaid
flowchart TD
    subgraph RAW ["1. Capa Raw (Fuentes Crudas)"]
        R1["raw/customer_profile.csv"]
        R2["raw/device_data.json"]
        R3["raw/transaction_history.parquet"]
        R4["raw/transactions.csv"]
        R5["raw/user_location.json"]
        R6["raw/access_logs.jsonl"]
        R7["raw/previous_fraud_alerts.csv"]
    end

    subgraph BRONZE ["2. Capa Bronze (Raw Ingestion + Metadata)"]
        B1["bronze/customer_profile"]
        B2["bronze/device_data"]
        B3["bronze/transaction_history (particionado)"]
        B4["bronze/transactions (particionado)"]
        B5["bronze/user_location"]
        B6["bronze/access_logs"]
        B7["bronze/previous_fraud_alerts"]
    end

    subgraph SILVER ["3. Capa Silver (Limpio, Deduplicado, Validado)"]
        S1["silver/customer_profile"]
        S2["silver/device_data"]
        S3["silver/transactions (unión history + stream)"]
        S4["silver/user_location"]
        S5["silver/access_logs"]
        S6["silver/previous_fraud_alerts"]
    end

    subgraph GOLD ["4. Capa Gold (Features Multidimensionales)"]
        G1["gold/features.parquet\n(19 features: geo, velocity, behavior, profile)"]
    end

    subgraph SERVING ["5. Capa de Decisión y Consumo"]
        M1["LightGBM Model (Scoring) &\nBaseline Rules Engine"]
        A1["data/alerts.parquet\n(alert_timestamp, fraud_score, latency, is_alert)"]
        D1["Dashboard Streamlit (KPI % Tiempo Real,\nBreakdown de Fraudes, Impacto Financiero)"]
    end

    R1 --> B1
    R2 --> B2
    R3 --> B3
    R4 --> B4
    R5 --> B5
    R6 --> B6
    R7 --> B7

    B1 --> S1
    B2 --> S2
    B3 --> S3
    B4 --> S3
    B5 --> S4
    B6 --> S5
    B7 --> S6

    S1 --> G1
    S2 --> G1
    S3 --> G1
    S4 --> G1
    S5 --> G1
    S6 --> G1

    G1 --> M1
    M1 --> A1
    A1 --> D1
```

---

## 3. Matriz de Linaje a Nivel de Columna (Column-Level Lineage)

La siguiente tabla traza la procedencia y transformación de las variables críticas:

| Variable Destino (Gold / Alerts) | Tabla Origen (Raw / Bronze) | Columnas de Origen | Lógica de Transformación / Algoritmo |
|---|---|---|---|
| `geo_distance_ip_gps_km` | `user_location.json` | `ip_country`, `gps.lat`, `gps.lon` | Fórmula de Haversine calculando la discrepancia geográfica entre la coordenada GPS y la geolocalización IP. |
| `distance_from_home_km` | `transactions`, `customer_profile` | `gps.lat`, `gps.lon`, `home_lat`, `home_lon` | Distancia ortodrómica en km entre el punto de venta/dispositivo y el domicilio oficial registrado del cliente. |
| `travel_speed_kmh` | `transactions`, `user_location` | `gps.lat`, `gps.lon`, `event_timestamp` | $\Delta \text{distancia} / \Delta \text{tiempo}$ entre transacciones consecutivas del mismo cliente. Detecta teleportación o viaje imposible. |
| `amount_zscore_customer` | `transactions`, `transaction_history` | `customer_id`, `amount` | $( \text{amount} - \mu_{\text{customer}} ) / \sigma_{\text{customer}}$. Normalización estadística del desvío de consumo individual. |
| `txn_count_10min` | `transactions` | `customer_id`, `event_timestamp` | Conteo en ventana temporal deslizante de 10 minutos (cerrada a la izquierda) para detectar ráfagas de prueba de tarjetas. |
| `is_new_device` | `transactions`, `device_data` | `customer_id`, `device_id` | Cruce con el catálogo histórico de dispositivos del cliente. Asigna `1` si el dispositivo no estaba previamente registrado. |
| `has_failed_login_history` | `access_logs.jsonl` | `customer_id`, `event_type`, `event_timestamp` | Presencia de eventos `login_failed` en el historial de sesión previo a la transacción. |
| `detection_latency_seconds` | `transactions`, `consumer.py` | `event_timestamp`, `alert_timestamp` | $\text{alert\_timestamp} - \text{event\_timestamp}$. Tiempo total transcurrido desde la emisión del pago hasta la decisión del modelo. |
| `real_time_fraud_pct` | `alerts.parquet` | `is_fraud`, `is_alert`, `detection_latency_seconds` | Métrica agregada de negocio: porcentaje de fraudes confirmados alertados con latencia $\le 2.0$ segundos. |

---

## 4. Garantías de Trazabilidad y Prevención de Data Leakage

1. **Partición Temporal Estricta**:
   - Las alertas previas (`previous_fraud_alerts.csv`) solo referencian transacciones del periodo histórico (`2026-01-01` a `2026-06-30`). El test automatizado `test_no_data_leakage_in_previous_alerts` garantiza que la intersección de identificadores de transacción con el periodo de streaming es nula (`len == 0`).
2. **Ventanas Deslizantes sin Mirada al Futuro**:
   - Todas las funciones de ventana en `velocity.py` y `behavior.py` ordenan estrictamente por `event_timestamp` ascendente y solo acumulan información pasada, garantizando que el modelo sea fiel al entorno de producción en tiempo real.
3. **Auditoría Regulatoria**:
   - Cada registro en la capa final `alerts.parquet` retiene el `transaction_id`, el timestamp de evento, el timestamp de decisión y el `fraud_score`, permitiendo reproducir y justificar cualquier bloqueo transaccional ante auditorías del Banco de España o el BCE.
