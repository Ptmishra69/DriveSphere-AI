# tools.py

from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history
)


@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Fetch full profile including risk index, climate zone, cost sensitivity."""
    return load_vehicle_profile(vehicle_id)


@tool("get_maintenance_history")
def get_maintenance_history_tool(vehicle_id: str):
    """Retrieve previous issues to detect recurring patterns."""
    return load_maintenance_history(vehicle_id)
