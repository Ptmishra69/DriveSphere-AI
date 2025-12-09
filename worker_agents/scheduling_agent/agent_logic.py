import json
import os

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

from .tools import (
    load_vehicle_profile,
    load_service_center_slots
)

from .slot_rules import prioritize_slots


# -------------------------------
# Load HuggingFace offline model
# -------------------------------
MODEL_NAME = "google/flan-t5-base"

_tokenizer = None
_model = None


def load_llm():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model


def run_llm(prompt: str, max_length=256):
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


# -------------------------------
# Main scheduling logic
# -------------------------------
def schedule_appointment(vehicle_id: str, diagnosis: dict, customer_pref: dict = None):

    urgency = diagnosis["predicted_failure"]["urgency"]

    # Load offline data
    profile = load_vehicle_profile(vehicle_id)
    city = profile.get("city", "")

    centers = load_service_center_slots(city)

    if not centers:
        return {
            "status": "no_slots_available",
            "message": f"No service centers found for {city}."
        }

    recommended = prioritize_slots(centers, urgency)

    base_info = {
        "vehicle_id": vehicle_id,
        "model": profile.get("model"),
        "city": city,
        "urgency": urgency,
        "recommended_slots": recommended,
        "customer_preference": customer_pref,
    }

    prompt = f"""
Convert the following data into a JSON response:

{json.dumps(base_info, indent=2)}

Output JSON fields:
- best_slot
- alternate_slots
- customer_friendly_text
- voice_script

Return ONLY JSON.
"""

    raw = run_llm(prompt)

    # try to load JSON
    try:
        return json.loads(raw)
    except:
        best = recommended[0]
        return {
            "best_slot": best["slot"],
            "alternate_slots": [s["slot"] for s in recommended[1:3]],
            "customer_friendly_text": (
                f"The best slot is {best['slot']} at {best['location']}."
            ),
            "voice_script": (
                f"I recommend booking {best['slot']} at {best['location']}."
            )
        }
