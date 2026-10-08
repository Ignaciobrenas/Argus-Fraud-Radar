import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, col, to_date
from src.fraud_detection.config import CONFIG

def run_stream_ingest():
    spark = SparkSession.builder \
        .appName("BankFraud_StreamIngest_Bronze") \
        .master("local[*]") \
        .getOrCreate()
        
    raw_path = CONFIG["paths"]["raw"]
    bronze_path = CONFIG["paths"]["bronze"]
    
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # Simulate batching the "stream" files into Bronze
    
    # 1. Transactions (Stream)
    df_tx = spark.read.csv(f"{raw_path}/transactions.csv", header=True, inferSchema=True)
    df_tx = df_tx.withColumn("source_system", lit("core_banking_simulator")) \
                 .withColumn("ingestion_timestamp", lit(current_time)) \
                 .withColumn("schema_version", lit("1.0.0")) \
                 .withColumn("date", to_date(col("event_timestamp")))
    tx_target = f"{bronze_path}/transactions"
    import shutil
    if os.path.exists(tx_target):
        shutil.rmtree(tx_target, ignore_errors=True)
    df_tx.write.mode("overwrite").partitionBy("date").parquet(tx_target)
    
    # 2. Access Logs (JSONL)
    if os.path.exists(f"{raw_path}/access_logs.jsonl"):
        df_logs = spark.read.json(f"{raw_path}/access_logs.jsonl")
        df_logs = df_logs.withColumn("source_system", lit("core_banking_simulator")) \
                         .withColumn("ingestion_timestamp", lit(current_time)) \
                         .withColumn("schema_version", lit("1.0.0")) \
                         .withColumn("date", to_date(col("event_timestamp")))
        df_logs.write.mode("append").partitionBy("date").parquet(f"{bronze_path}/access_logs")
    
    # 3. User Location (JSON)
    if os.path.exists(f"{raw_path}/user_location.json"):
        df_loc = spark.read.option("multiLine", "true").json(f"{raw_path}/user_location.json")
        df_loc = df_loc.withColumn("source_system", lit("core_banking_simulator")) \
                       .withColumn("ingestion_timestamp", lit(current_time)) \
                       .withColumn("schema_version", lit("1.0.0")) \
                       .withColumn("date", to_date(col("event_timestamp")))
        df_loc.write.mode("append").partitionBy("date").parquet(f"{bronze_path}/user_location")

    print("Stream ingestion to Bronze completed.")
    spark.stop()

if __name__ == "__main__":
    run_stream_ingest()
