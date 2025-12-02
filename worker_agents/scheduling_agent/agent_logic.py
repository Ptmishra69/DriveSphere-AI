# agent_logic.py

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .tools import (
    get_vehicle_profile_tool,
    get_service_center_slots_tool
)
from .slot_rules import prioritize_slots
import json


def build_scheduling_agent():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    tools = [
        get_vehicle_profile_tool,
        get_service_center_slots_tool
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False
    )
    return agent


def schedule_appointment(vehicle_id: str, diagnosis: dict, customer_pref: dict = None):
    agent = build_scheduling_agent()

    urgency = diagnosis["predicted_failure"]["urgency"]

    # load vehicle profile
    profile = get_vehicle_profile_tool.run(vehicle_id)
    city = profile["city"]

    # load all slots for this city
    centers = get_service_center_slots_tool.run(city)

    if not centers:
        return {
            "status": "no_slots_available",
            "message": f"No service centers found for {city}."
        }

    # rule-based prioritization
    recommended = prioritize_slots(centers, urgency)

    # Prepare base structure before LLM refinement
    base_info = {
        "vehicle_id": vehicle_id,
        "model": profile["model"],
        "city": city,
        "urgency": urgency,
        "recommended_slots": recommended,
        "customer_preference": customer_pref
    }

    # LLM prompt to finalize messaging
    prompt = f"""
    You are a smart scheduling assistant.
    Convert the following scheduling data into:
      - best_slot (top recommended slot)
      - alternate_slots (other options)
      - customer_friendly_text
      - voice_script

    DATA:
    {json.dumps(base_info, indent=2)}

    Return ONLY JSON structure:
    {{
       "best_slot": "...",
       "alternate_slots": [...],
       "customer_friendly_text": "...",
       "voice_script": "..."
    }}
    """

    raw = agent.run(prompt)

    try:
        refined = json.loads(raw)
    except:
        # fallback simple logic
        best_slot = recommended[0]
        refined = {
            "best_slot": best_slot["slot"],
            "alternate_slots": [s["slot"] for s in recommended[1:3]],
            "customer_friendly_text": (
                f"The best available appointment is {best_slot['slot']} at "
                f"{best_slot['location']}."
            ),
            "voice_script": (
                f"I recommend booking your service for {best_slot['slot']} "
                f"at {best_slot['location']}."
            )
        }

    return refined
