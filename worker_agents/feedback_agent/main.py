from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import analyze_feedback

app = FastAPI(title="Feedback Agent", version="1.0.0")

class FeedbackRequest(BaseModel):
    vehicle_id: str
    feedback_text: str

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    return analyze_feedback(req.vehicle_id, req.feedback_text)
