# tools.py

from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history,
    load_telematics
)


@tool("get_vehicle_profile")
def get_vehicle_profile(vehicle_id: str):
    """
    Returns detailed, normalized vehicle profile data.
    """
    return load_vehicle_profile(vehicle_id)


@tool("get_historical_usage")
def get_historical_usage(vehicle_id: str):
    """
    Returns past maintenance and usage patterns for the vehicle.
    """
    history = load_maintenance_history(vehicle_id)

    # Summaries to reduce LLM token load
    summary = {
        "total_records": len(history),
        "last_service_date": history[-1]["date"].isoformat() if history else None,
        "recurring_issues": [
            h["issue_reported"] for h in history if "recurring" in h["issue_reported"].lower()
        ],
        "declined_repairs": sum(1 for h in history if h.get("customer_declined_parts_replacement")),
    }

    return summary


@tool("get_telematics_snapshot")
def get_telematics_snapshot(vehicle_id: str):
    """
    Returns live telematics for real-time anomaly detection.
    """
    return load_telematics(vehicle_id)
