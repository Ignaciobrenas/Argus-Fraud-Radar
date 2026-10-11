import sys
from src.fraud_detection.config import logger
from src.fraud_detection.generation.run_generation import generate_all
from src.fraud_detection.ingestion.batch_ingest import run_batch_ingest
from src.fraud_detection.ingestion.stream_ingest import run_stream_ingest
from src.fraud_detection.processing.build_silver import run_build_silver
from src.fraud_detection.features.build_gold import run_build_gold
from src.fraud_detection.models.train import run_train
from src.fraud_detection.streaming.consumer import run_consumer
from src.fraud_detection.analysis.scenarios import analyze_scenarios

def main():
    logger.info("Starting End-to-End Bank Fraud Detection Pipeline")
    try:
        generate_all()
        run_batch_ingest()
        run_stream_ingest()
        run_build_silver()
        run_build_gold()
        run_train()
        run_consumer()
        analyze_scenarios()
        logger.info("Pipeline executed successfully end-to-end!")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
