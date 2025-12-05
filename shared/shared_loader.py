import json
import os
from datetime import datetime
from typing import Dict, List, Any

from langchain_core.documents import Document


# ---------- Auto-correct base path ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


def safe_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


# ---------- Safe JSON Loader ----------
def load_json(file_path: str) -> Any:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[shared_loader] JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- VEHICLE PROFILES ----------
def load_vehicle_profile(vehicle_id: str) -> Dict:
    path = safe_path("vehicle_profiles.json")
    data = load_json(path)

    # Normalize list / single object
    vehicles = data if isinstance(data, list) else [data]

    vehicle = next((v for v in vehicles if v["vehicle_id"] == vehicle_id), None)

    if vehicle is None:
        return {"error": f"Vehicle {vehicle_id} not found", "exists": False}

    # Enrich fields
    vehicle.setdefault("known_model_defect", "none")
    vehicle.setdefault("cost_sensitivity", False)
    vehicle["risk_index"] = compute_vehicle_risk(vehicle)

    return vehicle


def compute_vehicle_risk(vehicle: Dict) -> float:
    try:
        age = datetime.now().year - int(vehicle.get("manufacturing_year", 2020))
        usage = vehicle.get("avg_km_per_day", 10)
        climate_factor = 1.2 if vehicle.get("climate_zone") == "Hot" else 1.0
        risk = (age * 0.3 + usage * 0.02) * climate_factor
        return round(min(risk, 1.0), 2)
    except:
        return 0.3


# ---------- MAINTENANCE HISTORY ----------
def load_maintenance_history(vehicle_id: str) -> List[Dict]:
    path = safe_path("maintenance_history.json")
    data = load_json(path)

    records = data if isinstance(data, list) else [data]
    history = [r for r in records if r["vehicle_id"] == vehicle_id]

    # Convert timestamps safely
    for h in history:
        try:
            h["date"] = datetime.fromisoformat(h["date"])
        except:
            h["date"] = None

        h.setdefault("components_serviced", [])
        h.setdefault("parts_replaced", [])
        h.setdefault("warranty_applied", False)

    return history


# ---------- LIVE TELEMATICS ----------
def load_telematics(vehicle_id: str) -> Dict:
    path = safe_path("live_telematics_feed.json")
    data = load_json(path)

    records = data if isinstance(data, list) else [data]
    tele = next((r for r in records if r["vehicle_id"] == vehicle_id), None)

    if tele is None:
        return {"error": f"No telematics for {vehicle_id}", "exists": False}

    # timestamp normalization
    try:
        tele["timestamp"] = datetime.fromisoformat(tele["timestamp"].replace("Z", ""))
    except:
        tele["timestamp"] = None

    # DTC normalization
    dtc = tele.get("dtc_code")
    tele["dtc_code_list"] = dtc if isinstance(dtc, list) else [dtc]

    # enrich engine temp severity
    tele["engine_temp_status"] = engine_temp_status(
        tele.get("engine_temp_c", 0),
        tele.get("coolant_temp_c", 0),
    )
    return tele


def engine_temp_status(engine_temp: float, coolant_temp: float) -> str:
    if engine_temp < 85:
        return "normal"
    elif engine_temp <= 100:
        return "elevated"
    return "overheating"


# ---------- CAPA/RCA DOCS ----------
def load_capa_rca_docs() -> List[Document]:
    path = safe_path("capa_rca_library.json")
    data = load_json(path)

    entries = data if isinstance(data, list) else [data]
    docs = []

    for e in entries:
        content = (
            f"Failure Pattern: {e['failure_pattern']}\n"
            f"Root Cause: {e['root_cause']}\n"
            f"CAPA: {e['capa']}\n"
            f"Feedback: {e['manufacturing_feedback']}"
        )
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "id": e["id"],
                    "confidence": e.get("confidence", 0.5),
                    "related_dtc_codes": e.get("related_dtc_codes", [])
                }
            )
        )
    return docs
