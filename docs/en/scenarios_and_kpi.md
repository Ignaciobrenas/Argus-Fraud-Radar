# Comparative Scenario Benchmark & Real-Time KPI Evaluation
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

The central objective of this project is to answer the core business question: **What is the measurable effectiveness of an AI-driven real-time streaming fraud architecture compared to traditional banking rule engines?**

---

## 1. Primary Lineage KPI Definition

The primary KPI measures the percentage of verified fraudulent transactions alerted within the strict sub-second real-time latency threshold ($N = 2.0$ seconds):

$$\text{Real-Time Fraud Detected (\%)} = \frac{\text{Frauds alerted with latency } \le N \text{ seconds}}{\text{Total verified frauds}} \times 100$$

### Immutable Design Constraints:
- **Real-Time Latency Threshold ($N$)**: **2.0 seconds** (the critical window to halt a transfer before automated interbank settlement).
- **Target Fraud Prevalence**: ~1.0% (severe class imbalance mirroring real retail banking environments).
- **Ground Truth**: Binary `is_fraud` label (retained strictly for evaluation and audit, never fed as a feature to models).

---

## 2. Definition of the Three Comparative Scenarios

To isolate the impact of processing latency (Batch vs Streaming) from algorithmic efficacy (Heuristic Rules vs Machine Learning), three parallel scenarios are benchmarked:

### Scenario A: Batch Heuristic Rules (Traditional Paradigm)
- **Mode**: Periodic batch job executing every 4 hours (mean latency of 14,400 seconds).
- **Algorithm**: Standard heuristic rules (impossible travel, new device + high amount, velocity $\ge 3$ txns/10 min, foreign country, failed logins).
- **Business Flaw**: Although the rules identify 60.27% of frauds after 4 hours, **the money has already left the bank**. Because latency is far greater than 2 seconds, the real-time KPI is **0.00%**.

### Scenario B: Streaming Heuristic Rules
- **Mode**: Continuous event streaming with sub-second latency (mean latency of 0.285 seconds).
- **Algorithm**: The same heuristic rules executed in real time.
- **Advantage**: Detects fraud within the 2-second SLA, achieving 60.27% real-time KPI.
- **Business Flaw**: Rigid thresholding creates an **unacceptable flood of false positives** (478 false alarms, precision of only 21.64%), generating severe customer friction and analyst alert fatigue.

### Scenario C: Streaming Machine Learning (Proposed Architecture)
- **Mode**: Continuous event streaming with sub-second latency (mean latency of 0.285 seconds).
- **Algorithm**: Supervised **LightGBM Classifier** calibrated across 19 features with decision threshold $\theta = 0.890$ to cap the false positive rate under $0.05\%$.
- **Business Result**: Optimal performance with **79.91% real-time fraud detection**, **97.22% precision**, and only **5 false positives** across 20,000 transactions.

---

## 3. Experimental Benchmark Results Table

| Scenario | Mode | Engine | Mean Latency | Real-Time KPI (%) | Total Recall (%) | Precision (%) | False Positives |
|---|---|---|---|---|---|---|---|
| **A** | Batch (4h) | Heuristic Rules | 14,400.00 s | **0.00 %** | 60.27 % | 21.64 % | 478 |
| **B** | Streaming | Heuristic Rules | 0.285 s | **60.27 %** | 60.27 % | 21.64 % | 478 |
| **C** | Streaming | **LightGBM ML** | **0.285 s** | **79.91 %** | **79.91 %** | **97.22 %** | **5** |

---

## 4. Breakdown by Fraud Pattern (Rules vs. ML)

| Fraud Pattern | Total Frauds | Rules Caught | Rules Recall (%) | ML Caught | ML Recall (%) |
|---|---|---|---|---|---|
| `impossible_travel` | 55 | 32 | 58.2 % | **55** | **100.0 %** |
| `foreign_country` | 47 | 26 | 55.3 % | **47** | **100.0 %** |
| `new_device_high_amount` | 46 | 40 | 87.0 % | **46** | **100.0 %** |
| `account_takeover` | 39 | 32 | 82.1 % | **27** | **69.2 %** |
| `velocity_burst` | 32 | 2 | 6.2 % | 0 | 0.0 % |
| **Total** | **219** | **132** | **60.27 %** | **175** | **79.91 %** |

---

## 5. Financial Impact & ROI Analysis

Evaluating monetary savings over the 20,000 streaming transaction test stream confirms the financial superiority of Scenario C:

| Financial Metric | Scenario B (Streaming Rules) | Scenario C (Streaming ML) | ML Differential Impact |
|---|---|---|---|
| **Money Saved (Fraud Prevented)** | 24,810.40 € | **34,359.13 €** | **+9,548.73 €** (+38.5%) |
| **Money Lost (Missed Fraud)** | 12,910.13 € | **3,361.40 €** | **-9,548.73 €** (-74.0%) |
| **Operational False Positive Cost** | ~11,950.00 € (478 cases) | **~125.00 €** (5 cases) | **-11,825.00 €** (-99.0%) |
| **Legitimate Customer Friction** | Severe (alert fatigue) | **Negligible (< 0.03%)** | Brand equity preserved |

---

## 6. Executive Conclusions

1. **Streaming alone is insufficient**: Transitioning from Batch (A) to Streaming (B) satisfies the latency constraint but causes an operational disaster by issuing 478 false alarms.
2. **Machine Learning is the critical discriminator**: Scenario C pairs the speed of streaming (285 ms) with the non-linear precision of LightGBM, lifting real-time fraud detection to 79.91% while dropping false positives to 5.
3. **Immediate Bottom-Line ROI**: The bank saves over 34,000 € per 20,000 transactions processed while virtually eliminating chargeback administrative costs.
