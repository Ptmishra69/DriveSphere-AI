# project_root/webhook/python/service_center_slots_loader.py

import json
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

SLOTS_FILE = os.path.join(DATA_DIR, "service_center_slots.json")


def load_service_centers():
    if not os.path.exists(SLOTS_FILE):
        raise FileNotFoundError(f"{SLOTS_FILE} not found")

    with open(SLOTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_service_center(city: str = None):
    """
    Pick a service center by city if possible,
    else pick any random center.
    """
    centers = load_service_centers()

    if city:
        filtered = {
            key: val for key, val in centers.items()
            if val.get("city", "").lower() == city.lower()
        }
        if filtered:
            return random.choice(list(filtered.items()))

    return random.choice(list(centers.items()))
