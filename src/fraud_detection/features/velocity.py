import pandas as pd
import numpy as np

def compute_rolling_velocity(df_tx: pd.DataFrame) -> pd.DataFrame:
    """
    Computes time-based rolling transaction counts and spending amounts per customer.
    STRICTLY avoids data leakage by computing rolling metrics on past events only.
    Expects df_tx sorted by event_timestamp and customer_id.
    """
    df = df_tx.copy()
    df["dt"] = pd.to_datetime(df["event_timestamp"], utc=True)

    df = df.sort_values(["customer_id", "dt"]).reset_index(drop=True)

    # Use pandas rolling with time windows grouped by customer
    # Note: Closed on 'left' would exclude current txn; closed 'both' includes current txn.
    # We include current txn so txn_count_10min >= 1 always.
    df_indexed = df.set_index("dt")

    # Rolling 10 minutes count
    roll_10m = df_indexed.groupby("customer_id")["transaction_id"].rolling("10min", closed="both").count()
    df["txn_count_10min"] = roll_10m.values.astype(int)

    # Rolling 1 hour count
    roll_1h = df_indexed.groupby("customer_id")["transaction_id"].rolling("1h", closed="both").count()
    df["txn_count_1h"] = roll_1h.values.astype(int)

    # Rolling 1 hour amount sum
    roll_amt_1h = df_indexed.groupby("customer_id")["amount"].rolling("1h", closed="both").sum()
    df["amount_sum_1h"] = roll_amt_1h.values.astype(float)

    return df
