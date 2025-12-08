# agent_logic.py   (Customer Engagement Agent using UEBA logs)

import json
import os
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

UEBA_LOG_PATH = os.path.join("..", "..", "data", "agent_activity_logs.json")

MODEL_NAME = "google/flan-t5-base"
_tokenizer = None
_model = None


# ---------------------------------------------------------
# Load HuggingFace LLM (FREE, offline)
# ---------------------------------------------------------
def load_llm():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model


def llm_generate(prompt: str, max_length=256):
    tokenizer, model = load_llm()
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_length=max_length,
            do_sample=True,
            temperature=0.4,
            top_p=0.9
        )

    return tokenizer.decode(output[0], skip_special_tokens=True)


# ---------------------------------------------------------
# Load UEBA logs
# ---------------------------------------------------------
def load_ueba_logs():
    if not os.path.exists(UEBA_LOG_PATH):
        return []
    with open(UEBA_LOG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


# ---------------------------------------------------------
# Extract latest diagnosis + analysis from UEBA logs
# ---------------------------------------------------------
def get_latest_agent_output(vehicle_id: str, agent_name: str):
    logs = load_ueba_logs()

    filtered = [
        entry for entry in logs
        if entry.get("agent_name") == agent_name
        and entry.get("extra", {}).get("vehicle_id") == vehicle_id
        and "response_json" in entry.get("extra", {})
    ]

    if not filtered:
        return None

    # sort by timestamp descending
    filtered.sort(key=lambda x: x["timestamp"], reverse=True)
    return filtered[0]["extra"]["response_json"]


# ---------------------------------------------------------
# Generate Customer Message
# ---------------------------------------------------------
def generate_engagement(vehicle_id: str):

    # 1️⃣ Get latest data-analysis result from UEBA logs
    analysis = get_latest_agent_output(vehicle_id, "DataAnalysisAgent")

    # 2️⃣ Get latest diagnosis result from UEBA logs
    diagnosis = get_latest_agent_output(vehicle_id, "DiagnosisAgent")

    if diagnosis is None:
        return {
            "error": "No diagnosis found in UEBA logs. Cannot generate engagement."
        }

    # 3️⃣ Prepare prompt
    prompt = f"""
You are a service assistant. Explain the issue to the vehicle owner in friendly, clear language.

DATA ANALYSIS:
{json.dumps(analysis, indent=2)}

DIAGNOSIS:
{json.dumps(diagnosis, indent=2)}

Write these outputs:
1. full_message - friendly explanation
2. short_push_notification - under 80 chars
3. voice_script - natural spoken sentence

Return ONLY JSON.
"""

    # 4️⃣ Run HuggingFace LLM
    raw = llm_generate(prompt)

    # 5️⃣ Try parsing JSON from HF output
    try:
        result = json.loads(raw)
    except:
        # fallback: create simple message
        failure = diagnosis["predicted_failure"]["predicted_failure"]
        urgency = diagnosis["predicted_failure"]["urgency"]

        result = {
            "full_message": f"We detected an issue: {failure}. Urgency: {urgency}. Please service soon.",
            "short_push_notification": f"Issue: {failure}.",
            "voice_script": f"Your vehicle has an issue: {failure}. It is {urgency} urgency."
        }

    return result
