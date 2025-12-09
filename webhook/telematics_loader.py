# project_root/webhook/python/telematics_loader.py

import json
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

TELEMETRICS_FILE = os.path.join(DATA_DIR, "live_telematics_feed.json")
VEHICLE_PROFILES = os.path.join(DATA_DIR, "vehicle_profiles.json")


def load_telematics():
    if not os.path.exists(TELEMETRICS_FILE):
        raise FileNotFoundError(f"{TELEMETRICS_FILE} not found")

    with open(TELEMETRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_vehicle_profiles():
    if not os.path.exists(VEHICLE_PROFILES):
        raise FileNotFoundError(f"{VEHICLE_PROFILES} not found")

    with open(VEHICLE_PROFILES, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_vehicle():
    """
    Picks a random vehicle from live_telematics_feed.json.
    Returns vehicle_id + city (from vehicle profile).
    """
    live_data = load_telematics()
    profiles = load_vehicle_profiles()

    if isinstance(live_data, dict):
        live_data = [live_data]

    random_entry = random.choice(live_data)
    vid = random_entry["vehicle_id"]

    # Match vehicle profile for city
    profile = next((p for p in profiles if p["vehicle_id"] == vid), None)

    city = profile.get("city") if profile else None

    return vid, city
