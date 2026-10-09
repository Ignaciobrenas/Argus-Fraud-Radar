import pandas as pd
import numpy as np

def compute_behavior_features(
    df_tx: pd.DataFrame,
    df_cust: pd.DataFrame,
    devices_dict: dict,
    access_logs_df: pd.DataFrame = None,
    alerts_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Computes customer behavioral features, joins customer profiles, device risks,
    access log anomaly flags, and historical alert counts.
    """
    df = df_tx.copy()
    
    # 1. Temporal conversion
    if "dt" not in df.columns:
        df["dt"] = pd.to_datetime(df["event_timestamp"], utc=True)
        
    df["hour_of_day"] = df["dt"].dt.hour
    df["day_of_week"] = df["dt"].dt.dayofweek
    df["is_night"] = ((df["hour_of_day"] >= 0) & (df["hour_of_day"] <= 6)).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # 2. Merge Customer Profile
    cust_cols = ["customer_id", "age", "country", "home_city", "home_lat", "home_lon", "risk_level", "account_open_date", "avg_monthly_spend"]
    available_cust_cols = [c for c in cust_cols if c in df_cust.columns]
    
    # Deduplicate customer profile if needed
    df_cust_clean = df_cust[available_cust_cols].drop_duplicates(subset=["customer_id"])
    df = df.merge(df_cust_clean, on="customer_id", how="left")

    # Risk level encoding
    risk_map = {"low": 0, "medium": 1, "high": 2}
    df["risk_level_code"] = df["risk_level"].map(risk_map).fillna(0).astype(int)

    # Account age in days
    if "account_open_date" in df.columns:
        open_dt = pd.to_datetime(df["account_open_date"], utc=True, errors="coerce")
        df["account_age_days"] = np.clip((df["dt"] - open_dt).dt.total_seconds() / 86400.0, 1.0, 3650.0).fillna(365.0)
    else:
        df["account_age_days"] = 365.0

    # 3. Customer Baseline Spending & Z-Score
    # Group by customer_id to get mean and std of historical amount
    cust_stats = df.groupby("customer_id")["amount"].agg(["mean", "std"]).reset_index()
    cust_stats.columns = ["customer_id", "cust_amt_mean", "cust_amt_std"]
    cust_stats["cust_amt_std"] = cust_stats["cust_amt_std"].fillna(1.0).replace(0.0, 1.0)
    
    df = df.merge(cust_stats, on="customer_id", how="left")
    df["amount_zscore_customer"] = (df["amount"] - df["cust_amt_mean"]) / (df["cust_amt_std"] + 1e-5)
    df["amount_zscore_customer"] = df["amount_zscore_customer"].fillna(0.0).clip(-3.0, 10.0)

    # Amount to expected daily spend ratio
    expected_daily = np.maximum(5.0, df["avg_monthly_spend"].fillna(150.0) / 30.0)
    df["amount_to_spend_ratio"] = np.clip(df["amount"] / expected_daily, 0.0, 100.0)

    # 4. Device Risk: Is New / Unrecognized Device
    def check_new_device(row):
        cid = row.get("customer_id")
        did = row.get("device_id")
        known = devices_dict.get(cid, set())
        return 0 if (did in known or len(known) == 0) else 1

    df["is_new_device"] = df.apply(check_new_device, axis=1)

    # 5. Access Logs: Failed Logins
    if access_logs_df is not None and not access_logs_df.empty and "event_type" in access_logs_df.columns:
        failed_logins = access_logs_df[access_logs_df["event_type"] == "login_failed"]
        failed_custs = set(failed_logins["customer_id"].unique())
        df["has_failed_login_history"] = df["customer_id"].isin(failed_custs).astype(int)
    else:
        df["has_failed_login_history"] = 0

    # 6. Previous Alerts: Customer Prior Fraud Alert Count
    if alerts_df is not None and not alerts_df.empty and "customer_id" in alerts_df.columns:
        alert_counts = alerts_df.groupby("customer_id")["alert_id"].count().to_dict()
        df["previous_alert_count"] = df["customer_id"].map(alert_counts).fillna(0).astype(int)
    else:
        df["previous_alert_count"] = 0

    # 7. Foreign Country Discrepancy
    if "ip_country" in df.columns and "country" in df.columns:
        df["is_foreign_country"] = (df["ip_country"] != df["country"]).astype(int)
    else:
        df["is_foreign_country"] = 0

    return df
