# tools.py

from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history
)
import json
import os

FEEDBACK_LOG_PATH = "../data/feedback_records.json"


@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Return the vehicle profile for feedback personalization."""
    return load_vehicle_profile(vehicle_id)


@tool("get_past_feedback")
def get_past_feedback_tool(vehicle_id: str):
    """Return all past feedback records for a vehicle."""
    if not os.path.exists(FEEDBACK_LOG_PATH):
        return []

    with open(FEEDBACK_LOG_PATH, "r") as f:
        data = json.load(f)

    return [f for f in data if f.get("vehicle_id") == vehicle_id]


@tool("store_feedback")
def store_feedback_tool(feedback_json: str):
    """
    Store structured feedback into local JSON.
    (In production, replace with DB insert logic)
    """
    feedback = json.loads(feedback_json)

    existing = []
    if os.path.exists(FEEDBACK_LOG_PATH):
        with open(FEEDBACK_LOG_PATH, "r") as f:
            existing = json.load(f)

    existing.append(feedback)

    with open(FEEDBACK_LOG_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return {"status": "stored", "count": len(existing)}
