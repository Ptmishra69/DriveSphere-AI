# worker_agents/data_analysis/agent_logic.py

from typing import Dict, Any

from shared.shared_loader import (
    load_telematics,
    load_vehicle_profile,
    load_maintenance_history,
)


def detect_raw_anomalies(telematics: Dict[str, Any]):
    """
    Simple rule-based anomaly detector.
    Works even if some fields are missing.
    """
    anomalies = []

    if not isinstance(telematics, dict) or not telematics.get("exists", True):
        anomalies.append({
            "component": "system",
            "type": "no_telematics_data",
            "severity": "high"
        })
        return anomalies

    engine_temp = telematics.get("engine_temp_c", 0)
    brake_wear = telematics.get("brake_pad_wear_pct", 100)
    battery_health = telematics.get("battery_health_pct", 100)
    oil_pressure = telematics.get("oil_pressure_psi", 100)

    # Engine temperature rules
    if engine_temp > 100:
        anomalies.append({
            "component": "engine",
            "type": "overheating",
            "severity": "high"
        })
    elif engine_temp > 85:
        anomalies.append({
            "component": "engine",
            "type": "elevated_temperature",
            "severity": "medium"
        })

    # Brake pad wear
    if brake_wear < 20:
        anomalies.append({
            "component": "brake_system",
            "type": "brake_pad_thin",
            "severity": "medium"
        })

    # Battery health
    if battery_health < 40:
        anomalies.append({
            "component": "battery",
            "type": "battery_health_low",
            "severity": "high"
        })

    # Oil pressure
    if oil_pressure < 25:
        anomalies.append({
            "component": "engine",
            "type": "low_oil_pressure",
            "severity": "high"
        })

    return anomalies


def analyze_vehicle_telematics(vehicle_id: str) -> Dict[str, Any]:
    """
    MAIN ANALYSIS FUNCTION
    Called by FastAPI in main.py
    """

    # 1) Load raw data safely
    tele = load_telematics(vehicle_id)
    profile = load_vehicle_profile(vehicle_id)
    history = load_maintenance_history(vehicle_id)

    # 2) Detect anomalies
    alerts = detect_raw_anomalies(tele)

    # 3) Build response (clean_json in main.py will make datetimes serializable)
    return {
        "vehicle_id": vehicle_id,
        "telematics_found": tele.get("exists", False),
        "vehicle_profile_found": profile.get("exists", False),
        "maintenance_records": len(history),
        "alerts": alerts,
        "raw_telematics": tele,
    }
