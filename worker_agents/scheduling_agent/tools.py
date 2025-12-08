# tools.py

import json
import os
from shared.shared_loader import load_vehicle_profile

SLOTS_FILE = "../data/service_center_slots.json"


def get_vehicle_profile_tool(vehicle_id: str):
    """Return vehicle profile."""
    return load_vehicle_profile(vehicle_id)


def get_service_center_slots_tool(city: str):
    """Return service centers in the city."""
    if not os.path.exists(SLOTS_FILE):
        return {}

    with open(SLOTS_FILE, "r") as f:
        slots = json.load(f)

    city_lower = city.lower()

    # match using "location" field
    city_centers = {
        name: info for name, info in slots.items()
        if city_lower in info["location"].lower()
    }

    return city_centers
