import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor

from .tools import (
    get_vehicle_profile,
    get_historical_usage,
    get_telematics_snapshot
)


# ============================================================
# CLEAN JSON SERIALIZER
# ============================================================

def clean_json(obj):
    """Recursively convert datetime → ISO and ensure JSON-safe output."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(i) for i in obj]
    return obj


# ============================================================
# RULE-BASED ANOMALY DETECTION
# ============================================================

def detect_raw_anomalies(telematics: dict):
    anomalies = []

    if not isinstance(telematics, dict):
        return [{"component": "system", "type": "invalid_telematics_data", "severity": "high"}]

    et = telematics.get("engine_temp_c", 0)
    if et > 100:
        anomalies.append({"component": "engine", "type": "overheating", "severity": "high"})
    elif et > 85:
        anomalies.append({"component": "engine", "type": "elevated_temperature", "severity": "medium"})

    if telematics.get("brake_pad_wear_pct", 100) < 20:
        anomalies.append({"component": "brake_system", "type": "brake_pad_thin", "severity": "medium"})

    if telematics.get("battery_health_pct", 100) < 40:
        anomalies.append({"component": "battery", "type": "battery_health_low", "severity": "high"})

    if telematics.get("oil_pressure_psi", 100) < 25:
        anomalies.append({"component": "engine", "type": "low_oil_pressure", "severity": "high"})

    return anomalies


# ============================================================
# LLM AGENT FACTORY — NEW LANGCHAIN v0.3 API
# ============================================================

def llm_reasoning_agent():
    """Builds an OpenAI Functions Agent (new LangChain API)."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    tools = [
        get_vehicle_profile,
        get_historical_usage,
        get_telematics_snapshot
    ]

    # Build the agent
    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools
    )

    # Wrap with AgentExecutor (new required wrapper)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False
    )


# ============================================================
# MAIN TELEMATICS ANALYSIS PIPELINE
# ============================================================

def analyze_vehicle_telematics(vehicle_id: str):

    # --------------------------------------------------------
    # STEP 1 — Load telematics via TOOL
    # --------------------------------------------------------
    try:
        telematics = get_telematics_snapshot.run(vehicle_id)
    except Exception as e:
        return {
            "vehicle_id": vehicle_id,
            "error": f"Failed to load telematics: {str(e)}"
        }

    telematics_safe = clean_json(telematics)

    # --------------------------------------------------------
    # STEP 2 — Rule-based detection
    # --------------------------------------------------------
    rule_anomalies = detect_raw_anomalies(telematics_safe)

    # --------------------------------------------------------
    # STEP 3 — Build LLM reasoning prompt
    # --------------------------------------------------------
    llm_input = f"""
    You are an automotive diagnostics expert.

    Analyze the vehicle telematics and infer deeper mechanical failures.

    Vehicle ID: {vehicle_id}
    Telematics JSON: {json.dumps(telematics_safe)}

    STRICT JSON OUTPUT ONLY:
    {{
      "vehicle_id": "{vehicle_id}",
      "ai_inferred_alerts": [
        {{
          "component": "...",
          "issue": "...",
          "severity": "..."
        }}
      ]
    }}
    """

    # --------------------------------------------------------
    # STEP 4 — Invoke LLM agent
    # --------------------------------------------------------
    agent = llm_reasoning_agent()

    try:
        # New API returns a dict: {"output": "...", "logs": "..."}
        response = agent.invoke({"input": llm_input})
        llm_output = response.get("output", '{"ai_inferred_alerts": []}')
    except Exception as e:
        print("LLM ERROR:", e)
        llm_output = '{"ai_inferred_alerts": []}'

    # --------------------------------------------------------
    # STEP 5 — Parse LLM JSON safely
    # --------------------------------------------------------
    try:
        llm_data = json.loads(llm_output)
    except:
        llm_data = {"ai_inferred_alerts": []}

    # --------------------------------------------------------
    # STEP 6 — Final merged output
    # --------------------------------------------------------
    final = {
        "vehicle_id": vehicle_id,
        "alerts": rule_anomalies,                     # Rule-based
        "ai_inferred_alerts": llm_data.get("ai_inferred_alerts", [])  # LLM based
    }

    return clean_json(final)
