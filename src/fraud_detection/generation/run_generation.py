import os
import json
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from faker import Faker
from src.fraud_detection.config import CONFIG, logger

def generate_all():
    seed = int(CONFIG.get("seed", 42))
    np.random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    raw_path = CONFIG["paths"]["raw"]
    os.makedirs(raw_path, exist_ok=True)

    n_cust = int(CONFIG.get("n_customers", 5000))
    n_hist = int(CONFIG.get("n_history_transactions", 100000))
    n_stream = int(CONFIG.get("n_stream_transactions", 20000))
    fraud_rate = float(CONFIG.get("fraud_rate", 0.012))

    history_start = pd.to_datetime(CONFIG.get("history_start", "2026-01-01"))
    history_end = pd.to_datetime(CONFIG.get("history_end", "2026-06-30 23:59:59"))
    stream_start = pd.to_datetime(CONFIG.get("stream_start", "2026-07-01"))
    stream_end = pd.to_datetime(CONFIG.get("stream_end", "2026-07-31 23:59:59"))

    logger.info(f"Starting Enterprise synthetic data generation: {n_cust} customers, {n_hist} history txns, {n_stream} stream txns (fraud_rate={fraud_rate:.3f})...")

    # -------------------------------------------------------------
    # 1. Customers Profile
    # -------------------------------------------------------------
    logger.info("Generating customer profiles...")
    country_pool = ["ES", "FR", "DE", "IT", "PT", "GB", "US", "NL", "BE", "MX"]
    city_map = {
        "ES": ("Madrid", 40.4168, -3.7038),
        "FR": ("Paris", 48.8566, 2.3522),
        "DE": ("Berlin", 52.5200, 13.4050),
        "IT": ("Rome", 41.9028, 12.4964),
        "PT": ("Lisbon", 38.7223, -9.1393),
        "GB": ("London", 51.5074, -0.1278),
        "US": ("New York", 40.7128, -74.0060),
        "NL": ("Amsterdam", 52.3676, 4.9041),
        "BE": ("Brussels", 50.8503, 4.3517),
        "MX": ("Mexico City", 19.4326, -99.1332)
    }

    cust_ids = [f"c-{uuid.uuid4().hex[:8]}" for _ in range(n_cust)]
    cust_ages = np.random.randint(18, 80, size=n_cust)
    cust_countries = np.random.choice(country_pool, size=n_cust, p=[0.45, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04, 0.03, 0.03, 0.02])
    
    cities, lats, lons = [], [], []
    for c in cust_countries:
        base_city, base_lat, base_lon = city_map[c]
        cities.append(base_city)
        # Jitter around base coords (+/- 0.5 deg)
        lats.append(round(base_lat + np.random.uniform(-0.4, 0.4), 4))
        lons.append(round(base_lon + np.random.uniform(-0.4, 0.4), 4))

    cust_risk = np.random.choice(["low", "medium", "high"], size=n_cust, p=[0.75, 0.20, 0.05])
    
    # Account open date between 5 years ago and 6 months ago
    days_back = np.random.randint(180, 1825, size=n_cust)
    now_ref = pd.Timestamp.now()
    open_dates = [(now_ref - pd.Timedelta(days=int(d))).strftime("%Y-%m-%d") for d in days_back]
    
    # Log-normal spend: median around €150/month, positive skew
    avg_monthly_spend = np.round(np.random.lognormal(mean=5.2, sigma=0.8, size=n_cust), 2)
    avg_monthly_spend = np.clip(avg_monthly_spend, 50.0, 15000.0)

    df_cust = pd.DataFrame({
        "customer_id": cust_ids,
        "age": cust_ages,
        "country": cust_countries,
        "home_city": cities,
        "home_lat": lats,
        "home_lon": lons,
        "risk_level": cust_risk,
        "account_open_date": open_dates,
        "avg_monthly_spend": avg_monthly_spend
    })
    df_cust.to_csv(f"{raw_path}/customer_profile.csv", index=False)
    logger.info(f"Saved {len(df_cust)} customer profiles to {raw_path}/customer_profile.csv")

    # -------------------------------------------------------------
    # 2. Devices
    # -------------------------------------------------------------
    logger.info("Generating customer devices...")
    device_records = []
    cust_device_map = {}
    
    for cid in cust_ids:
        n_dev = np.random.choice([1, 2, 3], p=[0.65, 0.28, 0.07])
        c_dev_list = []
        for d_idx in range(n_dev):
            dev_id = f"d-{uuid.uuid4().hex[:8]}"
            c_dev_list.append(dev_id)
            d_type = "mobile" if d_idx == 0 else np.random.choice(["mobile", "web"])
            os_name = "Android" if np.random.rand() > 0.45 else "iOS" if d_type == "mobile" else "Windows"
            browser = "Chrome" if os_name in ["Android", "Windows"] else "Safari"
            is_rooted = bool(np.random.rand() > 0.97) # 3% rooted devices
            
            device_records.append({
                "device_id": dev_id,
                "customer_id": cid,
                "device_type": d_type,
                "os": os_name,
                "browser": browser,
                "app_version": "2.4.0",
                "first_seen": (now_ref - pd.Timedelta(days=int(np.random.randint(30, 700)))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_rooted": is_rooted
            })
        cust_device_map[cid] = c_dev_list

    with open(f"{raw_path}/device_data.json", "w") as f:
        json.dump(device_records, f)
    logger.info(f"Saved {len(device_records)} devices to {raw_path}/device_data.json")

    # -------------------------------------------------------------
    # 3. Transactions (History & Stream)
    # -------------------------------------------------------------
    logger.info("Generating transactions, locations, logs, and alerts...")
    
    categories = ["retail", "groceries", "travel", "entertainment", "electronics", "services", "transfer"]
    channels = ["mobile", "web", "pos"]
    fraud_types = ["impossible_travel", "new_device_high_amount", "velocity_burst", "account_takeover", "foreign_country"]

    # Fast indexed customer lookup
    cust_dict = df_cust.set_index("customer_id").to_dict(orient="index")

    def generate_partition(n_tx, start_dt, end_dt, is_stream_batch=False):
        # Customer selection
        c_idx_arr = np.random.randint(0, n_cust, size=n_tx)
        selected_cust_ids = [cust_ids[idx] for idx in c_idx_arr]
        
        # Timestamps with daily seasonality (peak at 14h, low at 4h)
        total_seconds = (end_dt - start_dt).total_seconds()
        raw_seconds = np.random.uniform(0, total_seconds, size=n_tx)
        dt_base = start_dt + pd.to_timedelta(raw_seconds, unit='s')
        
        # Fraud assignment
        fraud_mask = np.random.rand(n_tx) < fraud_rate
        assigned_fraud_types = np.where(fraud_mask, np.random.choice(fraud_types, size=n_tx), "")
        
        tx_rows = []
        loc_rows = []
        access_log_rows = []
        alert_rows = []

        for i in range(n_tx):
            cid = selected_cust_ids[i]
            c_meta = cust_dict[cid]
            is_f = int(fraud_mask[i])
            f_type = assigned_fraud_types[i]
            ts = dt_base[i].strftime("%Y-%m-%dT%H:%M:%SZ")
            tx_id = f"t-{uuid.uuid4().hex[:8]}"

            # Device selection
            known_devices = cust_device_map[cid]
            if is_f and f_type == "new_device_high_amount":
                dev_id = f"d-{uuid.uuid4().hex[:8]}"  # Unseen device
            else:
                dev_id = known_devices[0] if len(known_devices) == 1 else np.random.choice(known_devices)

            # Amount logic
            # Normal amount matches customer's average daily spend with log-normal noise
            base_exp = np.log(max(15.0, c_meta["avg_monthly_spend"] / 25.0))
            if is_f:
                if f_type in ["new_device_high_amount", "account_takeover"]:
                    amount = float(np.round(np.random.lognormal(mean=base_exp + 2.5, sigma=0.6), 2))
                elif f_type == "velocity_burst":
                    amount = float(np.round(np.random.lognormal(mean=base_exp + 1.2, sigma=0.4), 2))
                else:
                    amount = float(np.round(np.random.lognormal(mean=base_exp + 1.8, sigma=0.5), 2))
            else:
                amount = float(np.round(np.random.lognormal(mean=base_exp, sigma=0.7), 2))
            amount = max(1.0, min(amount, 99999.0))

            category = np.random.choice(categories, p=[0.30, 0.25, 0.10, 0.12, 0.08, 0.10, 0.05])
            channel = "mobile" if is_f and f_type == "account_takeover" else np.random.choice(channels, p=[0.55, 0.30, 0.15])

            tx_rows.append({
                "transaction_id": tx_id,
                "customer_id": cid,
                "source_account": f"acc-{uuid.uuid4().hex[:8]}",
                "destination_account": f"acc-{uuid.uuid4().hex[:8]}",
                "amount": amount,
                "currency": "EUR",
                "merchant_category": category,
                "channel": channel,
                "device_id": dev_id,
                "event_timestamp": ts,
                "is_fraud": is_f,
                "fraud_type": f_type
            })

            # Location
            if is_f and f_type in ["impossible_travel", "foreign_country"]:
                loc_country = "RU" if c_meta["country"] != "RU" else "BR"
                loc_lat = round(c_meta["home_lat"] + np.random.uniform(25.0, 45.0), 4)
                loc_lon = round(c_meta["home_lon"] + np.random.uniform(30.0, 60.0), 4)
            else:
                loc_country = c_meta["country"]
                loc_lat = round(c_meta["home_lat"] + np.random.uniform(-0.1, 0.1), 4)
                loc_lon = round(c_meta["home_lon"] + np.random.uniform(-0.1, 0.1), 4)

            loc_rows.append({
                "transaction_id": tx_id,
                "customer_id": cid,
                "ip_address": f"{np.random.randint(11, 210)}.{np.random.randint(1, 254)}.{np.random.randint(1, 254)}.{np.random.randint(1, 254)}",
                "ip_country": loc_country,
                "gps": {"lat": loc_lat, "lon": loc_lon},
                "event_timestamp": ts
            })

            # Access Log (Account Takeover or background random)
            if (is_f and f_type == "account_takeover") or (np.random.rand() < 0.08):
                is_failed = True if (is_f and f_type == "account_takeover") else (np.random.rand() < 0.03)
                access_log_rows.append({
                    "event_id": f"e-{uuid.uuid4().hex[:8]}",
                    "customer_id": cid,
                    "event_type": "login_failed" if is_failed else "login_success",
                    "event_timestamp": ts,
                    "device_id": dev_id,
                    "ip_address": f"{np.random.randint(11, 210)}.{np.random.randint(1, 254)}.{np.random.randint(1, 254)}.{np.random.randint(1, 254)}",
                    "user_agent": "Mozilla/5.0 (Enterprise Client)",
                    "geo": {"country": loc_country, "city": c_meta["home_city"]}
                })

            # Previous alerts (only from historical frauds)
            if not is_stream_batch and is_f and np.random.rand() < 0.65:
                alert_rows.append({
                    "alert_id": f"a-{uuid.uuid4().hex[:8]}",
                    "customer_id": cid,
                    "transaction_id": tx_id,
                    "alert_timestamp": ts,
                    "alert_type": "anomaly_pattern" if f_type != "account_takeover" else "high_risk_takeover",
                    "resolution": "confirmed"
                })

        df_out_tx = pd.DataFrame(tx_rows).sort_values("event_timestamp").reset_index(drop=True)
        return df_out_tx, loc_rows, access_log_rows, alert_rows

    logger.info("Generating historical transactions partition...")
    df_hist, hist_locs, hist_logs, alert_records = generate_partition(n_hist, history_start, history_end, is_stream_batch=False)
    
    logger.info("Generating stream transactions partition...")
    df_stream, stream_locs, stream_logs, _ = generate_partition(n_stream, stream_start, stream_end, is_stream_batch=True)

    # Save transaction history (Parquet) & streaming transactions (CSV)
    df_hist.to_parquet(f"{raw_path}/transaction_history.parquet", index=False)
    df_stream.to_csv(f"{raw_path}/transactions.csv", index=False)
    logger.info(f"Saved {len(df_hist)} rows to {raw_path}/transaction_history.parquet")
    logger.info(f"Saved {len(df_stream)} rows to {raw_path}/transactions.csv")

    # Combine locations
    all_locs = hist_locs + stream_locs
    with open(f"{raw_path}/user_location.json", "w") as f:
        json.dump(all_locs, f)
    logger.info(f"Saved {len(all_locs)} user locations to {raw_path}/user_location.json")

    # Combine access logs
    all_logs = hist_logs + stream_logs
    with open(f"{raw_path}/access_logs.jsonl", "w") as f:
        for log in all_logs:
            f.write(json.dumps(log) + "\n")
    logger.info(f"Saved {len(all_logs)} access logs to {raw_path}/access_logs.jsonl")

    # Save previous alerts
    df_alerts = pd.DataFrame(alert_records)
    df_alerts.to_csv(f"{raw_path}/previous_fraud_alerts.csv", index=False)
    logger.info(f"Saved {len(df_alerts)} previous fraud alerts to {raw_path}/previous_fraud_alerts.csv")

    logger.info("Enterprise synthetic generation successfully completed!")

if __name__ == "__main__":
    generate_all()
