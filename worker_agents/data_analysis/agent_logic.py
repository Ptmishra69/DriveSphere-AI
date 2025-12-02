# agent_logic.py

from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from .tools import get_vehicle_profile, get_historical_usage, get_telematics_snapshot


# -------------------------------
# Rule-Based Severity Detection
# -------------------------------
def detect_raw_anomalies(telematics: dict):
    anomalies = []

    # Engine Temperature
    if telematics["engine_temp_c"] > 100:
        anomalies.append({
            "component": "engine",
            "type": "overheating",
            "severity": "high"
        })
    elif telematics["engine_temp_c"] > 85:
        anomalies.append({
            "component": "engine",
            "type": "elevated_temperature",
            "severity": "medium"
        })

    # Brake Pad Wear
    if telematics["brake_pad_wear_pct"] < 20:
        anomalies.append({
            "component": "brake_system",
            "type": "brake_pad_thin",
            "severity": "medium"
        })

    # Battery Health
    if telematics["battery_health_pct"] < 40:
        anomalies.append({
            "component": "battery",
            "type": "battery_health_low",
            "severity": "high"
        })

    # Oil Pressure
    if telematics["oil_pressure_psi"] < 25:
        anomalies.append({
            "component": "engine",
            "type": "low_oil_pressure",
            "severity": "high"
        })

    return anomalies



# -------------------------------
# LLM REASONING AGENT
# -------------------------------
def llm_reasoning_agent():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    tools = [
        get_vehicle_profile,
        get_historical_usage,
        get_telematics_snapshot
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False
    )

    return agent



# -------------------------------
# MAIN ANALYSIS PIPELINE
# -------------------------------
def analyze_vehicle_telematics(vehicle_id: str):
    agent = llm_reasoning_agent()

    # Step 1 — Get Telematics (via tool)
    telematics = get_telematics_snapshot.run(vehicle_id)

    # Step 2 — Rule-based anomaly detection
    rule_anomalies = detect_raw_anomalies(telematics)

    # Step 3 — LLM analysis for deeper context
    llm_input = f"""
    Vehicle ID: {vehicle_id}
    Telematics Data: {telematics}

    Using the sensor data, maintenance history, and profile,
    identify potential failure patterns, their components, 
    and classify severity (low/medium/high).

    Return only JSON:
    {{
       "vehicle_id": "...",
       "ai_inferred_alerts": [...]
    }}
    """

    llm_result = agent.run(llm_input)

    # Step 4 — Merge rule-based + LLM alerts
    final_output = {
        "vehicle_id": vehicle_id,
        "alerts": rule_anomalies,
        "ai_inferred_alerts": llm_result.get("ai_inferred_alerts", [])
    }

    return final_output
