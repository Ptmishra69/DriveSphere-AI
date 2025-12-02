# tools.py

from langchain.tools import tool
from shared.shared_loader import load_vehicle_profile
import json
import os

SLOTS_FILE = "../data/service_center_slots.json"


@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Fetch profile to select nearest and appropriate service center."""
    return load_vehicle_profile(vehicle_id)


@tool("get_service_center_slots")
def get_service_center_slots_tool(city: str):
    """Load available slots for all centers in the given city."""
    if not os.path.exists(SLOTS_FILE):
        return {}

    with open(SLOTS_FILE, "r") as f:
        slots = json.load(f)

    # Filter centers by city name match
    city_centers = {
        name: info for name, info in slots.items()
        if city.lower() in info["location"].lower()
    }

    return city_centers
