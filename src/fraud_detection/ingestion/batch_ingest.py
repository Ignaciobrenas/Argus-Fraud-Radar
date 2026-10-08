import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, col, to_date
from src.fraud_detection.config import CONFIG, logger

def run_batch_ingest():
    logger.info("Starting batch ingestion to Bronze...")
    spark = SparkSession.builder \
        .appName("BankFraud_BatchIngest_Bronze") \
        .master("local[*]") \
        .getOrCreate()
        
    raw_path = CONFIG["paths"]["raw"]
    bronze_path = CONFIG["paths"]["bronze"]
    
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # 1. Customer Profile
    df_cust = spark.read.csv(f"{raw_path}/customer_profile.csv", header=True, inferSchema=True)
    df_cust = df_cust.withColumn("source_system", lit("core_banking_simulator")) \
                     .withColumn("ingestion_timestamp", lit(current_time)) \
                     .withColumn("schema_version", lit("1.0.0"))
    df_cust.write.mode("overwrite").parquet(f"{bronze_path}/customer_profile")
    
    # 2. Device Data
    df_dev = spark.read.option("multiLine", "true").json(f"{raw_path}/device_data.json")
    df_dev = df_dev.withColumn("source_system", lit("core_banking_simulator")) \
                   .withColumn("ingestion_timestamp", lit(current_time)) \
                   .withColumn("schema_version", lit("1.0.0"))
    df_dev.write.mode("overwrite").parquet(f"{bronze_path}/device_data")
    
    # 3. Transaction History
    df_hist = spark.read.parquet(f"{raw_path}/transaction_history.parquet")
    df_hist = df_hist.withColumn("source_system", lit("core_banking_simulator")) \
                     .withColumn("ingestion_timestamp", lit(current_time)) \
                     .withColumn("schema_version", lit("1.0.0")) \
                     .withColumn("date", to_date(col("event_timestamp")))
    hist_target = f"{bronze_path}/transaction_history"
    import shutil
    if os.path.exists(hist_target):
        shutil.rmtree(hist_target, ignore_errors=True)
    df_hist.write.mode("overwrite").partitionBy("date").parquet(hist_target)
    
    # 4. Previous Fraud Alerts
    if os.path.exists(f"{raw_path}/previous_fraud_alerts.csv"):
        df_alerts = spark.read.csv(f"{raw_path}/previous_fraud_alerts.csv", header=True, inferSchema=True)
        df_alerts = df_alerts.withColumn("source_system", lit("core_banking_simulator")) \
                             .withColumn("ingestion_timestamp", lit(current_time)) \
                             .withColumn("schema_version", lit("1.0.0"))
        df_alerts.write.mode("overwrite").parquet(f"{bronze_path}/previous_fraud_alerts")

    logger.info("Batch ingestion to Bronze completed.")
    spark.stop()

if __name__ == "__main__":
    run_batch_ingest()
