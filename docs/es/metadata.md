# Estrategia de Metadatos y Gobernanza — Bank Fraud Detection Pipeline
**Datacycle · Unidad 1 · Caso 2: Retail Banking Real-Time Fraud Detection**

Los metadatos proporcionan contexto técnico, procedencia de auditoría y gobernanza de esquemas a lo largo de todo el pipeline de datos, permitiendo trazar con exactitud el ciclo de vida de cada registro bancario.

---

## 1. Los 4 Elementos Fundamentales de Metadatos

En cumplimiento estricto con los requerimientos de la actividad, cada registro procesado en la plataforma bancaria incorpora las siguientes etiquetas de metadatos estandarizadas:

| Elemento de Metadata | Tipo de Dato | Obligatoriedad | Descripción Técnica | Ejemplo Real en Pipeline |
|---|---|---|---|---|
| `source_system` | `string` | **Obligatorio** | Identifica unívocamente el sistema de origen o emisor del dato antes de su captura en el data lake. Permite aislar errores de red y validar la confianza de la fuente. | `core_banking_simulator`, `mobile_app_gateway`, `atm_switch_network` |
| `ingestion_timestamp` | `timestamp` (UTC ISO-8601) | **Obligatorio** | Momento exacto en el que el bus de ingesta (Batch o Streaming) recibió y persistió el registro crudo en la capa Bronze. | `2026-07-03T10:16:11.240Z` |
| `schema_version` | `string` (SemVer) | **Obligatorio** | Versión semántica del contrato de esquema con el que fue emitido el evento. Fundamental para la evolución y compatibilidad de esquemas (*schema evolution*). | `1.0.0` |
| `data_classification` | `string` | **Recomendado** | Etiqueta de clasificación de seguridad y privacidad según la política corporativa de protección de datos personales (PII / RGPD). | `PII_CONFIDENTIAL`, `RESTRICTED_FINANCIAL`, `PUBLIC` |

---

## 2. Inyección Técnica de Metadatos en la Capa Bronze

Durante la fase de ingesta (`batch_ingest.py` y `stream_ingest.py`), el motor de datos añade automáticamente estas columnas a los DataFrames antes de su persistencia en formato Parquet:

```python
from datetime import datetime, timezone
from pyspark.sql.functions import lit

current_utc = datetime.now(timezone.utc).isoformat()

# Enriquecimiento con metadata de gobernanza
df_bronze = (
    df_raw.withColumn("source_system", lit("core_banking_simulator"))
    .withColumn("ingestion_timestamp", lit(current_utc))
    .withColumn("schema_version", lit("1.0.0"))
    .withColumn("data_classification", lit("PII_CONFIDENTIAL"))
)

# Escritura inmutable particionada por fecha
df_bronze.write.mode("overwrite").partitionBy("date").parquet(
    "data/bronze/transactions"
)
```

---

## 3. Catálogo de Esquemas y Gestión de Evolución de Esquema

Para garantizar la estabilidad operativa del pipeline frente a cambios en los sistemas de origen, se aplica una política estricta de versiones semánticas:

### Reglas de Compatibilidad (Schema Evolution Policy):
1. **Versiones Menores (`1.0.0` $\to$ `1.1.0`) — Compatibilidad Hacia Atrás (Backward Compatibility)**:
   - Se permite la adición de campos opcionales o con valores por defecto (ejemplo: incorporar un nuevo parámetro biométrico `device_biometrics_enrolled`).
   - El consumidor de streaming ignora campos desconocidos sin interrumpir el procesamiento en tiempo real.
2. **Versiones Mayores (`1.x.x` $\to$ `2.0.0`) — Cambios Rompedores (Breaking Changes)**:
   - Modificación del tipo de datos de una clave primaria (ejemplo: de `integer` a `UUID` en `transaction_id`) o eliminación de columnas requeridas por el modelo analítico.
   - Requiere despliegue en paralelo de una nueva ruta de almacenamiento Bronze (`data/bronze/v2/`) y reentrenamiento del modelo de Machine Learning.

---

## 4. Auditoría, Linaje y Trazabilidad de Cumplimiento

La inclusión sistemática de estos metadatos permite responder de manera instantánea a requerimientos regulatorios críticos:
- **Trazabilidad de Latencia en la Cadena de Suministro**:
  - Comparando `event_timestamp` con `ingestion_timestamp`, el equipo de ingeniería puede monitorizar retrasos en la red o colas de espera en los sistemas emisores.
- **Auditoría Forense de Modelos**:
  - Ante una reclamación por bloqueo erróneo (*falso positivo*), el banco puede certificar exactamente qué versión del esquema (`schema_version`) y qué sistema emisor (`source_system`) alimentaron la decisión del modelo en ese milisegundo exacto.
