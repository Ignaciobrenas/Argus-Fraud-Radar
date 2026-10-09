import pytest
import pandas as pd
import numpy as np
from src.fraud_detection.features.geo import haversine_distance_km
from src.fraud_detection.features.velocity import compute_rolling_velocity
from src.fraud_detection.features.behavior import compute_behavior_features
from src.fraud_detection.models.baseline_rules import apply_baseline_rules

def test_haversine_distance_zero():
    # Distance between identical coordinates is 0
    dist = haversine_distance_km(40.4168, -3.7038, 40.4168, -3.7038)
    assert round(dist, 2) == 0.0

def test_haversine_distance_madrid_barcelona():
    # Madrid (40.4168, -3.7038) to Barcelona (41.3851, 2.1734) is approx 505 km
    dist = haversine_distance_km(40.4168, -3.7038, 41.3851, 2.1734)
    assert 490.0 < dist < 520.0

def test_rolling_velocity_count():
    df = pd.DataFrame({
        "transaction_id": ["tx-1", "tx-2", "tx-3"],
        "customer_id": ["c-1", "c-1", "c-1"],
        "amount": [50.0, 60.0, 70.0],
        "event_timestamp": [
            "2026-07-01T10:00:00Z",
            "2026-07-01T10:02:00Z",
            "2026-07-01T10:15:00Z"
        ]
    })
    res = compute_rolling_velocity(df)
    # tx-1 (1 in 10m), tx-2 (2 in 10m: tx-1 & tx-2), tx-3 (1 in 10m: 13 min later)
    assert res.iloc[0]["txn_count_10min"] == 1
    assert res.iloc[1]["txn_count_10min"] == 2
    assert res.iloc[2]["txn_count_10min"] == 1

def test_behavior_new_device():
    df_tx = pd.DataFrame({
        "transaction_id": ["tx-1", "tx-2"],
        "customer_id": ["c-1", "c-1"],
        "device_id": ["d-known", "d-rogue"],
        "amount": [100.0, 5000.0],
        "event_timestamp": ["2026-07-01T12:00:00Z", "2026-07-01T12:05:00Z"]
    })
    df_cust = pd.DataFrame([{
        "customer_id": "c-1",
        "country": "ES",
        "home_city": "Madrid",
        "home_lat": 40.41,
        "home_lon": -3.70,
        "risk_level": "low",
        "avg_monthly_spend": 1000.0,
        "age": 30
    }])
    devices_dict = {"c-1": {"d-known"}}

    res = compute_behavior_features(df_tx, df_cust, devices_dict)
    assert res.iloc[0]["is_new_device"] == 0
    assert res.iloc[1]["is_new_device"] == 1

def test_baseline_rules_detection():
    df = pd.DataFrame({
        "amount": [50.0, 6000.0, 100.0],
        "amount_zscore_customer": [0.1, 4.2, 0.5],
        "travel_speed_kmh": [20.0, 0.0, 1200.0],
        "geo_distance_ip_gps_km": [5.0, 10.0, 2000.0],
        "txn_count_10min": [1, 1, 1],
        "failed_logins_before_txn": [0, 0, 0],
        "is_new_device": [0, 1, 0],
        "is_foreign_country": [0, 0, 0]
    })
    alerts = apply_baseline_rules(df)
    assert alerts.iloc[0] == 0
    assert alerts.iloc[1] == 1 # High amount
    assert alerts.iloc[2] == 1 # Impossible travel
