# agent_logic.py

import json
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage

# Tools (already decorated with @tool)
from .tools import (
    get_vehicle_profile_tool,
    get_past_feedback_tool,
    store_feedback_tool
)

from .sentiment_rules import rule_sentiment

load_dotenv()


def analyze_feedback(vehicle_id: str, feedback_text: str):
    """
    Processes customer feedback using:
    - Rule-based analysis
    - LLM JSON extraction
    - Tool-based storage
    """

    # 1. Rule-based sentiment
    sentiment, complaint_flag = rule_sentiment(feedback_text)

    # 2. Build Groq LLM
    llm = ChatGroq(
        model="llama3-70b-8192",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    )

    prompt = f"""
    A customer submitted feedback:

    "{feedback_text}"

    Vehicle ID: {vehicle_id}

    Extract structured info:
    - service_rating (1-5)
    - sentiment (positive/neutral/negative)
    - issues_reported (list of strings)
    - is_recurring (true/false)
    - recommended_followup_action

    Return ONLY valid JSON:
    {{
        "vehicle_id": "{vehicle_id}",
        "sentiment": "...",
        "service_rating": 1-5,
        "issues_reported": ["..."],
        "is_recurring": true/false,
        "recommended_followup_action": "..."
    }}
    """

    try:
        response = llm.invoke([
            SystemMessage(content="You are an expert JSON extractor."),
            HumanMessage(content=prompt)
        ])
        llm_raw = response.content
    except Exception as e:
        print("LLM ERROR:", e)
        llm_raw = ""

    # 3. Try JSON parsing
    try:
        structured = json.loads(llm_raw)
    except:
        structured = {
            "vehicle_id": vehicle_id,
            "sentiment": sentiment,
            "service_rating": 3,
            "issues_reported": [],
            "is_recurring": complaint_flag,
            "recommended_followup_action": (
                "Suggest service recheck" if complaint_flag else "None"
            )
        }

    # 4. Store feedback
    store_feedback_tool.run(json.dumps(structured))

    return structured
