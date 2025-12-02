# agent_logic.py

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .tools import (
    get_vehicle_profile_tool,
    get_maintenance_history_tool,
    search_capa_rca_tool
)
from .rules import (
    map_issue_to_root_cause,
    climate_factor
)
import json


def build_rca_agent():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.15
    )

    tools = [
        get_vehicle_profile_tool,
        get_maintenance_history_tool,
        search_capa_rca_tool
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False
    )
    return agent


def generate_manufacturing_insights(vehicle_id: str, diagnosis: dict, feedback: dict):
    agent = build_rca_agent()

    failure = diagnosis["predicted_failure"]["predicted_failure"]
    component = diagnosis["predicted_failure"]["component"]
    urgency = diagnosis["predicted_failure"]["urgency"]

    profile = get_vehicle_profile_tool.run(vehicle_id)
    climate = profile.get("climate_zone")

    maintenance_history = get_maintenance_history_tool.run(vehicle_id)

    # Step 1: Rule-based hint
    rule_root_cause = map_issue_to_root_cause(failure)
    climate_boost = climate_factor(climate, failure)

    # Step 2: Vectorstore pattern matching
    query = f"{failure} {component} {climate} {feedback}"
    rca_hits = search_capa_rca_tool.run(query)

    # Step 3: LLM refinement
    prompt = f"""
    You are an automotive quality RCA/CAPA expert.

    Diagnose long-term patterns using:
    - Failure: {failure}
    - Component: {component}
    - Urgency: {urgency}
    - Vehicle profile: {json.dumps(profile, indent=2)}
    - Maintenance history: {json.dumps(maintenance_history, indent=2)}
    - Customer feedback: {json.dumps(feedback, indent=2)}
    - Pattern matches: {json.dumps(rca_hits, indent=2)}
    - Rule root cause: {rule_root_cause}
    - Climate boost: {climate_boost}

    Generate structured insights for manufacturing teams:
    {{
      "primary_root_cause": "...",
      "recommended_capa_actions": [...],
      "recurrence_risk_score": 0-1,
      "should_notify_manufacturing": true/false,
      "manufacturing_notes": "...",
      "service_center_guidelines": "..."
    }}
    """

    raw = agent.run(prompt)

    try:
        insights = json.loads(raw)
    except:
        insights = {
            "primary_root_cause": rule_root_cause,
            "recommended_capa_actions": ["Perform cooling system redesign"],
            "recurrence_risk_score": 0.6 + climate_boost,
            "should_notify_manufacturing": True,
            "manufacturing_notes": "Recurring pattern detected.",
            "service_center_guidelines": "Inspect for underlying component fatigue."
        }

    return insights
