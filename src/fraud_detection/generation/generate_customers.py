import pandas as pd
import numpy as np
from faker import Faker
from typing import List, Dict, Tuple
from src.fraud_detection.config import CONFIG, logger

# Curated reference cities for realistic geographic distance calculations
CITIES = [
    {"city": "Madrid", "country": "ES", "lat": 40.4168, "lon": -3.7038},
    {"city": "Barcelona", "country": "ES", "lat": 41.3851, "lon": 2.1734},
    {"city": "Valencia", "country": "ES", "lat": 39.4699, "lon": -0.3763},
    {"city": "Seville", "country": "ES", "lat": 37.3891, "lon": -5.9845},
    {"city": "Bilbao", "country": "ES", "lat": 43.2630, "lon": -2.9350},
    {"city": "Paris", "country": "FR", "lat": 48.8566, "lon": 2.3522},
    {"city": "Lyon", "country": "FR", "lat": 45.7640, "lon": 4.8357},
    {"city": "Rome", "country": "IT", "lat": 41.9028, "lon": 12.4964},
    {"city": "Milan", "country": "IT", "lat": 45.4642, "lon": 9.1900},
    {"city": "Berlin", "country": "DE", "lat": 52.5200, "lon": 13.4050},
    {"city": "Frankfurt", "country": "DE", "lat": 50.1109, "lon": 8.6821},
    {"city": "Amsterdam", "country": "NL", "lat": 52.3676, "lon": 4.9041},
    {"city": "London", "country": "GB", "lat": 51.5074, "lon": -0.1278},
    {"city": "Lisbon", "country": "PT", "lat": 38.7223, "lon": -9.1393},
    {"city": "Porto", "country": "PT", "lat": 41.1579, "lon": -8.6291},
]

def generate_customers(n_customers: int, seed: int = 42) -> Tuple[pd.DataFrame, List[Dict]]:
    Faker.seed(seed)
    np.random.seed(seed)
    fake = Faker()

    customers = []
    for i in range(n_customers):
        city_info = CITIES[np.random.choice(len(CITIES))]
        # Add slight jitter to home coordinates (within ~2km)
        lat_jitter = float(city_info["lat"] + np.random.uniform(-0.02, 0.02))
        lon_jitter = float(city_info["lon"] + np.random.uniform(-0.02, 0.02))

        risk_level = np.random.choice(["low", "medium", "high"], p=[0.75, 0.20, 0.05])
        avg_monthly_spend = float(np.round(np.random.lognormal(mean=6.5, sigma=0.6), 2))
        account_open_date = fake.date_between(start_date="-5y", end_date="-6m").isoformat()

        customers.append({
            "customer_id": f"c-{100000 + i}",
            "age": int(np.random.randint(18, 80)),
            "country": city_info["country"],
            "home_city": city_info["city"],
            "home_lat": round(lat_jitter, 5),
            "home_lon": round(lon_jitter, 5),
            "risk_level": risk_level,
            "account_open_date": account_open_date,
            "avg_monthly_spend": avg_monthly_spend
        })

    df_cust = pd.DataFrame(customers)
    return df_cust, customers
