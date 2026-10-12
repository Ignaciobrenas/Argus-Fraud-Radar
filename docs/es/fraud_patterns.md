# Patrones de Fraude Inyectados — Especificación Técnica y Vectores de Ataque
**Datacycle · Unidad 1 · Caso 2: Retail Banking Real-Time Fraud Detection**

Para evaluar con rigor un sistema antifraude bancario, la entidad inyecta una mezcla realista de fraudes: algunos **fáciles y evidentes** (que pueden capturarse con reglas fijas) y otros **sutiles y complejos** (que requieren modelos de Machine Learning multivariante para ser discriminados del comportamiento legítimo).

---

## 1. Resumen de los 8 Vectores de Ataque Inyectados

| `fraud_type` | Vector de Ataque | Criterio de Detección | Capturado por Reglas | Capturado por ML |
|---|---|---|---|---|
| `impossible_travel` | Suplantación de sesión / Teleportación | $\Delta \text{distancia} > 800\text{ km}$ o velocidad $> 800\text{ km/h}$ entre eventos consecutivos | ✅ Sí (si hay regla fija) | ✅ Sí (100% recall) |
| `new_device_high_amount` | Compra fraudulenta con tarjeta clonada | Nuevo terminal no reconocido + importe $> 3\times$ media habitual del cliente | ✅ Sí | ✅ Sí (100% recall) |
| `velocity_burst` | Prueba automatizada de tarjetas (*card testing*) | $\ge 3$ transacciones en ventana $< 10$ minutos por un mismo cliente | ✅ Sí (regla de ventana) | ⚠️ Requiere threshold ajustado |
| `account_takeover` (ATO) | Robo de credenciales (*credential stuffing*) | Intentos fallidos previos en `access_logs`, éxito en nuevo dispositivo e importe alto | ⚠️ Parcial | ✅ Sí (alta precisión) |
| `foreign_country` | Operaciones transfronterizas no autorizadas | País de origen de la IP o terminal distinto al país de residencia habitual | ⚠️ Genera falsos positivos | ✅ Sí (100% recall) |
| `atm_nocturnal_drain` | Vaciado en cajero con tarjeta duplicada | Retirada en canal ATM entre 02:00 y 04:30 al límite del saldo | ❌ No (confusión horaria) | ✅ Sí (seasonality features) |
| `phishing_mule_transfer` | Transferencia a cuenta puente (*money mule*) | Canal web, destinatario no habitual, importe rápido post-login | ❌ No | ✅ Sí (risk score) |
| `hard_subtle_fraud` | Fraude sofisticado (*low and slow*) | Importes moderados sin violar límites rígidos | ❌ No (invisibles a reglas) | ✅ Sí |

---

## 2. Detalle Técnico de los Patrones

### 1. `impossible_travel` (Viaje Imposible)
- **Mecanismo**: El usuario realiza una transacción física en Madrid a las 10:00 y a las 10:15 se registra una transacción en Moscú o Nueva York. La velocidad de desplazamiento requerida supera los $1.000\text{ km/h}$, físicamente imposible para aviación comercial de pasajeros.
- **Features determinantes**:
  - `distance_from_home_km`
  - `travel_speed_kmh`
  - `geo_distance_ip_gps_km`

### 2. `new_device_high_amount` (Nuevo Dispositivo + Importe Elevado)
- **Mecanismo**: El defraudador accede con una huella de hardware o navegador no registrada previamente en el perfil del cliente e inmediatamente emite un pago o transferencia que excede significativamente su media histórica de gasto.
- **Features determinantes**:
  - `is_new_device`
  - `amount_zscore_customer`
  - `amount_to_spend_ratio`

### 3. `velocity_burst` (Ráfaga de Transacciones Rápidas)
- **Mecanismo**: Un script automatizado (*botnet*) ejecuta múltiples compras o autorizaciones de pequeño o mediano importe en segundos o pocos minutos para vaciar el saldo antes de que el titular bloquee la tarjeta.
- **Features determinantes**:
  - `txn_count_10min`
  - `txn_count_1h`
  - `amount_sum_1h`

### 4. `account_takeover` (Toma de Control de Cuenta)
- **Mecanismo**: Un ciberdelincuente realiza múltiples intentos fallidos de autenticación (fuerza bruta o diccionario) en `access_logs`, finalmente acierta o elude la contraseña, y ejecuta una transferencia desde una IP y dispositivo no reconocidos.
- **Features determinantes**:
  - `has_failed_login_history`
  - `is_new_device`
  - `amount_zscore_customer`

### 5. `foreign_country` (Transacción en Jurisdicción Extranjera)
- **Mecanismo**: Operación emitida desde una IP geolocalizada en un país diferente al país de residencia habitual del cliente.
- **Problema de las Reglas**: Una regla estática que bloquee todo pago en el extranjero causará un aluvión de **falsos positivos** cada vez que un cliente viaje por trabajo o turismo legítimo.
- **Solución del Modelo**: El modelo LightGBM pondera el país junto al tipo de comercio, canal, dispositivo e importe para distinguir turistas legítimos de ciberataques.

### 6. `atm_nocturnal_drain` (Vaciado Nocturno en Cajero)
- **Mecanismo**: Retirada masiva de efectivo en cajero automático (ATM) en mitad de la noche (02:00 a 05:00), aprovechando que la víctima duerme y no revisará las notificaciones bancarias inmediatas.
- **Features determinantes**:
  - `channel == "atm"`
  - `is_night == 1`
  - `hour_of_day`

### 7. `phishing_mule_transfer` (Transferencia por Phishing)
- **Mecanismo**: La víctima es engañada para ceder sus credenciales mediante un portal clonado. El atacante transfiere fondos de inmediato hacia una cuenta mula para su posterior blanqueo.
- **Features determinantes**:
  - `channel == "web"`
  - `amount_to_spend_ratio`
  - `risk_level_code`

### 8. `hard_subtle_fraud` (Fraude Sutil y Sofisticado)
- **Mecanismo**: El defraudador modula intencionadamente los importes (por ejemplo, pagos de 80 € a 120 €) para no disparar alertas heurísticas fijas basadas en importes límite (como 500 € o 1.000 €).
- **Ventaja del Modelo ML**: Al analizar la interacción simultánea de 19 dimensiones (frecuencia, hora, ratio de gasto y coordenadas), el modelo detecta la desviación multivariante que escapa a los filtros tradicionales.
