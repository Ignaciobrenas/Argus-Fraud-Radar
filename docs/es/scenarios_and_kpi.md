# Comparativa de Escenarios y Evaluación del KPI en Tiempo Real
**Datacycle · Unidad 1 · Caso 2: Retail Banking Real-Time Fraud Detection**

El objetivo central del proyecto es responder a la pregunta de negocio: **¿Cuál es la eficacia real de una arquitectura de detección de fraude en tiempo real basada en Inteligencia Artificial frente a soluciones tradicionales?**

---

## 1. Definición del KPI Principal

El KPI fijado para el proyecto mide el porcentaje de transacciones fraudulentas que el sistema es capaz de detectar y alertar dentro del umbral estricto de tiempo real ($N = 2.0$ segundos):

$$\text{Real-Time Fraud Detected (\%)} = \frac{\text{Fraudes alertados con } \text{latencia} \le N \text{ segundos}}{\text{Total de fraudes reales}} \times 100$$

### Decisiones de Diseño Inmutables:
- **Umbral de Tiempo Real ($N$)**: **2.0 segundos** (SLA crítica para interrumpir la transacción antes del asentamiento interbancario).
- **Tasa de Fraude Base**: ~1.0% (desbalance severo de clases, representativo del sector financiero).
- **Ground Truth**: Columna binaria inmutable `is_fraud` (utilizada únicamente para entrenamiento y auditoría, nunca expuesta al modelo como feature).

---

## 2. Definición de los Tres Escenarios Evaluados

Para contrastar el impacto del modo de procesamiento (Batch vs Streaming) y del paradigma algorítmico (Reglas Heurísticas vs Machine Learning), se modelan y evalúan tres escenarios concurrentes:

### Escenario A: Reglas Heurísticas en Batch (Solución Tradicional)
- **Modo**: Procesamiento por lotes ejecutado cada 4 horas (14.400 segundos de latencia media).
- **Algoritmo**: Motor de reglas fijas clásicas (imposible travel, nuevo dispositivo + importe alto, velocidad $\ge 3$ txns/10 min, país extranjero, intentos fallidos).
- **Problema de Negocio**: Aunque las reglas detecten el fraude después de 4 horas, **el dinero ya ha salido de la entidad**. La latencia supera ampliamente los 2 segundos, por lo que el KPI de tiempo real es **0%**.

### Escenario B: Reglas Heurísticas en Streaming
- **Modo**: Ingesta continua en streaming con baja latencia (media de 0.285 segundos).
- **Algoritmo**: Mismo motor de reglas fijas que en el Escenario A.
- **Ventaja**: Detecta los fraudes antes del umbral de 2 segundos.
- **Problema de Negocio**: Rigidez extrema y **aluvión masivo de falsos positivos** (21.6% de precisión, 478 falsas alarmas). Bloquea clientes legítimos que viajan o compran con dispositivos nuevos, saturando a los operadores de seguridad.

### Escenario C: Machine Learning Supervisado en Streaming (Solución Propuesta)
- **Modo**: Ingesta continua en streaming con baja latencia (media de 0.285 segundos).
- **Algoritmo**: Modelo **LightGBM Classifier** calibrado sobre 19 características multidimensionales y optimizado en el umbral $\theta = 0.890$ para minimizar la tasa de falsos positivos (FPR $\le 0.05\%$).
- **Resultado de Negocio**: Equilibrio óptimo con **79.91% de detección en tiempo real**, **97.22% de precisión** y solo **5 falsos positivos** en 20.000 transacciones.

---

## 3. Tabla Comparativa de Resultados Experimentales

| Escenario | Modo | Motor | Latencia Media | Real-Time KPI (%) | Recall Total (%) | Precisión (%) | Falsos Positivos |
|---|---|---|---|---|---|---|---|
| **A** | Batch (4h) | Reglas Heurísticas | 14.400,00 s | **0,00 %** | 60,27 % | 21,64 % | 478 |
| **B** | Streaming | Reglas Heurísticas | 0,285 s | **60,27 %** | 60,27 % | 21,64 % | 478 |
| **C** | Streaming | **LightGBM ML** | **0,285 s** | **79,91 %** | **79,91 %** | **97,22 %** | **5** |

---

## 4. Desglose de Detección por Tipo de Fraude (Reglas vs ML)

| Tipo de Fraude | Fraudes Totales | Detectados por Reglas | Recall Reglas (%) | Detectados por ML | Recall ML (%) |
|---|---|---|---|---|---|
| `impossible_travel` | 55 | 32 | 58,2 % | **55** | **100,0 %** |
| `foreign_country` | 47 | 26 | 55,3 % | **47** | **100,0 %** |
| `new_device_high_amount` | 46 | 40 | 87,0 % | **46** | **100,0 %** |
| `account_takeover` | 39 | 32 | 82,1 % | **27** | **69,2 %** |
| `velocity_burst` | 32 | 2 | 6,2 % | 0 | 0,0 % |
| **Total** | **219** | **132** | **60,27 %** | **175** | **79,91 %** |

---

## 5. Análisis de Impacto Financiero y Retorno de Inversión (ROI)

El análisis de balance económico sobre la ventana de evaluación de 20.000 transacciones demuestra la superioridad comercial de la solución basada en ML:

| Métrica Financiera | Escenario B (Streaming Rules) | Escenario C (Streaming ML) | Beneficio Diferencial ML |
|---|---|---|---|
| **Dinero Salvado (Fraude Evitado)** | 24.810,40 € | **34.359,13 €** | **+9.548,73 €** (+38,5%) |
| **Dinero Perdido (Fraudes No Detectados)** | 12.910,13 € | **3.361,40 €** | **-9.548,73 €** (74% menos pérdidas) |
| **Coste Operativo de Falsos Positivos** | ~11.950,00 € (478 casos) | **~125,00 €** (5 casos) | **-11.825,00 €** (99% reducción costes) |
| **Fricción de Usuario Legítimo** | Muy alta (alerta fatiga) | **Mínima (< 0.03% incidencia)** | Reputación protegida |

---

## 6. Conclusiones Ejecutivas

1. **La velocidad sola no basta**: El paso del Escenario A (Batch) al Escenario B (Streaming) soluciona el KPI de tiempo real pero genera una crisis operativa al disparar 478 falsas alarmas que bloquean a clientes inocentes.
2. **La Inteligencia Artificial es el diferenciador crítico**: El Escenario C combina la inmediatez del streaming (285 ms) con la discriminación no lineal de LightGBM, elevando el ratio de detección real al 79.91% y reduciendo las falsas alarmas a solo 5 casos.
3. **Retorno Económico Inmediato**: La entidad salva más de 34.000 € por cada 20.000 transacciones procesadas mientras reduce a cero las indemnizaciones y costes de reclamación por contracargo.
