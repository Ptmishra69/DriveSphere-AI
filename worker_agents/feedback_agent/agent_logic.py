# agent_logic.py

import json
import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

from .tools import (
    get_vehicle_profile_tool,
    get_past_feedback_tool,
    store_feedback_tool
)
from .sentiment_rules import rule_sentiment


# -------------------------------
# Load HuggingFace OFFLINE model
# -------------------------------
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"   # Example model, change if needed

print("Loading offline HuggingFace model locally...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype="auto",
    local_files_only=True
)

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=300
)


def analyze_feedback(vehicle_id: str, feedback_text: str):
    """
    Processes customer feedback fully OFFLINE using a local HuggingFace model.
    """

    # 1. Rule-based sentiment
    sentiment, complaint_flag = rule_sentiment(feedback_text)

    # 2. Prepare offline prompt
    prompt = f"""
You are an expert JSON extractor.
Read customer feedback and return ONLY a JSON object.

Feedback: "{feedback_text}"
Vehicle ID: {vehicle_id}

Return EXACT JSON:
{{
  "vehicle_id": "{vehicle_id}",
  "sentiment": "positive/neutral/negative",
  "service_rating": 1-5,
  "issues_reported": ["..."],
  "is_recurring": true/false,
  "recommended_followup_action": "..."
}}
"""

    # 3. Run offline LLM
    output = generator(prompt)[0]["generated_text"]

    # Extract the JSON part only
    json_start = output.find("{")
    json_end = output.rfind("}")

    if json_start != -1 and json_end != -1:
        llm_raw = output[json_start:json_end+1]
    else:
        llm_raw = ""

    # 4. Parse JSON
    try:
        structured = json.loads(llm_raw)
    except:
        # Fallback
        structured = {
            "vehicle_id": vehicle_id,
            "sentiment": sentiment,
            "service_rating": 3,
            "issues_reported": [],
            "is_recurring": complaint_flag,
            "recommended_followup_action":
                "Suggest service recheck" if complaint_flag else "None"
        }

    # 5. Store it using your @tool
    store_feedback_tool.run(json.dumps(structured))

    return structured
