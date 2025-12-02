# tools.py

from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history,
    load_capa_rca_docs
)
from .vectorstore_builder import get_vectorstore


@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Fetch detailed profile for model, climate, usage."""
    return load_vehicle_profile(vehicle_id)


@tool("get_maintenance_history")
def get_maintenance_history_tool(vehicle_id: str):
    """Return full service + issue history for RCA context."""
    return load_maintenance_history(vehicle_id)


@tool("search_capa_rca")
def search_capa_rca_tool(query: str, top_k: int = 3):
    """Search CAPA/RCA patterns most similar to query."""
    vs = get_vectorstore()
    hits = vs.similarity_search(query, k=top_k)

    return [
        {"content": h.page_content, "metadata": h.metadata}
        for h in hits
    ]
