import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from typing import List, Dict, Tuple

FAR_AWAY_LOCATIONS = [
    {"city": "Tokyo", "country": "JP", "lat": 35.6762, "lon": 139.6503},
    {"city": "New York", "country": "US", "lat": 40.7128, "lon": -74.0060},
    {"city": "Sydney", "country": "AU", "lat": -33.8688, "lon": 151.2093},
    {"city": "Moscow", "country": "RU", "lat": 55.7558, "lon": 37.6173},
    {"city": "Sao Paulo", "country": "BR", "lat": -23.5505, "lon": -46.6333},
]

FOREIGN_COUNTRIES = ["RU", "CN", "NG", "BR", "IN", "TR", "SG", "US"]
CHANNELS = ["mobile", "pos", "web", "atm"]
MERCHANT_CATEGORIES = ["grocery", "retail", "travel", "electronics", "entertainment", "restaurant", "utilities"]

def generate_transactions_and_events(
    customers: List[Dict],
    devices: List[Dict],
    start_date: str,
    end_date: str,
    n_transactions: int,
    fraud_rate: float = 0.015,
    seed: int = 42,
    start_tx_id: int = 1000000
) -> Tuple[pd.DataFrame, List[Dict], List[Dict]]:
    Faker.seed(seed)
    np.random.seed(seed)
    fake = Faker()

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    total_seconds = int((end_dt - start_dt).total_seconds())

    # Map customer to their registered devices
    cust_dev_map = {}
    for d in devices:
        cust_dev_map.setdefault(d["customer_id"], []).append(d)

    cust_map = {c["customer_id"]: c for c in customers}

    transactions = []
    locations = []
    access_logs = []

    fraud_target_count = int(n_transactions * fraud_rate)
    fraud_patterns = [
        "impossible_travel",
        "new_device_high_amount",
        "velocity_burst",
        "account_takeover",
        "foreign_country",
        "atm_nocturnal_drain",
        "phishing_mule_transfer",
        "hard_subtle_fraud"
    ]

    tx_id_counter = start_tx_id
    log_id_counter = 100000

    # Pre-select transaction indices that will be fraud
    fraud_indices = set(np.random.choice(n_transactions, size=fraud_target_count, replace=False))

    i = 0
    while i < n_transactions:
        cust = customers[np.random.randint(len(customers))]
        cust_id = cust["customer_id"]
        c_devices = cust_dev_map.get(cust_id, [])
        reg_dev = c_devices[0] if c_devices else {"device_id": f"d-{fake.uuid4()[:8]}", "is_rooted": False}

        # Diurnal time generation (more transactions during daytime)
        random_sec = int(np.random.uniform(0, total_seconds))
        base_time = start_dt + timedelta(seconds=random_sec)
        # Hour adjustment to simulate daytime peaks
        raw_hour_probs = np.array([
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02, # 00-05
            0.03, 0.05, 0.07, 0.08, 0.08, 0.07, # 06-11
            0.08, 0.08, 0.06, 0.06, 0.07, 0.08, # 12-17
            0.07, 0.05, 0.03, 0.02, 0.01, 0.01  # 18-23
        ], dtype=float)
        hour_probs = raw_hour_probs / raw_hour_probs.sum()
        hour_prob = np.random.choice(24, p=hour_probs)
        base_time = base_time.replace(hour=hour_prob, minute=np.random.randint(0, 60), second=np.random.randint(0, 60))

        # Check if this index is chosen for fraud
        is_fraud = 1 if i in fraud_indices else 0
        fraud_type = np.random.choice(fraud_patterns) if is_fraud else ""

        if not is_fraud:
            # NORMAL TRANSACTION
            mean_spend_daily = max(cust["avg_monthly_spend"] / 30.0, 10.0)
            amount = float(np.round(np.random.lognormal(mean=np.log(mean_spend_daily), sigma=0.55), 2))
            amount = max(1.5, amount)

            chosen_dev = c_devices[np.random.choice(len(c_devices))] if c_devices else reg_dev
            channel = np.random.choice(CHANNELS, p=[0.55, 0.25, 0.15, 0.05])
            ts_str = base_time.isoformat() + "Z"
            txn_id = f"tx-{tx_id_counter}"
            tx_id_counter += 1

            transactions.append({
                "transaction_id": txn_id,
                "customer_id": cust_id,
                "source_account": f"acc-{cust_id[2:]}",
                "destination_account": f"acc-{fake.uuid4()[:8]}",
                "amount": amount,
                "currency": "EUR",
                "merchant_category": np.random.choice(MERCHANT_CATEGORIES),
                "channel": channel,
                "device_id": chosen_dev["device_id"],
                "event_timestamp": ts_str,
                "is_fraud": 0,
                "fraud_type": ""
            })

            # Normal location: near customer home city
            loc_lat = float(cust["home_lat"] + np.random.uniform(-0.05, 0.05))
            loc_lon = float(cust["home_lon"] + np.random.uniform(-0.05, 0.05))
            locations.append({
                "transaction_id": txn_id,
                "customer_id": cust_id,
                "ip_address": fake.ipv4(),
                "ip_country": cust["country"],
                "gps": {"lat": round(loc_lat, 5), "lon": round(loc_lon, 5)},
                "event_timestamp": ts_str
            })

            # Normal access log
            if np.random.rand() < 0.20:
                access_logs.append({
                    "event_id": f"e-{log_id_counter}",
                    "customer_id": cust_id,
                    "event_type": "login_success",
                    "event_timestamp": (base_time - timedelta(minutes=np.random.randint(1, 15))).isoformat() + "Z",
                    "device_id": chosen_dev["device_id"],
                    "ip_address": fake.ipv4(),
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "geo": {"country": cust["country"], "city": cust["home_city"]}
                })
                log_id_counter += 1

            i += 1

        else:
            # FRAUD TRANSACTION USE CASES
            if fraud_type == "impossible_travel":
                # Transaction 1: Home country
                t1_time = base_time
                txn_id_1 = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id_1,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": float(np.round(np.random.uniform(25, 80), 2)),
                    "currency": "EUR",
                    "merchant_category": "restaurant",
                    "channel": "pos",
                    "device_id": reg_dev["device_id"],
                    "event_timestamp": t1_time.isoformat() + "Z",
                    "is_fraud": 0,
                    "fraud_type": ""
                })
                locations.append({
                    "transaction_id": txn_id_1,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": cust["country"],
                    "gps": {"lat": float(cust["home_lat"]), "lon": float(cust["home_lon"])},
                    "event_timestamp": t1_time.isoformat() + "Z"
                })

                # Transaction 2: 25 minutes later in Tokyo/NYC/Moscow!
                t2_time = t1_time + timedelta(minutes=np.random.randint(15, 35))
                far_loc = FAR_AWAY_LOCATIONS[np.random.choice(len(FAR_AWAY_LOCATIONS))]
                txn_id_2 = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id_2,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": float(np.round(np.random.uniform(850, 2900), 2)),
                    "currency": "EUR",
                    "merchant_category": "electronics",
                    "channel": "web",
                    "device_id": f"d-new-{fake.uuid4()[:6]}",
                    "event_timestamp": t2_time.isoformat() + "Z",
                    "is_fraud": 1,
                    "fraud_type": "impossible_travel"
                })
                locations.append({
                    "transaction_id": txn_id_2,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": far_loc["country"],
                    "gps": {"lat": float(far_loc["lat"]), "lon": float(far_loc["lon"])},
                    "event_timestamp": t2_time.isoformat() + "Z"
                })
                i += 2

            elif fraud_type == "new_device_high_amount":
                # Unregistered device with huge amount
                new_dev_id = f"d-rogue-{fake.uuid4()[:6]}"
                amount = float(np.round(cust["avg_monthly_spend"] * np.random.uniform(3.5, 9.0), 2))
                ts_str = base_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1

                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": amount,
                    "currency": "EUR",
                    "merchant_category": "electronics",
                    "channel": "web",
                    "device_id": new_dev_id,
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "new_device_high_amount"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": cust["country"],
                    "gps": {"lat": float(cust["home_lat"] + 0.1), "lon": float(cust["home_lon"] + 0.1)},
                    "event_timestamp": ts_str
                })
                i += 1

            elif fraud_type == "velocity_burst":
                # Rapid succession of 4-6 transactions in 5 minutes
                burst_len = np.random.randint(4, 7)
                burst_start = base_time
                for b in range(burst_len):
                    b_time = burst_start + timedelta(seconds=int(b * np.random.uniform(30, 80)))
                    txn_id_b = f"tx-{tx_id_counter}"
                    tx_id_counter += 1
                    transactions.append({
                        "transaction_id": txn_id_b,
                        "customer_id": cust_id,
                        "source_account": f"acc-{cust_id[2:]}",
                        "destination_account": f"acc-{fake.uuid4()[:8]}",
                        "amount": float(np.round(np.random.uniform(190, 480), 2)),
                        "currency": "EUR",
                        "merchant_category": "retail",
                        "channel": "web",
                        "device_id": reg_dev["device_id"],
                        "event_timestamp": b_time.isoformat() + "Z",
                        "is_fraud": 1,
                        "fraud_type": "velocity_burst"
                    })
                    locations.append({
                        "transaction_id": txn_id_b,
                        "customer_id": cust_id,
                        "ip_address": fake.ipv4(),
                        "ip_country": cust["country"],
                        "gps": {"lat": float(cust["home_lat"]), "lon": float(cust["home_lon"])},
                        "event_timestamp": b_time.isoformat() + "Z"
                    })
                i += burst_len

            elif fraud_type == "account_takeover":
                # Injected access logs: 4 failed logins followed by success from new device
                ato_dev_id = f"d-ato-{fake.uuid4()[:6]}"
                foreign_ip = fake.ipv4()
                for f_idx in range(4):
                    fail_time = base_time - timedelta(minutes=int(25 - f_idx * 4))
                    access_logs.append({
                        "event_id": f"e-{log_id_counter}",
                        "customer_id": cust_id,
                        "event_type": "login_failed",
                        "event_timestamp": fail_time.isoformat() + "Z",
                        "device_id": ato_dev_id,
                        "ip_address": foreign_ip,
                        "user_agent": "Python-requests/2.28.1",
                        "geo": {"country": "RU", "city": "Moscow"}
                    })
                    log_id_counter += 1

                # 1 success
                succ_time = base_time - timedelta(minutes=2)
                access_logs.append({
                    "event_id": f"e-{log_id_counter}",
                    "customer_id": cust_id,
                    "event_type": "login_success",
                    "event_timestamp": succ_time.isoformat() + "Z",
                    "device_id": ato_dev_id,
                    "ip_address": foreign_ip,
                    "user_agent": "Python-requests/2.28.1",
                    "geo": {"country": "RU", "city": "Moscow"}
                })
                log_id_counter += 1

                # Immediate large transaction
                ts_str = base_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-mule-{fake.uuid4()[:6]}",
                    "amount": float(np.round(np.random.uniform(3500, 8500), 2)),
                    "currency": "EUR",
                    "merchant_category": "utilities",
                    "channel": "web",
                    "device_id": ato_dev_id,
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "account_takeover"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": foreign_ip,
                    "ip_country": "RU",
                    "gps": {"lat": 55.7558, "lon": 37.6173},
                    "event_timestamp": ts_str
                })
                i += 1

            elif fraud_type == "foreign_country":
                # Foreign IP and country completely disjoint from home country
                foreign_c = np.random.choice([c for c in FOREIGN_COUNTRIES if c != cust["country"]])
                ts_str = base_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": float(np.round(np.random.uniform(400, 2200), 2)),
                    "currency": "EUR",
                    "merchant_category": "travel",
                    "channel": "web",
                    "device_id": reg_dev["device_id"],
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "foreign_country"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": foreign_c,
                    "gps": {"lat": float(fake.latitude()), "lon": float(fake.longitude())},
                    "event_timestamp": ts_str
                })
                i += 1

            elif fraud_type == "atm_nocturnal_drain":
                # Night drain (02:00 - 04:30)
                night_time = base_time.replace(hour=np.random.choice([2, 3, 4]), minute=np.random.randint(0, 59))
                ts_str = night_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": float(np.round(np.random.uniform(950, 1800), 2)),
                    "currency": "EUR",
                    "merchant_category": "retail",
                    "channel": "atm",
                    "device_id": f"atm-{fake.uuid4()[:6]}",
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "atm_nocturnal_drain"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": cust["country"],
                    "gps": {"lat": float(cust["home_lat"] + 0.02), "lon": float(cust["home_lon"] + 0.02)},
                    "event_timestamp": ts_str
                })
                i += 1

            elif fraud_type == "phishing_mule_transfer":
                # Large online transfer to mule account
                ts_str = base_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-mule-{fake.uuid4()[:6]}",
                    "amount": float(np.round(np.random.uniform(2800, 7200), 2)),
                    "currency": "EUR",
                    "merchant_category": "utilities",
                    "channel": "web",
                    "device_id": f"d-web-{fake.uuid4()[:6]}",
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "phishing_mule_transfer"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": cust["country"],
                    "gps": {"lat": float(cust["home_lat"]), "lon": float(cust["home_lon"])},
                    "event_timestamp": ts_str
                })
                i += 1

            elif fraud_type == "hard_subtle_fraud":
                # Hard subtle case: moderate amount (e.g. 150-320 EUR), normal mobile channel,
                # but subtle indicators: brand new device, slightly unusual evening time, slight velocity
                ts_str = base_time.isoformat() + "Z"
                txn_id = f"tx-{tx_id_counter}"
                tx_id_counter += 1
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "source_account": f"acc-{cust_id[2:]}",
                    "destination_account": f"acc-{fake.uuid4()[:8]}",
                    "amount": float(np.round(np.random.uniform(160, 340), 2)),
                    "currency": "EUR",
                    "merchant_category": "retail",
                    "channel": "mobile",
                    "device_id": f"d-subtle-{fake.uuid4()[:6]}",
                    "event_timestamp": ts_str,
                    "is_fraud": 1,
                    "fraud_type": "hard_subtle_fraud"
                })
                locations.append({
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "ip_address": fake.ipv4(),
                    "ip_country": cust["country"],
                    "gps": {"lat": float(cust["home_lat"] + 0.04), "lon": float(cust["home_lon"] + 0.04)},
                    "event_timestamp": ts_str
                })
                i += 1

    df_tx = pd.DataFrame(transactions)
    df_tx = df_tx.sort_values("event_timestamp").reset_index(drop=True)
    return df_tx, locations, access_logs
