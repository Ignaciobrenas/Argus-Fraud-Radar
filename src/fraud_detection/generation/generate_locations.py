import json
from typing import List, Dict

def save_locations_json(locations: List[Dict], filepath: str):
    """Saves semi-structured user location events to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(locations, f, indent=2)
