# worker_agents/diagnosis_agent/agent_logic.py

from shared.shared_loader import (
    load_vehicle_profile,
    load_telematics,
    load_maintenance_history,
)

from shared.vectorstore import get_vectorstore


# ---------- RULE-BASED DIAGNOSTICS ----------
def rule_based_signals(tele):
    alerts = []

    if tele.get("engine_temp_c", 0) > 95:
        alerts.append({
            "component": "engine",
            "issue": "overheating",
            "severity": "high"
        })

    if tele.get("brake_pad_wear_pct", 100) < 15:
        alerts.append({
            "component": "brakes",
            "issue": "pad_wear_low",
            "severity": "medium"
        })

    if tele.get("battery_health_pct", 100) < 40:
        alerts.append({
            "component": "battery",
            "issue": "weak_battery",
            "severity": "medium"
        })

    return alerts


# ---------- RETRIEVAL FROM CAPA / RCA VECTORSTORE ----------
def capa_similarity(tele, rule_alerts):
    rule_summary = " ".join([f"{a['component']} {a['issue']}" for a in rule_alerts])

    query = f"""
    Vehicle Condition:
    - Engine Temp Status: {tele.get('engine_temp_status')}
    - Brake Pad Wear: {tele.get('brake_pad_wear_pct')}
    - Battery Health: {tele.get('battery_health_pct')}
    - Rule Alerts: {rule_summary}
    - DTC Codes: {tele.get('dtc_code_list')}
    """

    vs = get_vectorstore()
    docs = vs.similarity_search(query, k=3)
    return [d.page_content for d in docs]


# ---------- MAIN DIAGNOSIS PIPELINE ----------
def diagnose_vehicle(vehicle_id: str):
    profile = load_vehicle_profile(vehicle_id)
    tele = load_telematics(vehicle_id)
    history = load_maintenance_history(vehicle_id)

    if not profile.get("exists") or not tele.get("exists"):
        return {
            "vehicle_id": vehicle_id,
            "error": "Vehicle profile or telematics not found."
        }

    rule_alerts = rule_based_signals(tele)
    capa_docs = capa_similarity(tele, rule_alerts)

    # -------------------------------------------------------
    # ⭐ Compute most-likely predicted failure for CustomerAgent
    # -------------------------------------------------------
    if len(rule_alerts) > 0:
        top_alert = rule_alerts[0]    # priority 1: engine > brakes > battery
        predicted_failure = {
            "predicted_failure": top_alert["issue"],
            "urgency": top_alert["severity"],
            "component": top_alert["component"]
        }
    else:
        # fallback: low-risk general report
        predicted_failure = {
            "predicted_failure": "general_inspection_needed",
            "urgency": "low",
            "component": "vehicle"
        }

    # -------------------------------------------------------
    # Prepare summary text for debugging/logs
    # -------------------------------------------------------
    diagnosis_text = (
        f"Vehicle {vehicle_id} shows {len(rule_alerts)} preliminary alerts.\n"
        f"Telemetry analysis: Engine temp status = {tele.get('engine_temp_status')}.\n"
        f"Based on CAPA/RCA patterns, potential failure causes match: {capa_docs[:2]}.\n"
    )

    # -------------------------------------------------------
    # ⭐ FINAL OUTPUT (now compatible with CustomerAgent)
    # -------------------------------------------------------
    return {
        "vehicle_id": vehicle_id,
        "rule_alerts": rule_alerts,
        "capa_matches": capa_docs,
        "predicted_failure": predicted_failure,   # ⭐ ADDED BLOCK
        "diagnosis_summary": diagnosis_text
    }
