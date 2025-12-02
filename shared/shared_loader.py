import json
import os
from datetime import datetime
from typing import Dict, List, Any

from langchain_core.documents import Document
import pandas as pd


# ---------- Helper: Load JSON file safely ----------
def load_json(file_path: str) -> Any:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# ---------- 1. Load VEHICLE PROFILE ----------
def load_vehicle_profile(vehicle_id: str, base_path="../data/vehicle_profile.json") -> Dict:
    vehicles = load_json(base_path)

    # If it's a list of vehicles
    if isinstance(vehicles, list):
        vehicle = next((v for v in vehicles if v["vehicle_id"] == vehicle_id), None)
    else:
        # Single-object JSON (your sample)
        vehicle = vehicles if vehicles["vehicle_id"] == vehicle_id else None

    if vehicle is None:
        raise ValueError(f"Vehicle ID {vehicle_id} NOT FOUND in vehicle_profile.json")

    # Normalize missing values
    vehicle.setdefault("known_model_defect", "none")
    vehicle.setdefault("cost_sensitivity", False)

    # Enrichment: risk profile
    risk_index = _compute_vehicle_risk(vehicle)
    vehicle["risk_index"] = risk_index

    return vehicle



# ---------- Enrichment Logic ----------
def _compute_vehicle_risk(vehicle: Dict) -> float:
    # Simple weighted formula based on age, usage, climate
    age = datetime.now().year - int(vehicle["manufacturing_year"])
    usage = vehicle["avg_km_per_day"]
    climate_factor = 1.2 if vehicle["climate_zone"] == "Hot" else 1.0

    risk = (age * 0.3 + usage * 0.02) * climate_factor
    return round(min(risk, 1.0), 2)      # clamp between 0 - 1.0



# ---------- 2. Load MAINTENANCE HISTORY ----------
def load_maintenance_history(vehicle_id: str, base_path="../data/maintenance_history.json") -> List[Dict]:
    data = load_json(base_path)

    if isinstance(data, dict):  # if only one record
        data = [data]

    history = [h for h in data if h["vehicle_id"] == vehicle_id]

    # Convert dates
    for h in history:
        h["date"] = datetime.fromisoformat(h["date"])

        # Normalize missing fields
        h.setdefault("components_serviced", [])
        h.setdefault("parts_replaced", [])
        h.setdefault("warranty_applied", False)

    return history



# ---------- 3. Load LIVE TELEMATICS ----------
def load_telematics(vehicle_id: str, base_path="../data/live_telematics.json") -> Dict:
    data = load_json(base_path)

    # If file contains multiple records
    if isinstance(data, list):
        record = next((r for r in data if r["vehicle_id"] == vehicle_id), None)
    else:
        record = data if data["vehicle_id"] == vehicle_id else None

    if record is None:
        raise ValueError(f"No telematics data for vehicle {vehicle_id}")

    # Convert timestamp
    record["timestamp"] = datetime.fromisoformat(record["timestamp"].replace("Z", ""))

    # Normalize DTC code
    if isinstance(record["dtc_code"], str):
        record["dtc_code_list"] = [record["dtc_code"]]
    else:
        record["dtc_code_list"] = record["dtc_code"]

    # Add severity enrichment
    record["engine_temp_status"] = _engine_temp_status(record["engine_temp_c"], record.get("coolant_temp_c"))

    return record



# ---------- Telematics Severity Enrichment ----------
def _engine_temp_status(engine_temp: float, coolant_temp: float) -> str:
    if engine_temp < 85:
        return "normal"
    elif 85 <= engine_temp <= 100:
        return "elevated"
    else:
        return "overheating"



# ---------- 4. Load CAPA/RCA Library ----------
def load_capa_rca_docs(base_path="../data/capa_rca_library.json") -> List[Document]:
    data = load_json(base_path)

    # Convert single entry → list
    if isinstance(data, dict):
        data = [data]

    documents = []

    for entry in data:
        content = (
            f"Failure Pattern: {entry['failure_pattern']}\n"
            f"Root Cause: {entry['root_cause']}\n"
            f"CAPA Recommendation: {entry['capa']}\n"
            f"Manufacturing Feedback: {entry['manufacturing_feedback']}"
        )

        doc = Document(
            page_content=content,
            metadata={
                "id": entry["id"],
                "confidence": entry.get("confidence", 0.5),
                "related_dtc_codes": entry.get("related_dtc_codes", [])
            }
        )

        documents.append(doc)

    return documents
