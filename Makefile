.PHONY: setup generate bronze silver gold train test all

setup:
	python -m pip install -r requirements.txt
	python -m pytest tests/

generate:
	python -m src.fraud_detection.generation.run_generation

bronze:
	python -m src.fraud_detection.ingestion.batch_ingest

silver:
	python -m src.fraud_detection.processing.build_silver

gold:
	python -m src.fraud_detection.features.build_gold

train:
	python -m src.fraud_detection.models.train

test:
	python -m pytest tests/ -v

stream:
	python -m src.fraud_detection.streaming.consumer

api:
	uvicorn src.fraud_detection.api.serve:app --host 0.0.0.0 --port 8000

kpi:
	python -m src.fraud_detection.analysis.scenarios

dashboard:
	streamlit run src/fraud_detection/dashboard/app.py

run:
	python main.py

all: generate bronze silver gold train stream kpi test


