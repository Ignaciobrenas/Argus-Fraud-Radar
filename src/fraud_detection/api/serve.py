from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os
from src.fraud_detection.config import logger

app = FastAPI(
    title="ARGUS Fraud Radar Inference API",
    version="1.0.0",
    description="Real-time banking fraud inference microservice with sub-millisecond scoring."
)

# Load model at startup
MODEL_PATH = "models/lgbm_model.pkl"
clf = None

if os.path.exists(MODEL_PATH):
    clf = joblib.load(MODEL_PATH)
    logger.info("Loaded LightGBM model for API inference.")
else:
    logger.warning("Model not found at startup. API will return 503 until model is trained.")

class TransactionInput(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    amount_zscore_customer: float = 0.0
    amount_to_avg_spend_ratio: float = 1.0
    distance_from_home_km: float = 0.0
    geo_distance_ip_gps_km: float = 0.0
    travel_speed_kmh: float = 0.0
    txn_count_10min: int = 1
    txn_count_1h: int = 1
    amount_sum_1h: float = 0.0
    is_new_device: int = 0
    is_foreign_country: int = 0
    failed_logins_before_txn: int = 0
    hour_of_day: int = 12
    is_weekend: int = 0
    is_night: int = 0
    customer_risk_level: int = 0
    previous_alerts_count: int = 0
    age: int = 35
    avg_monthly_spend: float = 800.0

class FraudPredictionResponse(BaseModel):
    transaction_id: str
    is_alert: bool
    fraud_score: float

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": clf is not None}

@app.post("/predict", response_model=FraudPredictionResponse)
def predict_fraud(transaction: TransactionInput):
    if clf is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    # Extract features in the exact order expected by the model
    from src.fraud_detection.models.train import MODEL_FEATURES
    row_data = [getattr(transaction, feat, 0.0) for feat in MODEL_FEATURES]
    df_features = pd.DataFrame([row_data], columns=MODEL_FEATURES)
    
    import json
    optimal_thresh = 0.50
    if os.path.exists("models/optimal_threshold.json"):
        try:
            with open("models/optimal_threshold.json", "r") as f:
                optimal_thresh = float(json.load(f).get("optimal_threshold", 0.50))
        except Exception:
            pass

    score = float(clf.predict_proba(df_features)[0, 1])
    is_alert = bool(score >= optimal_thresh)
    
    logger.info(f"Scored transaction {transaction.transaction_id}: {score:.4f} (Alert: {is_alert})")
    
    return FraudPredictionResponse(
        transaction_id=transaction.transaction_id,
        is_alert=is_alert,
        fraud_score=score
    )
