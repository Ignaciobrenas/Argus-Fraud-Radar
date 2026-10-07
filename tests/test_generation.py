import os
import pandas as pd
from src.fraud_detection.config import CONFIG

def test_config_seed_exists():
    assert "seed" in CONFIG
    assert type(CONFIG["seed"]) is int

def test_fraud_rate_is_valid():
    raw_path = CONFIG["paths"]["raw"]
    tx_file = f"{raw_path}/transactions.csv"
    if os.path.exists(tx_file):
        df = pd.read_csv(tx_file)
        rate = df["is_fraud"].mean()
        assert 0.005 <= rate <= 0.05, f"Fraud rate {rate} outside expected range [0.5%, 5%]"

def test_referential_integrity():
    raw_path = CONFIG["paths"]["raw"]
    cust_file = f"{raw_path}/customer_profile.csv"
    tx_file = f"{raw_path}/transactions.csv"
    if os.path.exists(cust_file) and os.path.exists(tx_file):
        df_cust = pd.read_csv(cust_file)
        df_tx = pd.read_csv(tx_file)
        valid_custs = set(df_cust["customer_id"])
        tx_custs = set(df_tx["customer_id"])
        # Every customer in transactions must exist in customer_profile
        assert tx_custs.issubset(valid_custs), "Referential integrity broken: unknown customer_ids found"

def test_no_data_leakage_in_previous_alerts():
    raw_path = CONFIG["paths"]["raw"]
    alerts_file = f"{raw_path}/previous_fraud_alerts.csv"
    stream_tx_file = f"{raw_path}/transactions.csv"
    if os.path.exists(alerts_file) and os.path.exists(stream_tx_file):
        df_alerts = pd.read_csv(alerts_file)
        df_stream = pd.read_csv(stream_tx_file)
        stream_tx_ids = set(df_stream["transaction_id"])
        alert_tx_ids = set(df_alerts["transaction_id"])
        # No stream transaction ID should ever appear in historical alerts!
        overlap = stream_tx_ids.intersection(alert_tx_ids)
        assert len(overlap) == 0, f"DATA LEAKAGE DETECTED: {len(overlap)} stream transactions in previous_fraud_alerts!"

def test_fraud_patterns_injected():
    raw_path = CONFIG["paths"]["raw"]
    tx_file = f"{raw_path}/transactions.csv"
    if os.path.exists(tx_file):
        df = pd.read_csv(tx_file)
        frauds = df[df["is_fraud"] == 1]
        patterns = set(frauds["fraud_type"].dropna().unique())
        assert len(patterns) >= 3, f"Expected multiple fraud patterns injected, found: {patterns}"
