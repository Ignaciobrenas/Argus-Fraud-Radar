import os
import time
import pandas as pd
from typing import Generator
from src.fraud_detection.config import CONFIG, logger

def get_stream_microbatches(batch_size: int = 500) -> Generator[pd.DataFrame, None, None]:
    """
    Yields transactions from the streaming period ordered chronologically by event_timestamp.
    """
    raw_path = CONFIG["paths"]["raw"]
    tx_file = f"{raw_path}/transactions.csv"
    if not os.path.exists(tx_file):
        logger.error(f"Stream transactions file not found at {tx_file}")
        return

    df_stream = pd.read_csv(tx_file)
    df_stream = df_stream.sort_values("event_timestamp").reset_index(drop=True)
    logger.info(f"Producer loaded {len(df_stream)} stream transactions.")

    total = len(df_stream)
    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        yield df_stream.iloc[start_idx:end_idx].copy()
