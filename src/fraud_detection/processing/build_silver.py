import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, abs
from src.fraud_detection.config import CONFIG, logger

def run_build_silver():
    logger.info("Starting Silver layer processing...")
    spark = SparkSession.builder \
        .appName("BankFraud_BuildSilver") \
        .master("local[*]") \
        .getOrCreate()
        
    bronze_path = CONFIG["paths"]["bronze"]
    silver_path = CONFIG["paths"]["silver"]
    
    # 1. Clean Customers
    if os.path.exists(f"{bronze_path}/customer_profile"):
        logger.info("Cleaning customer profiles...")
        df_cust = spark.read.parquet(f"{bronze_path}/customer_profile")
        df_cust = df_cust.dropDuplicates(["customer_id"])
        df_cust.write.mode("overwrite").parquet(f"{silver_path}/customer_profile")
    
    # 2. Clean Devices
    if os.path.exists(f"{bronze_path}/device_data"):
        logger.info("Cleaning device data...")
        df_dev = spark.read.parquet(f"{bronze_path}/device_data")
        df_dev = df_dev.dropDuplicates(["device_id"])
        df_dev.write.mode("overwrite").parquet(f"{silver_path}/device_data")
    
    # 3. Clean Transactions
    logger.info("Cleaning transactions...")
    df_all_tx = None
    if os.path.exists(f"{bronze_path}/transaction_history"):
        df_hist = spark.read.parquet(f"{bronze_path}/transaction_history")
        df_all_tx = df_hist
        
    if os.path.exists(f"{bronze_path}/transactions"):
        df_tx = spark.read.parquet(f"{bronze_path}/transactions")
        if df_all_tx is not None:
            df_all_tx = df_all_tx.unionByName(df_tx, allowMissingColumns=True)
        else:
            df_all_tx = df_tx
            
    if df_all_tx is not None:
        df_all_tx = df_all_tx.dropDuplicates(["transaction_id"])
        df_all_tx = df_all_tx.withColumn("amount", abs(col("amount")))
        df_all_tx = df_all_tx.na.drop(subset=["customer_id", "amount", "event_timestamp"])
        
        # Run Data Quality Checks
        from src.fraud_detection.processing.quality_checks import run_all_checks
        if not run_all_checks(df_all_tx):
            logger.warning("Data quality checks failed for Silver transactions!")
        else:
            logger.info("All data quality checks passed for Silver transactions.")
            
        silver_tx_target = f"{silver_path}/transactions"
        import shutil
        if os.path.exists(silver_tx_target):
            shutil.rmtree(silver_tx_target, ignore_errors=True)
        df_all_tx.write.mode("overwrite").parquet(silver_tx_target)
    
    # 4. Clean User Location
    if os.path.exists(f"{bronze_path}/user_location"):
        logger.info("Processing user location into Silver...")
        df_loc = spark.read.parquet(f"{bronze_path}/user_location")
        df_loc = df_loc.dropDuplicates(["transaction_id"])
        df_loc.write.mode("overwrite").parquet(f"{silver_path}/user_location")

    # 5. Clean Access Logs
    if os.path.exists(f"{bronze_path}/access_logs"):
        logger.info("Processing access logs into Silver...")
        df_logs = spark.read.parquet(f"{bronze_path}/access_logs")
        df_logs = df_logs.dropDuplicates(["event_id"])
        df_logs.write.mode("overwrite").parquet(f"{silver_path}/access_logs")

    # 6. Previous Alerts
    if os.path.exists(f"{bronze_path}/previous_fraud_alerts"):
        logger.info("Processing previous fraud alerts into Silver...")
        df_alt = spark.read.parquet(f"{bronze_path}/previous_fraud_alerts")
        df_alt = df_alt.dropDuplicates(["alert_id"])
        df_alt.write.mode("overwrite").parquet(f"{silver_path}/previous_fraud_alerts")

    logger.info("Silver layer build completed.")
    spark.stop()

if __name__ == "__main__":
    run_build_silver()
