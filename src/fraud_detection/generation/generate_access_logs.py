import json
from typing import List, Dict

def save_access_logs_jsonl(access_logs: List[Dict], filepath: str):
    """Saves access logs to JSON Lines format."""
    with open(filepath, "w", encoding="utf-8") as f:
        for log in access_logs:
            f.write(json.dumps(log) + "\n")
