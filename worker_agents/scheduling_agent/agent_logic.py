# agent_logic.py  (HuggingFace / transformers version – FREE)

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from .tools import (
    get_vehicle_profile_tool,
    get_service_center_slots_tool
)
from .slot_rules import prioritize_slots
import json
import torch


# ------------------------------------------------------------
# Load HF Model (cached on first load, shared across requests)
# ------------------------------------------------------------

MODEL_NAME = "google/flan-t5-base"

_tokenizer = None
_model = None


def load_llm():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model


# ------------------------------------------------------------
# Helper: run HuggingFace LLM
# ------------------------------------------------------------

def llm_generate(prompt: str, max_tokens: int = 256):
    tokenizer, model = load_llm()

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_length=max_tokens,
            do_sample=True,
            top_p=0.9,
            temperature=0.4
        )

    text = tokenizer.decode(output[0], skip_special_tokens=True)
    return text


# ------------------------------------------------------------
# Main scheduling logic (LLM + rules)
# ------------------------------------------------------------

def schedule_appointment(vehicle_id: str, diagnosis: dict, customer_pref: dict = None):

    # ---------------------------------------------
    # Load vehicle profile (location / city)
    # ---------------------------------------------
    profile = get_vehicle_profile_tool.run(vehicle_id)
    city = profile.get("city", "Unknown City")
    model_name = profile.get("model", "vehicle")
    urgency = diagnosis["predicted_failure"]["urgency"]

    # ---------------------------------------------
    # Load all service center slots for this city
    # ---------------------------------------------
    centers = get_service_center_slots_tool.run(city)

    if not centers:
        return {
            "status": "no_slots_available",
            "message": f"No service centers found for city: {city}"
        }

    # ---------------------------------------------
    # Rule-based prioritization (deterministic)
    # ---------------------------------------------
    recommended_slots = prioritize_slots(centers, urgency)

    if not recommended_slots:
        return {
            "status": "no_recommended_slots",
            "message": f"No suitable slots found for {city}"
        }

    # ---------------------------------------------
    # Prepare structured info for LLM refinement
    # ---------------------------------------------
    best_slot = recommended_slots[0]
    alt_slots = recommended_slots[1:3]

    base_info = {
        "model": model_name,
        "city": city,
        "urgency": urgency,
        "best_slot": best_slot,
        "alternate_slots": alt_slots,
        "customer_pref": customer_pref,
    }

    # ---------------------------------------------
    # Prompt for LLM refinement (FREE HF model)
    # ---------------------------------------------
    prompt = f"""
You are a smart scheduling assistant for a motorcycle service brand.

Convert this scheduling data into natural language:

DATA:
{json.dumps(base_info, indent=2)}

Return the result in JSON with these fields:
- best_slot
- alternate_slots
- customer_friendly_text
- voice_script
    """

    llm_output = llm_generate(prompt)

    # ---------------------------------------------------------
    # HF models like T5 may not return clean JSON → fix fallback
    # ---------------------------------------------------------
    try:
        result = json.loads(llm_output)
    except Exception:
        # simple fallback if JSON fails:
        result = {
            "best_slot": best_slot["slot"],
            "alternate_slots": [s["slot"] for s in alt_slots],
            "customer_friendly_text": (
                f"Based on the issue urgency, the best available service "
                f"appointment is {best_slot['slot']} at {best_slot['location']}."
            ),
            "voice_script": (
                f"I recommend booking your appointment on {best_slot['slot']} "
                f"at {best_slot['location']} for your {model_name}."
            )
        }

    return result
