import os
import pandas as pd
import numpy as np
from src.fraud_detection.config import CONFIG, logger

def apply_baseline_rules(df: pd.DataFrame) -> pd.Series:
    """
    Applies production-grade baseline rule heuristics:
    1. High amount anomaly: z-score > 3.0 or absolute amount > 4000 EUR
    2. Impossible travel: physical velocity > 800 km/h or IP/GPS distance > 1000 km
    3. Velocity burst: >= 4 transactions within 10 minutes
    4. Account takeover: >= 3 recent failed logins on a new device
    5. Foreign country high spend: foreign country with amount > 800 EUR
    """
    rule_amount = (df.get("amount_zscore_customer", 0) > 3.0) | (df["amount"] > 4000.0)
    rule_travel = (df.get("travel_speed_kmh", 0) > 800.0) | (df.get("geo_distance_ip_gps_km", 0) > 1000.0)
    rule_velocity = df.get("txn_count_10min", 0) >= 4
    rule_ato = (df.get("failed_logins_before_txn", 0) >= 3) & (df.get("is_new_device", 0) == 1)
    rule_foreign = (df.get("is_foreign_country", 0) == 1) & (df["amount"] > 800.0)

    alerts = rule_amount | rule_travel | rule_velocity | rule_ato | rule_foreign
    return alerts.astype(int)

def evaluate_baseline():
    gold_path = CONFIG["paths"]["gold"]
    features_file = f"{gold_path}/features.parquet"
    if not os.path.exists(features_file):
        logger.error(f"Features file not found at {features_file}. Run build_gold first.")
        return

    df = pd.read_parquet(features_file)
    logger.info(f"Evaluating Baseline Rules on {len(df)} transactions...")

    df["rule_alert"] = apply_baseline_rules(df)

    y_true = df["is_fraud"]
    y_pred = df["rule_alert"]

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    logger.info("==================================================")
    logger.info("Baseline Rules Evaluation Results:")
    logger.info(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
    logger.info(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
    logger.info(f"F1-Score:  {f1:.4f}")
    logger.info(f"Confusion Matrix: TP={tp}, FP={fp}, FN={fn}, TN={tn}")

    # Breakdown by fraud type
    if "fraud_type" in df.columns:
        logger.info("\nBaseline Detection by Fraud Type:")
        frauds_df = df[df["is_fraud"] == 1]
        for ftype, group in frauds_df.groupby("fraud_type"):
            detected = group["rule_alert"].sum()
            total = len(group)
            pct = (detected / total) * 100.0
            logger.info(f" - {ftype:<25}: {detected}/{total} ({pct:.1f}%)")
    logger.info("==================================================")

if __name__ == "__main__":
    evaluate_baseline()
