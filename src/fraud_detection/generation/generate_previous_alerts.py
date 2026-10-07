import pandas as pd
import numpy as np
from faker import Faker
from typing import List, Dict, Tuple

def generate_previous_fraud_alerts(
    df_history: pd.DataFrame,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates historical fraud alerts.
    CRITICAL: Only references transactions from the historical period to prevent data leakage.
    """
    Faker.seed(seed)
    np.random.seed(seed)
    fake = Faker()

    # Get known frauds from the history period
    hist_frauds = df_history[df_history["is_fraud"] == 1]
    hist_normals = df_history[df_history["is_fraud"] == 0]

    alerts = []
    alert_counter = 1

    # Most historical frauds triggered an alert (e.g. 85%)
    for _, row in hist_frauds.iterrows():
        if np.random.rand() < 0.85:
            alerts.append({
                "alert_id": f"alt-{alert_counter:06d}",
                "customer_id": row["customer_id"],
                "transaction_id": row["transaction_id"],
                "alert_timestamp": row["event_timestamp"],
                "alert_type": "high_risk_rule",
                "resolution": "confirmed"
            })
            alert_counter += 1

    # Add a small proportion of false positive alerts on normal transactions in history
    sample_fp = hist_normals.sample(n=min(len(hist_normals), int(len(alerts) * 0.3)), random_state=seed)
    for _, row in sample_fp.iterrows():
        alerts.append({
            "alert_id": f"alt-{alert_counter:06d}",
            "customer_id": row["customer_id"],
            "transaction_id": row["transaction_id"],
            "alert_timestamp": row["event_timestamp"],
            "alert_type": "velocity_warning",
            "resolution": "false_positive"
        })
        alert_counter += 1

    df_alerts = pd.DataFrame(alerts)
    if not df_alerts.empty:
        df_alerts = df_alerts.sort_values("alert_timestamp").reset_index(drop=True)
    return df_alerts
