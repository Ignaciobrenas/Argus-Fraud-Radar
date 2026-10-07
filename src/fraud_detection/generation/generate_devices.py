import pandas as pd
import numpy as np
from faker import Faker
from typing import List, Dict, Tuple

OS_LIST = ["Android 14", "iOS 17", "Windows 11", "macOS 14"]
BROWSER_LIST = ["Chrome", "Safari", "Firefox", "Edge"]
APP_VERSIONS = ["5.2.0", "5.2.1", "5.3.0"]

def generate_devices(customers: List[Dict], seed: int = 42) -> Tuple[pd.DataFrame, List[Dict]]:
    Faker.seed(seed)
    np.random.seed(seed)
    fake = Faker()

    devices = []
    dev_counter = 1
    for cust in customers:
        num_devices = np.random.choice([1, 2, 3], p=[0.60, 0.30, 0.10])
        for _ in range(num_devices):
            dev_type = np.random.choice(["mobile", "web"], p=[0.7, 0.3])
            os_name = np.random.choice(OS_LIST[:2]) if dev_type == "mobile" else np.random.choice(OS_LIST[2:])
            browser_name = np.random.choice(BROWSER_LIST)
            app_ver = np.random.choice(APP_VERSIONS) if dev_type == "mobile" else None
            # Rooted is very rare in normal devices (~1.5%)
            is_rooted = bool(np.random.rand() < 0.015) if dev_type == "mobile" else False

            first_seen = fake.date_time_between(start_date="-2y", end_date="-1m").isoformat() + "Z"

            devices.append({
                "device_id": f"d-{dev_counter:06d}",
                "customer_id": cust["customer_id"],
                "device_type": dev_type,
                "os": os_name,
                "browser": browser_name,
                "app_version": app_ver,
                "first_seen": first_seen,
                "is_rooted": is_rooted
            })
            dev_counter += 1

    df_devices = pd.DataFrame(devices)
    return df_devices, devices
