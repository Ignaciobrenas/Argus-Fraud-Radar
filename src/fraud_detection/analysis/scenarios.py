import os
import pandas as pd
import numpy as np
from src.fraud_detection.config import CONFIG, logger
from src.fraud_detection.analysis.kpi import real_time_fraud_pct

def analyze_scenarios(threshold_seconds: float = 2.0) -> pd.DataFrame:
    alerts_file = "data/alerts.parquet"
    if not os.path.exists(alerts_file):
        logger.error(f"Alerts data not found at {alerts_file}. Run stream consumer first.")
        return pd.DataFrame()

    alerts = pd.read_parquet(alerts_file)
    logger.info(f"Loaded {len(alerts)} alerts for scenario comparison (N = {threshold_seconds}s).")

    y_true = alerts["is_fraud"]

    # ========================================================
    # Scenario A: Reglas en Batch Nocturno
    # - Logic: baseline rules
    # - Latency: 3600 - 28800 seconds (overnight execution)
    # - Result: Since latency >> 2.0s, real-time KPI is strictly 0.0%!
    # ========================================================
    df_a = alerts.copy()
    df_a["is_alert"] = df_a["rule_alert"]
    # Simulated batch latency: 4 hours (14400 seconds)
    df_a["detection_latency_seconds"] = 14400.0

    tp_a = ((y_true == 1) & (df_a["is_alert"] == 1)).sum()
    fp_a = ((y_true == 0) & (df_a["is_alert"] == 1)).sum()
    fn_a = ((y_true == 1) & (df_a["is_alert"] == 0)).sum()
    prec_a = (tp_a / (tp_a + fp_a)) * 100.0 if (tp_a + fp_a) > 0 else 0.0
    rec_a = (tp_a / (tp_a + fn_a)) * 100.0 if (tp_a + fn_a) > 0 else 0.0
    kpi_a = real_time_fraud_pct(df_a, threshold_seconds)

    # ========================================================
    # Scenario B: Reglas en Streaming
    # - Logic: baseline rules
    # - Latency: real-time stream latency (~1.0s)
    # - Result: High real-time percentage for rules caught, but lower recall & higher false positives
    # ========================================================
    df_b = alerts.copy()
    df_b["is_alert"] = df_b["rule_alert"]
    # Keep real-time stream latency

    tp_b = ((y_true == 1) & (df_b["is_alert"] == 1)).sum()
    fp_b = ((y_true == 0) & (df_b["is_alert"] == 1)).sum()
    fn_b = ((y_true == 1) & (df_b["is_alert"] == 0)).sum()
    prec_b = (tp_b / (tp_b + fp_b)) * 100.0 if (tp_b + fp_b) > 0 else 0.0
    rec_b = (tp_b / (tp_b + fn_b)) * 100.0 if (tp_b + fn_b) > 0 else 0.0
    kpi_b = real_time_fraud_pct(df_b, threshold_seconds)

    # ========================================================
    # Scenario C: Modelo ML en Streaming
    # - Logic: LightGBM Model
    # - Latency: real-time stream latency (~1.0s)
    # - Result: High real-time KPI, highest recall across all complex patterns, lowest false positives
    # ========================================================
    df_c = alerts.copy()
    # is_alert is already ML alert from consumer

    tp_c = ((y_true == 1) & (df_c["is_alert"] == 1)).sum()
    fp_c = ((y_true == 0) & (df_c["is_alert"] == 1)).sum()
    fn_c = ((y_true == 1) & (df_c["is_alert"] == 0)).sum()
    prec_c = (tp_c / (tp_c + fp_c)) * 100.0 if (tp_c + fp_c) > 0 else 0.0
    rec_c = (tp_c / (tp_c + fn_c)) * 100.0 if (tp_c + fn_c) > 0 else 0.0
    kpi_c = real_time_fraud_pct(df_c, threshold_seconds)

    summary = pd.DataFrame([
        {
            "Scenario": "A (Batch Rules)",
            "Real-Time KPI (%)": round(kpi_a, 2),
            "Recall (%)": round(rec_a, 2),
            "Precision (%)": round(prec_a, 2),
            "False Positives": int(fp_a),
            "Mean Latency (s)": round(float(df_a["detection_latency_seconds"].mean()), 1)
        },
        {
            "Scenario": "B (Streaming Rules)",
            "Real-Time KPI (%)": round(kpi_b, 2),
            "Recall (%)": round(rec_b, 2),
            "Precision (%)": round(prec_b, 2),
            "False Positives": int(fp_b),
            "Mean Latency (s)": round(float(df_b["detection_latency_seconds"].mean()), 3)
        },
        {
            "Scenario": "C (Streaming ML)",
            "Real-Time KPI (%)": round(kpi_c, 2),
            "Recall (%)": round(rec_c, 2),
            "Precision (%)": round(prec_c, 2),
            "False Positives": int(fp_c),
            "Mean Latency (s)": round(float(df_c["detection_latency_seconds"].mean()), 3)
        }
    ])

    print("\n" + "="*80)
    print(f"SCENARIOS COMPARISON TABLE (N = {threshold_seconds}s)")
    print("="*80)
    print(summary.to_string(index=False))
    print("="*80)

    # Per-fraud-type breakdown comparison between Rules and ML
    frauds = alerts[alerts["is_fraud"] == 1]
    breakdown_list = []
    for ftype, grp in frauds.groupby("fraud_type"):
        total_f = len(grp)
        det_rules = int(grp["rule_alert"].sum())
        det_ml = int(grp["is_alert"].sum())
        breakdown_list.append({
            "Fraud Type": ftype,
            "Total Frauds": total_f,
            "Rules Detected": det_rules,
            "Rules Recall (%)": round((det_rules / total_f) * 100.0, 1),
            "ML Detected": det_ml,
            "ML Recall (%)": round((det_ml / total_f) * 100.0, 1)
        })

    df_breakdown = pd.DataFrame(breakdown_list)
    print("\nPER-PATTERN FRAUD DETECTION BREAKDOWN (Rules vs ML):")
    print(df_breakdown.to_string(index=False))
    print("="*80 + "\n")

    return summary

if __name__ == "__main__":
    analyze_scenarios()
