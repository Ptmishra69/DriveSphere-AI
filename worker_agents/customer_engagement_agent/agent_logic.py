# agent_logic.py

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .tools import (
    get_vehicle_profile_tool,
    get_maintenance_history_tool
)
from .message_templates import (
    intro_line,
    persuasive_line,
    safety_line,
    closing_line
)
import json


def build_engagement_agent():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )

    tools = [
        get_vehicle_profile_tool,
        get_maintenance_history_tool
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False
    )
    return agent


def generate_engagement(vehicle_id: str, diagnosis: dict):
    agent = build_engagement_agent()

    # Extract key fields from diagnosis
    failure = diagnosis["predicted_failure"]["predicted_failure"]
    urgency = diagnosis["predicted_failure"]["urgency"]
    issue_comp = diagnosis["predicted_failure"]["component"]

    # Load vehicle context
    profile = get_vehicle_profile_tool.run(vehicle_id)
    history = get_maintenance_history_tool.run(vehicle_id)

    model = profile["model"]
    cost_sensitive = profile.get("cost_sensitivity", False)
    climate = profile.get("climate_zone")

    # Build structured base message (before LLM refinement)
    base_message = {
        "intro": intro_line(model, urgency),
        "explanation": f"We found an issue related to your {failure}.",
        "persuasion": persuasive_line(cost_sensitive, failure),
        "safety": safety_line(urgency),
        "close": closing_line(),
        "context": {
            "vehicle": profile,
            "history": len(history),
            "urgency": urgency,
            "climate_zone": climate
        }
    }

    # Prompt for LLM refinement
    prompt = f"""
    Convert the following technical structure into a friendly,
    human-like, persuasive message for the vehicle owner.

    Maintain clarity, empathy, and action-orientation.

    DATA:
    {json.dumps(base_message, indent=2)}

    Return ONLY JSON:
    {{
        "full_message": "...",
        "short_push_notification": "...",
        "voice_script": "..."
    }}
    """

    result_raw = agent.run(prompt)

    # Parse JSON safely
    try:
        result = json.loads(result_raw)
    except:
        result = {
            "full_message": (
                f"{base_message['intro']} {base_message['explanation']} "
                f"{base_message['persuasion']} {base_message['safety']} "
                f"{base_message['close']}"
            ),
            "short_push_notification": f"Issue detected: {failure}. Tap to schedule service.",
            "voice_script": f"Hello! This is your Hero assistant. {base_message['intro']} {base_message['explanation']} {base_message['safety']}"
        }

    return result
