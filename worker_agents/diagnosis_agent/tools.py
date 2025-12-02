# tools.py
from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history,
    load_telematics,
    load_capa_rca_docs
)
from .vectorstore_builder import get_vectorstore

@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Return normalized vehicle profile dict from shared loader."""
    return load_vehicle_profile(vehicle_id)


@tool("get_maintenance_history")
def get_maintenance_history_tool(vehicle_id: str):
    """Return list of maintenance history items (normalized)."""
    return load_maintenance_history(vehicle_id)


@tool("get_telematics_snapshot")
def get_telematics_snapshot_tool(vehicle_id: str):
    """Return the latest telematics snapshot."""
    return load_telematics(vehicle_id)


@tool("search_capa_rca")
def search_capa_rca_tool(query: str, top_k: int = 3):
    """
    Query the RCA/CAPA vectorstore and return matched entries with metadata.
    The vectorstore is built at startup by vectorstore_builder.get_vectorstore().
    """
    vs = get_vectorstore()
    hits = vs.similarity_search(query, k=top_k)
    # Each hit is a LangChain Document with page_content and metadata
    results = []
    for doc in hits:
        results.append({
            "content": doc.page_content,
            "metadata": doc.metadata
        })
    return results
