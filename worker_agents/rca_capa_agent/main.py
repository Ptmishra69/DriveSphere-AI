# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import generate_manufacturing_insights

app = FastAPI(
    title="RCA/CAPA Agent",
    description="Generates manufacturing improvement insights from diagnosis and feedback.",
    version="1.0.0"
)

class RCARequest(BaseModel):
    vehicle_id: str
    diagnosis: dict
    feedback: dict


@app.post("/rca")
def rca(req: RCARequest):
    insights = generate_manufacturing_insights(
        req.vehicle_id,
        req.diagnosis,
        req.feedback
    )
    return insights
