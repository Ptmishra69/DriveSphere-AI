# worker_agents/diagnosis_agent/main.py

import sys, os
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.vectorstore import get_vectorstore
from worker_agents.diagnosis_agent.agent_logic import diagnose_vehicle


# -----------------------------
# 🚀 Lifespan Handler (Startup + Shutdown)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚡ [Startup] Preloading FAISS vectorstore...")
    get_vectorstore()   # loads global vectorstore once
    print("✔ Vectorstore ready.")

    yield  # ---- Application Runs Here ----

    print("🛑 [Shutdown] DiagnosisAgent shutting down.")


# -----------------------------
# 🚀 FastAPI App Initialization
# -----------------------------
app = FastAPI(title="Diagnosis Agent", lifespan=lifespan)


# -----------------------------
# Request Model
# -----------------------------
class DiagnosisRequest(BaseModel):
    vehicle_id: str


# -----------------------------
# API Endpoint
# -----------------------------
@app.post("/diagnose")
def diagnose(req: DiagnosisRequest):
    return diagnose_vehicle(req.vehicle_id)
