# agent_logic.py

import json
from .tools import (
    get_vehicle_profile_tool,
    get_maintenance_history_tool,
    load_capa_rca_docs,
)
from .rules import map_issue_to_root_cause, climate_factor


def keyword_match_score(text: str, query: str) -> int:
    """Simple offline scoring based on keyword overlap."""
    text_l = text.lower()
    score = 0
    for word in query.lower().split():
        if word in text_l:
            score += 1
    return score


def search_capa_patterns(query: str):
    """
    Offline keyword-based CAPA/RCA search.
    Looks inside local JSON docs.
    """
    docs = load_capa_rca_docs()
    results = []

    for d in docs:
        text = d.get("content", "")
        score = keyword_match_score(text, query)
        if score > 0:
            results.append({
                "score": score,
                "content": text,
                "metadata": d.get("metadata", {})
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]


def generate_manufacturing_insights(vehicle_id: str,
                                    service_event: dict,
                                    feedback_analysis: dict):
    """
    Fully offline RCA/CAPA reasoning.

    Inputs: 
    - vehicle_id
    - service_event (dict)
    - feedback_analysis (dict)
    """

    print("\n===== RCA INPUT RECEIVED =====")
    print("Vehicle ID:", vehicle_id)
    print("Service Event:", service_event)
    print("Feedback Analysis:", feedback_analysis)
    print("================================\n")

    # Fetch base profile + maintenance
    profile = get_vehicle_profile_tool(vehicle_id)
    maintenance = get_maintenance_history_tool(vehicle_id)

    climate = profile.get("climate_zone", "")

    # Derive failure from feedback
    issues = feedback_analysis.get("issues_reported", [])
    if issues:
        failure = issues[0]       # take first as primary failure
    else:
        # fallback: build from service tasks or sentiment
        if feedback_analysis.get("sentiment") == "negative":
            failure = "customer_reported_issue"
        else:
            failure = "no_major_issue"

    # Rule-based RCA hints
    rule_rca = map_issue_to_root_cause(failure)
    climate_boost = climate_factor(climate, failure)

    # Query for pattern matching
    query = f"{vehicle_id} {failure} {climate} {issues}"
    capa_hits = search_capa_patterns(query)

    # Compute recurrence risk
    base_risk = 0.3
    if feedback_analysis.get("is_recurring", False):
        base_risk += 0.3
    base_risk += climate_boost

    risk_score = min(1.0, round(base_risk, 2))

    should_notify = risk_score > 0.5

    insights = {
        "vehicle_id": vehicle_id,
        "primary_root_cause": rule_rca,
        "recommended_capa_actions": [
            "Deep inspection of affected subsystem",
            "Cross-check historical failure patterns",
            "Evaluate need for component redesign"
        ],
        "recurrence_risk_score": risk_score,
        "should_notify_manufacturing": should_notify,
        "manufacturing_notes": (
            "Significant recurrence risk detected."
            if should_notify else
            "Issue appears low-risk."
        ),
        "service_center_guidelines":
            "Advise technician to inspect for wear, blockage, or calibration errors.",
        "pattern_matches": capa_hits
    }

    return insights
