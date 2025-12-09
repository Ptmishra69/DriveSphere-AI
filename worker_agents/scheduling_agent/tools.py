import json
import os
from shared.shared_loader import load_vehicle_profile as _load_vehicle_profile

SLOTS_FILE = "../data/service_center_slots.json"


def load_vehicle_profile(vehicle_id: str):
    """Offline loader for vehicle profile."""
    return _load_vehicle_profile(vehicle_id)


def load_service_center_slots(city: str):
    """Load service center slots from local JSON file."""
    if not os.path.exists(SLOTS_FILE):
        return {}

    with open(SLOTS_FILE, "r") as f:
        slots = json.load(f)

    # Case-insensitive filter
    city_centers = {
        name: info
        for name, info in slots.items()
        if city.lower() in info["location"].lower()
    }

    return city_centers
