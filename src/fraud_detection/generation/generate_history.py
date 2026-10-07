from src.fraud_detection.generation.generate_transactions import generate_transactions_and_events

def generate_history_data(customers, devices, start_date, end_date, n_transactions, fraud_rate, seed):
    """Generates historical batch transactions and events."""
    return generate_transactions_and_events(
        customers=customers,
        devices=devices,
        start_date=start_date,
        end_date=end_date,
        n_transactions=n_transactions,
        fraud_rate=fraud_rate,
        seed=seed,
        start_tx_id=1000000
    )
