# shared/shared_loader.py

import json
import os
from datetime import datetime
from typing import Dict, List, Any

from langchain_core.documents import Document


# ---------- Base path helpers ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # /shared
DATA_DIR = os.path.join(BASE_DIR, "..", "data")              # /data


def _path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        raise FileNotFoundError(f"[shared_loader] JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- 1. VEHICLE PROFILES ----------
def load_vehicle_profile(vehicle_id: str) -> Dict:
    path = _path("vehicle_profiles.json")
    data = _load_json(path)

    vehicles = data if isinstance(data, list) else [data]
    v = next((x for x in vehicles if x.get("vehicle_id") == vehicle_id), None)

    if v is None:
        return {"exists": False, "vehicle_id": vehicle_id, "error": f"Vehicle {vehicle_id} not found"}

    # Default fields
    v.setdefault("known_model_defect", "none")
    v.setdefault("cost_sensitivity", False)

    # Simple risk score
    try:
        age = datetime.now().year - int(v.get("manufacturing_year", 2020))
        usage = v.get("avg_km_per_day", 10)
        climate_factor = 1.2 if v.get("climate_zone") == "Hot" else 1.0
        risk = (age * 0.3 + usage * 0.02) * climate_factor
        v["risk_index"] = round(min(risk, 1.0), 2)
    except Exception:
        v["risk_index"] = 0.3

    v["exists"] = True
    return v


# ---------- 2. MAINTENANCE HISTORY ----------
def load_maintenance_history(vehicle_id: str) -> List[Dict]:
    path = _path("maintenance_history.json")
    data = _load_json(path)

    records = data if isinstance(data, list) else [data]
    history = [r for r in records if r.get("vehicle_id") == vehicle_id]

    for h in history:
        # Robust date parsing
        date_str = h.get("date")
        try:
            h["date"] = datetime.fromisoformat(date_str) if date_str else None
        except Exception:
            h["date"] = None

        h.setdefault("components_serviced", [])
        h.setdefault("parts_replaced", [])
        h.setdefault("warranty_applied", False)

    return history


# ---------- 3. LIVE TELEMATICS ----------
def load_telematics(vehicle_id: str) -> Dict:
    path = _path("live_telematics_feed.json")
    data = _load_json(path)

    records = data if isinstance(data, list) else [data]
    rec = next((r for r in records if r.get("vehicle_id") == vehicle_id), None)

    if rec is None:
        return {"exists": False, "vehicle_id": vehicle_id, "error": f"No telematics for {vehicle_id}"}

    # Normalize timestamp
    ts = rec.get("timestamp")
    try:
        rec["timestamp"] = datetime.fromisoformat(ts.replace("Z", "")) if ts else None
    except Exception:
        rec["timestamp"] = None

    # Normalize DTC
    dtc = rec.get("dtc_code")
    rec["dtc_code_list"] = dtc if isinstance(dtc, list) else [dtc]

    # Simple engine temp status
    engine_temp = rec.get("engine_temp_c", 0)
    if engine_temp < 85:
        rec["engine_temp_status"] = "normal"
    elif engine_temp <= 100:
        rec["engine_temp_status"] = "elevated"
    else:
        rec["engine_temp_status"] = "overheating"

    rec["exists"] = True
    return rec


# ---------- 4. CAPA / RCA DOCS ----------
def load_capa_rca_docs() -> List[Document]:
    path = _path("capa_rca_library.json")
    data = _load_json(path)

    entries = data if isinstance(data, list) else [data]
    docs: List[Document] = []

    for e in entries:
        content = (
            f"Failure Pattern: {e['failure_pattern']}\n"
            f"Root Cause: {e['root_cause']}\n"
            f"CAPA Recommendation: {e['capa']}\n"
            f"Manufacturing Feedback: {e['manufacturing_feedback']}"
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
