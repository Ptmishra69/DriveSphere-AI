# agent_logic.py

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .tools import (
    get_vehicle_profile_tool,
    get_past_feedback_tool,
    store_feedback_tool
)
from .sentiment_rules import rule_sentiment

import json


def build_feedback_agent():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    tools = [
        get_vehicle_profile_tool,
        get_past_feedback_tool,
        store_feedback_tool
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False
    )

    return agent


def analyze_feedback(vehicle_id: str, feedback_text: str):
    agent = build_feedback_agent()

    # Step 1: Rule-based interpretation
    sentiment, complaint_flag = rule_sentiment(feedback_text)

    # Step 2: LLM deeper analysis
    prompt = f"""
    The customer provided feedback: "{feedback_text}"
    Vehicle ID: {vehicle_id}

    Based on this feedback:
    - Extract service_rating (1 to 5)
    - Determine overall sentiment (positive/neutral/negative)
    - Identify any issues reported
    - Check if issues are recurring
    - Recommend followup action

    Return only JSON like:
    {{
       "vehicle_id": "...",
       "sentiment": "...",
       "service_rating": ...,
       "issues_reported": [...],
       "is_recurring": true/false,
       "recommended_followup_action": "..."
    }}
    """

    llm_raw = agent.run(prompt)

    # Step 3: Parse LLM JSON
    try:
        structured = json.loads(llm_raw)
    except:
        structured = {
            "vehicle_id": vehicle_id,
            "sentiment": sentiment,
            "issues_reported": [],
            "service_rating": 3,
            "is_recurring": complaint_flag,
            "recommended_followup_action": "Suggest service recheck" if complaint_flag else "None"
        }

    # Step 4: Store feedback record
    store_feedback_tool.run(json.dumps(structured))

    return structured
