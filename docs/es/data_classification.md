# Clasificación de Datos — Bank Fraud Detection Pipeline
**Datacycle · Unidad 1 · Caso 2: Retail Banking Fraud Detection**

Este documento detalla la taxonomía, clasificación estructural, modo de ingesta y tratamiento de privacidad (PII/RGPD) para los 7 datasets utilizados en la plataforma de detección de fraude en tiempo real.

---

## 1. Matriz de Clasificación de Datasets

| Dataset | Formato Raw | Clasificación Estructural | Modo de Ingesta | Justificación Técnica |
|---|---|---|---|---|
| `transactions` | CSV / Parquet | **Estructurado** | Streaming | Esquema tabular rígido con columnas tipadas fijas (`transaction_id`, `amount`, `channel`, etc.). Representa el flujo transaccional en tiempo real del periodo de evaluación. |
| `transaction_history` | Parquet | **Estructurado** | Batch | Mismo esquema columnar rígido que las transacciones en vivo, pero almacenado históricamente y comprimido en formato columnar Parquet para entrenamiento batch offline. |
| `customer_profile` | CSV | **Estructurado** | Batch | Tabla maestra de clientes con atributos demográficos y financieros estáticos o de baja volatilidad (`risk_level`, `avg_monthly_spend`, coordenadas de domicilio). |
| `previous_fraud_alerts` | CSV | **Estructurado** | Batch | Registro histórico de alertas emitidas y confirmadas. Solo cubre el periodo histórico para prevenir *data leakage* en el modelo supervisado. |
| `user_location` | JSON | **Semi-estructurado** | Streaming | Contiene estructuras anidadas (objeto anidado `gps` con latitud y longitud) y campos opcionales según la disponibilidad del proveedor de red o sensor móvil. |
| `access_logs` | JSON Lines (`.jsonl`) | **Semi-estructurado** | Streaming | Eventos de autenticación de alta frecuencia con atributos variables según el tipo de evento (`login_failed`, `login_success`, user agents dinámicos y geolocalización IP). |
| `device_data` | JSON | **Semi-estructurado** | Batch / Micro-batch | Inventario de terminales móviles y navegadores web con esquemas que varían según el sistema operativo (iOS, Android, Windows) y flags de seguridad (`is_rooted`). |

---

## 2. Clasificación por Modo de Flujo: Streaming vs Batch

### A. Flujos en Tiempo Real (Streaming)
- **`transactions`**: Llegan como eventos transaccionales discretos por cada intento de pago o transferencia con una SLA de decisión inferior a 2 segundos ($N=2s$).
- **`user_location`**: Telemetría emitida simultáneamente con el pago desde la aplicación móvil o pasarela web para correlación inmediata de geolocalización.
- **`access_logs`**: Trazas de autenticación transmitidas continuamente hacia el bus de streaming para correlacionar ataques de fuerza bruta y *account takeover*.

### B. Flujos en Lote (Batch)
- **`customer_profile`**: Extraído de los sistemas centrales (*core banking*) mediante procesos de extracción nocturnos (ETL diario).
- **`transaction_history`**: Cargas masivas de históricos almacenadas en el data lake para reentrenamiento periódico de modelos de Machine Learning.
- **`previous_fraud_alerts`**: Volcados periódicos del sistema de gestión de casos de fraude (*fraud case management*).
- **`device_data`**: Catálogo de dispositivos reconocidos y huellas digitales de hardware actualizadas periódicamente.

---

## 3. Tratamiento de Datos Personales (PII) y Cumplimiento Normativo (RGPD)

En una entidad bancaria real regulada por normativas como el **RGPD (Reglamento General de Protección de Datos)** y las directivas de pagos **PSD2 / PSD3**, el tratamiento de datos sensibles requiere medidas técnicas y organizativas rigurosas:

### 1. Identificadores Directos e Indirectos (PII Identificados)
- **`customer_id` y Cuentas (`source_account`, `destination_account`)**: Identificadores bancarios críticos que vinculan el registro con una persona física.
- **Direcciones IP (`ip_address`)**: Consideradas dato de carácter personal según la jurisprudencia europea, ya que pueden vincularse a un abonado a través de su ISP.
- **Coordenadas GPS (`home_lat`, `home_lon`, `gps.lat`, `gps.lon`)**: Permiten ubicar con precisión el domicilio o la ubicación física en tiempo real de los usuarios.
- **Huellas de Dispositivo (`device_id`, User Agents)**: Permiten la reidentificación de usuarios (*fingerprinting*).

### 2. Políticas de Seguridad y Mitigación Aplicadas en Producción
- **Seudonimización y Hash Criptográfico**:
  - Los identificadores de cuenta y cliente se transforman mediante funciones hash unidireccionales con clave salada (*HMAC-SHA-256*) antes de entrar en las capas analíticas y modelos de Machine Learning.
  - La tabla de correspondencia (*lookup table*) reside en una zona aislada (*Vault*) protegida por HSM (*Hardware Security Module*).
- **Ofuscación y Agregación Espacial (Coarse-Graining de GPS)**:
  - En lugar de almacenar coordenadas GPS con precisión métrica (5 decimales), en capas Gold se trunca la precisión a nivel de radio de 1 a 2 kilómetros o se calcula directamente la métrica derivada (`distance_from_home_km`, `travel_speed_kmh`) sin retener la coordenada original cruda en el dataset de modelado.
- **Enmascaramiento de IPs**:
  - Las direcciones IPv4 e IPv6 se anonimizan truncando el último octeto (ejemplo: `192.168.1.xxx`) para retener únicamente la geolocalización a nivel de país o ciudad para detección de anomalías.
- **Cifrado de Extremo a Extremo**:
  - Cifrado en reposo (*Encryption at Rest*) mediante **AES-256-GCM** en las particiones de Parquet.
  - Cifrado en tránsito (*Encryption in Transit*) mediante **mTLS / TLS 1.3** entre productores y consumidores de streaming.
- **Políticas de Retención y Derecho al Olvido**:
  - Los datos crudos en la capa Bronze tienen un periodo de retención máximo de 30 días antes de su purga o migración a almacenamiento frío comprimido (`data/archive/`).
  - La arquitectura desacoplada permite eliminar o anonimizar los registros de un cliente específico ante una solicitud formal de baja o ejercicio del derecho de supresión.
