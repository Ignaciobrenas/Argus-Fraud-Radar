from pyspark.sql import DataFrame
from pyspark.sql.functions import col, abs, to_timestamp, when

def clean_transactions_df(df: DataFrame) -> DataFrame:
    """
    Cleans transactions:
    - Deduplicates by transaction_id
    - Drops null customer_id, amount, or timestamp
    - Ensures amount is positive
    - Casts event_timestamp to UTC timestamp
    """
    cleaned = df.dropDuplicates(["transaction_id"])
    cleaned = cleaned.na.drop(subset=["customer_id", "amount", "event_timestamp"])
    cleaned = cleaned.withColumn("amount", abs(col("amount")))
    cleaned = cleaned.filter(col("amount") > 0)
    cleaned = cleaned.withColumn("event_timestamp", to_timestamp(col("event_timestamp")))
    return cleaned

def clean_customers_df(df: DataFrame) -> DataFrame:
    """Cleans customer profile data and removes duplicate IDs."""
    return df.dropDuplicates(["customer_id"])

def clean_devices_df(df: DataFrame) -> DataFrame:
    """Cleans device data and removes duplicates."""
    return df.dropDuplicates(["device_id"])
