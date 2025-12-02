# agent_logic.py
import math
import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .tools import (
    get_vehicle_profile_tool,
    get_maintenance_history_tool,
    get_telematics_snapshot_tool,
    search_capa_rca_tool
)
from .vectorstore_builder import get_vectorstore

# --------- Utility helpers ----------
def _simple_rule_predict(telematics: Dict[str, Any]) -> List[Dict]:
    """
    Quick heuristic-based mapping from telematics anomalies to probable components/failures.
    Returns list of candidate dicts: {predicted_failure, component, base_confidence, reason}
    """
    candidates = []

    et = telematics.get("engine_temp_c")
    batt = telematics.get("battery_health_pct")
    oilp = telematics.get("oil_pressure_psi")
    brake_wear = telematics.get("brake_pad_wear_pct")
    dtc_list = telematics.get("dtc_code_list", [])

    # Engine overheating
    if et and et > 100:
        candidates.append({
            "predicted_failure": "Engine Overheating (cooling system)",
            "component": "engine/cooling",
            "base_confidence": 0.7,
            "reason": f"engine_temp_c={et}"
        })
    elif et and 85 < et <= 100:
        candidates.append({
            "predicted_failure": "Elevated Engine Temperature (monitor)",
            "component": "engine",
            "base_confidence": 0.45,
            "reason": f"engine_temp_c={et}"
        })

    # Battery
    if batt is not None and batt < 45:
        candidates.append({
            "predicted_failure": "Battery Degradation",
            "component": "electrical/battery",
            "base_confidence": 0.6,
            "reason": f"battery_health_pct={batt}"
        })

    # Oil pressure
    if oilp is not None and oilp < 25:
        candidates.append({
            "predicted_failure": "Low Oil Pressure",
            "component": "engine/lubrication",
            "base_confidence": 0.8,
            "reason": f"oil_pressure_psi={oilp}"
        })

    # Brakes
    if brake_wear is not None and brake_wear < 20:  # 12 in sample -> low percent means thin pads
        candidates.append({
            "predicted_failure": "Brake Pads Worn",
            "component": "brake_system",
            "base_confidence": 0.65,
            "reason": f"brake_pad_wear_pct={brake_wear}"
        })

    # DTC codes mapping (simple)
    for code in dtc_list:
        if code and code.startswith("P0"):
            candidates.append({
                "predicted_failure": f"OBD Diagnostic code {code} - possible subsystem issue",
                "component": "electronic/ecu",
                "base_confidence": 0.5,
                "reason": f"dtc_code={code}"
            })

    return candidates


def _map_confidence_with_history(base_conf: float, history_summary: Dict) -> float:
    """
    Adjust confidence using maintenance history signals.
    """
    # simple boost if recurring issues found
    if history_summary.get("recurring_issues"):
        return min(0.95, base_conf + 0.15)
    if history_summary.get("declined_repairs", 0) > 0:
        # slightly lower effective confidence due to incomplete repairs
        return min(0.95, base_conf + 0.05)
    return base_conf


def _urgency_from_confidence_and_severity(conf: float, severity_hint: str = None) -> str:
    if conf >= 0.8:
        return "high"
    if conf >= 0.5:
        return "medium"
    return "low"


# --------- LLM integration for refining predictions ----------
def _llm_refine_predictions(vehicle_id: str, telematics: Dict, candidates: List[Dict], history_summary: Dict):
    """
    Use an LLM to refine/validate candidate failures, and optionally suggest a primary predicted failure,
    mapped severity and confidence. Returns a dict structure.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.12)

    # Build prompt
    prompt = (
        f"You are a diagnostics assistant. Given vehicle id {vehicle_id},\n"
        f"telematics snapshot: {telematics}\n"
        f"candidate predictions (from heuristics): {candidates}\n"
        f"maintenance history summary: {history_summary}\n\n"
        "For each candidate, evaluate plausibility and assign an adjusted confidence (0-1). "
        "Then pick the top predicted_failure and produce a short human-readable reason and suggested immediate action.\n\n"
        "Return only JSON with keys: 'refined_candidates' (list), 'top_prediction' (object with predicted_failure, component, confidence, urgency, recommended_action')."
    )

    resp = llm.generate([prompt])
    text = resp.generations[0][0].text.strip()

    # Safeguard: try to parse JSON from LLM; if fails, fallback to simple logic
    import json
    try:
        parsed = json.loads(text)
        return parsed
    except Exception:
        # fallback: pick highest base_confidence adjusted by history
        for c in candidates:
            c["confidence"] = _map_confidence_with_history(c["base_confidence"], history_summary)
        candidates_sorted = sorted(candidates, key=lambda x: x["confidence"], reverse=True)
        top = candidates_sorted[0] if candidates_sorted else None
        if top:
            top_conf = top["confidence"]
            urgency = _urgency_from_confidence_and_severity(top_conf)
            top["urgency"] = urgency
            top["recommended_action"] = "Recommend service center inspection within 48 hours" if urgency != "low" else "Monitor and schedule normal service"
        return {
            "refined_candidates": candidates,
            "top_prediction": top
        }


# --------- Main expose function ----------
def diagnose_vehicle(vehicle_id: str) -> Dict:
    """
    End-to-end diagnosis:
    - fetch telematics, vehicle profile, history
    - rule-based candidate generation
    - RCA/CAPA lookup for supporting evidence
    - LLM refinement + final output
    """
    # Tools (direct calls)
    telematics = get_telematics_snapshot_tool.run(vehicle_id)
    profile = get_vehicle_profile_tool.run(vehicle_id)
    history_summary = get_maintenance_history_tool.run(vehicle_id)

    # Step 1: heuristics
    candidates = _simple_rule_predict(telematics)

    # Step 2: RCA/CAPA lookup: query vectorstore with telematics summary text + samples
    vs = get_vectorstore()
    query_text = f"telematics snapshot: {telematics}. profile: {profile}. history_summary: {history_summary}"
    rca_hits = vs.similarity_search(query_text, k=3)
    rca_info = [{
        "content": d.page_content,
        "metadata": d.metadata
    } for d in rca_hits]

    # Add RCA evidence to candidate reasons if DTC or symptom matches
    for c in candidates:
        # naive mapping: if any RCA metadata DTC overlaps, boost base confidence
        for hit in rca_info:
            related = hit["metadata"].get("related_dtc_codes", [])
            # check if any dtc in telematics matches related
            dtcs = telematics.get("dtc_code_list", [])
            if any(d in related for d in dtcs):
                c["base_confidence"] = min(0.98, c["base_confidence"] + 0.12)
                c.setdefault("evidence", []).append(hit["metadata"])

    # Step 3: LLM refine
    llm_result = _llm_refine_predictions(vehicle_id, telematics, candidates, history_summary)

    # Build structured final output
    top = llm_result.get("top_prediction")
    refined = llm_result.get("refined_candidates", candidates)

    return {
        "vehicle_id": vehicle_id,
        "predicted_failure": top,
        "candidates": refined,
        "rca_evidence": rca_info
    }
