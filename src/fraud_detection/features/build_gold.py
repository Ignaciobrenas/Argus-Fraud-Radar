import os
import json
import pandas as pd
import numpy as np
from src.fraud_detection.config import CONFIG, logger
from src.fraud_detection.features.geo import (
    calculate_distance_from_home_km,
    calculate_geo_distance_ip_gps_km,
    haversine_distance_km
)
from src.fraud_detection.features.velocity import compute_rolling_velocity
from src.fraud_detection.features.behavior import compute_behavior_features

def run_build_gold():
    logger.info("==================================================")
    logger.info("Starting Gold Layer Multi-Feature Engineering...")
    logger.info("==================================================")

    silver_path = CONFIG["paths"]["silver"]
    gold_path = CONFIG["paths"]["gold"]
    raw_path = CONFIG["paths"]["raw"]
    os.makedirs(gold_path, exist_ok=True)

    # 1. Load Silver transactions
    tx_file = f"{silver_path}/transactions"
    if not os.path.exists(tx_file):
        logger.error(f"Silver transactions not found at {tx_file}. Run build_silver first.")
        return

    df_tx = pd.read_parquet(tx_file)
    df_tx = df_tx.sort_values("event_timestamp").reset_index(drop=True)
    logger.info(f"Loaded {len(df_tx)} transactions from Silver.")

    # 2. Load Customer Profile
    cust_file = f"{silver_path}/customer_profile"
    if os.path.exists(cust_file):
        df_cust = pd.read_parquet(cust_file)
    else:
        df_cust = pd.read_csv(f"{raw_path}/customer_profile.csv")

    # 3. Load Devices
    dev_file = f"{silver_path}/device_data"
    if os.path.exists(dev_file):
        df_dev = pd.read_parquet(dev_file)
    else:
        with open(f"{raw_path}/device_data.json", "r") as f:
            df_dev = pd.DataFrame(json.load(f))

    devices_dict = {}
    for _, row in df_dev.iterrows():
        devices_dict.setdefault(row["customer_id"], set()).add(row["device_id"])

    # 4. Load User Locations
    loc_file = f"{silver_path}/user_location"
    if os.path.exists(loc_file):
        df_loc = pd.read_parquet(loc_file)
    elif os.path.exists(f"{raw_path}/user_location.json"):
        with open(f"{raw_path}/user_location.json", "r") as f:
            df_loc = pd.DataFrame(json.load(f))
    else:
        df_loc = pd.DataFrame()

    # Flatten GPS if nested
    if not df_loc.empty and "gps" in df_loc.columns:
        if isinstance(df_loc["gps"].iloc[0], dict):
            df_loc["gps_lat"] = df_loc["gps"].apply(lambda g: g.get("lat") if isinstance(g, dict) else np.nan)
            df_loc["gps_lon"] = df_loc["gps"].apply(lambda g: g.get("lon") if isinstance(g, dict) else np.nan)
        elif "lat" in df_loc.columns and "lon" in df_loc.columns:
            df_loc["gps_lat"] = df_loc["lat"]
            df_loc["gps_lon"] = df_loc["lon"]

    # 5. Load Access Logs
    logs_file = f"{silver_path}/access_logs"
    if os.path.exists(logs_file):
        df_logs = pd.read_parquet(logs_file)
    elif os.path.exists(f"{raw_path}/access_logs.jsonl"):
        df_logs = pd.read_json(f"{raw_path}/access_logs.jsonl", lines=True)
    else:
        df_logs = pd.DataFrame()

    # 6. Load Historical Alerts
    alerts_file = f"{silver_path}/previous_fraud_alerts"
    if os.path.exists(alerts_file):
        df_alerts = pd.read_parquet(alerts_file)
    elif os.path.exists(f"{raw_path}/previous_fraud_alerts.csv"):
        df_alerts = pd.read_csv(f"{raw_path}/previous_fraud_alerts.csv")
    else:
        df_alerts = pd.DataFrame()

    # --- Feature Computation ---

    # A. Merge Locations
    if not df_loc.empty:
        loc_cols = [c for c in ["transaction_id", "ip_address", "ip_country", "gps_lat", "gps_lon"] if c in df_loc.columns]
        df_tx = df_tx.merge(df_loc[loc_cols], on="transaction_id", how="left")

    # B. Compute Behavioral features
    logger.info("Computing behavioral and customer profile risk features...")
    df_tx = compute_behavior_features(
        df_tx=df_tx,
        df_cust=df_cust,
        devices_dict=devices_dict,
        access_logs_df=df_logs,
        alerts_df=df_alerts
    )

    # C. Compute Velocity features
    logger.info("Computing rolling window velocity features...")
    df_tx = compute_rolling_velocity(df_tx)

    # D. Compute Geographic features
    logger.info("Computing geographic distance and speed features...")
    gps_lat = df_tx["gps_lat"].fillna(df_tx["home_lat"]) if "gps_lat" in df_tx.columns else df_tx["home_lat"]
    gps_lon = df_tx["gps_lon"].fillna(df_tx["home_lon"]) if "gps_lon" in df_tx.columns else df_tx["home_lon"]

    df_tx["distance_from_home_km"] = calculate_distance_from_home_km(
        gps_lat, gps_lon, df_tx["home_lat"], df_tx["home_lon"]
    ).fillna(0.0)

    # Discrepancy between IP and GPS
    # If IP country != customer home country, estimate significant discrepancy
    if "is_foreign_country" in df_tx.columns:
        df_tx["geo_distance_ip_gps_km"] = np.where(
            df_tx["is_foreign_country"] == 1,
            df_tx["distance_from_home_km"] + 1200.0,
            np.clip(df_tx["distance_from_home_km"] * 0.2, 0.0, 50.0)
        )
    else:
        df_tx["geo_distance_ip_gps_km"] = 0.0

    # Calculate Travel Speed between consecutive transactions for the customer
    df_tx = df_tx.sort_values(["customer_id", "dt"]).reset_index(drop=True)
    prev_dt = df_tx.groupby("customer_id")["dt"].shift(1)
    prev_lat = df_tx.groupby("customer_id")["gps_lat"].shift(1).fillna(df_tx["home_lat"])
    prev_lon = df_tx.groupby("customer_id")["gps_lon"].shift(1).fillna(df_tx["home_lon"])

    time_diff_hours = (df_tx["dt"] - prev_dt).dt.total_seconds() / 3600.0
    dist_between_txns = haversine_distance_km(gps_lat, gps_lon, prev_lat, prev_lon)

    # Speed in km/h (avoid division by 0; clip to realistic limits)
    speed_kmh = dist_between_txns / np.clip(time_diff_hours, 0.001, None)
    df_tx["travel_speed_kmh"] = np.where(time_diff_hours.isna(), 0.0, np.clip(speed_kmh, 0.0, 5000.0))

    # Clean intermediate columns
    drop_temp = [c for c in ["dt", "cust_amt_mean", "cust_amt_std"] if c in df_tx.columns]
    df_tx = df_tx.drop(columns=drop_temp)

    # Save to Gold features Parquet (both as file and directory for full compatibility)
    import shutil
    df_tx.to_parquet(f"{gold_path}/features.parquet", index=False)
    features_dir = f"{gold_path}/features"
    if os.path.exists(features_dir):
        shutil.rmtree(features_dir)
    os.makedirs(features_dir, exist_ok=True)
    df_tx.to_parquet(f"{features_dir}/features.parquet", index=False)
    logger.info(f"Saved Gold features table to {gold_path}/features ({len(df_tx)} rows, {len(df_tx.columns)} columns)")
    logger.info("Gold layer feature engineering completed successfully!")

if __name__ == "__main__":
    run_build_gold()
