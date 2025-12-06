# agent_logic.py

import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from .tools import (
    get_vehicle_profile_tool,
    get_maintenance_history_tool,
    get_telematics_snapshot_tool,
)
from .vectorstore_builder import get_vectorstore


# --------------------------------------------------
#   SIMPLE RULE-BASED CANDIDATE GENERATION
# --------------------------------------------------

def _simple_rule_predict(telematics: Dict[str, Any]) -> List[Dict]:
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

    # Brake pads
    if brake_wear is not None and brake_wear < 20:
        candidates.append({
            "predicted_failure": "Brake Pads Worn",
            "component": "brake_system",
            "base_confidence": 0.65,
            "reason": f"brake_pad_wear_pct={brake_wear}"
        })

    # DTC codes
    for code in dtc_list:
        if code and code.startswith("P0"):
            candidates.append({
                "predicted_failure": f"OBD Diagnostic code {code}",
                "component": "electronic/ecu",
                "base_confidence": 0.5,
                "reason": f"dtc_code={code}"
            })

    return candidates



# --------------------------------------------------
#   CONFIDENCE MAPPING + URGENCY RULES
# --------------------------------------------------

def _map_confidence_with_history(base_conf: float, history_summary: Dict) -> float:
    if history_summary.get("recurring_issues"):
        return min(1.0, base_conf + 0.15)
    if history_summary.get("declined_repairs", 0) > 0:
        return min(1.0, base_conf + 0.05)
    return base_conf


def _urgency_from_conf(conf: float) -> str:
    if conf >= 0.8:
        return "high"
    if conf >= 0.5:
        return "medium"
    return "low"



# --------------------------------------------------
#   SAFE LLM INTEGRATION (NO HANGS)
# --------------------------------------------------

def _llm_refine_predictions(vehicle_id: str, telematics: Dict, candidates: List[Dict], history_summary: Dict):
    """
    Safer LLM call (invoke + timeout + fallback).
    Will NEVER block the agent.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, timeout=20)

    prompt = f"""
    You are an automotive diagnostics expert.

    Vehicle ID: {vehicle_id}
    Telematics: {telematics}
    Heuristic candidates: {candidates}
    Maintenance history: {history_summary}

    Improve confidence, validate issues, and choose one top predicted failure.

    Return strictly JSON:
    {{
      "refined_candidates": [...],
      "top_prediction": {{
         "predicted_failure": "...",
         "component": "...",
         "confidence": 0-1,
         "urgency": "low/medium/high",
         "recommended_action": "..."
      }}
    }}
    """

    try:
        resp = llm.invoke(prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)
        return json.loads(text)

    except Exception as e:
        print("[LLM ERROR - FALLBACK USED]", e)

        # fallback logic
        for c in candidates:
            c["confidence"] = _map_confidence_with_history(c["base_confidence"], history_summary)

        candidates_sorted = sorted(candidates, key=lambda x: x["confidence"], reverse=True)

        top = candidates_sorted[0] if candidates_sorted else None

        if top:
            top_conf = top["confidence"]
            top["urgency"] = _urgency_from_conf(top_conf)
            top["recommended_action"] = (
                "Recommend inspection within 48 hours"
                if top["urgency"] != "low"
                else "Monitor and schedule routine service"
            )

        return {
            "refined_candidates": candidates,
            "top_prediction": top
        }



# --------------------------------------------------
#   MAIN DIAGNOSIS PIPELINE
# --------------------------------------------------

def diagnose_vehicle(vehicle_id: str) -> Dict:

    # --- Load data via tools ---
    telematics = get_telematics_snapshot_tool.run(vehicle_id)
    profile = get_vehicle_profile_tool.run(vehicle_id)
    history_summary = get_maintenance_history_tool.run(vehicle_id)

    # --- Step 1: Rule-based heuristics ---
    candidates = _simple_rule_predict(telematics)

    # --- Step 2: RCA/CAPA context (vectorstore search) ---
    vs = get_vectorstore()
    query = f"vehicle {vehicle_id}, telematics={telematics}, profile={profile}, history={history_summary}"
    rca_hits = vs.similarity_search(query, k=3)
    rca_info = [{"content": h.page_content, "metadata": h.metadata} for h in rca_hits]

    # Add RCA evidence boosts
    dtcs = telematics.get("dtc_code_list", [])
    for c in candidates:
        for hit in rca_info:
            r_related = hit["metadata"].get("related_dtc_codes", [])
            if any(d in r_related for d in dtcs):
                c["base_confidence"] = min(1.0, c["base_confidence"] + 0.12)

    # --- Step 3: LLM refine (non-blocking) ---
    llm_result = _llm_refine_predictions(vehicle_id, telematics, candidates, history_summary)

    top = llm_result.get("top_prediction")
    refined = llm_result.get("refined_candidates", candidates)

    # --- Return final structured response ---
    return {
        "vehicle_id": vehicle_id,
        "predicted_failure": top,
        "candidates": refined,
        "rca_evidence": rca_info,
        "telematics": telematics,
        "vehicle_profile": profile
    }
