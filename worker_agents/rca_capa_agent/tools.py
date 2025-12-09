# tools.py

import json
import os
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history,
    load_capa_rca_docs
)


def get_vehicle_profile_tool(vehicle_id: str):
    return load_vehicle_profile(vehicle_id)


def get_maintenance_history_tool(vehicle_id: str):
    return load_maintenance_history(vehicle_id)


def load_capa_rca_docs():
    """
    Reads local CAPA/RCA pattern data.
    Should exist at shared/data/capa_rca_docs.json
    Format: list of { "content": "...", "metadata": {...} }
    """
    path = "./shared/data/capa_rca_docs.json"

    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        return json.load(f)
