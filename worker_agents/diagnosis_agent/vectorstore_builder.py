# vectorstore_builder.py

import os
import json
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

_vectorstore = None


def load_capa_rca_docs(path: str):
    """
    Load CAPA/RCA records from JSON file.
    Returns list of langchain Document objects.
    """
    from langchain.docstore.document import Document

    if not os.path.exists(path):
        print(f"[RCA] File not found: {path}")
        return []

    with open(path, "r") as f:
        data = json.load(f)

    docs = []
    # allow both: {..} or [ {...}, {...} ]
    if isinstance(data, dict):
        data = [data]

    for entry in data:
        text = (
            f"Failure Pattern: {entry.get('failure_pattern')}\n"
            f"Root Cause: {entry.get('root_cause')}\n"
            f"CAPA: {entry.get('capa')}\n"
            f"Manufacturing Feedback: {entry.get('manufacturing_feedback')}\n"
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": entry.get("id"),
                    "related_dtc_codes": entry.get("related_dtc_codes", []),
                    "confidence": entry.get("confidence", 0),
                }
            )
        )

    return docs


def build_vectorstore():
    """
    Build FAISS vectorstore from capa_rca_library.json
    """
    global _vectorstore

    json_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "capa_rca_library.json"
    )
    json_path = os.path.abspath(json_path)

    docs = load_capa_rca_docs(json_path)

    if not docs:
        print("[RCA] No documents loaded — vectorstore will be empty.")
        _vectorstore = None
        return None

    embeddings = OpenAIEmbeddings()
    _vectorstore = FAISS.from_documents(docs, embeddings)

    print(f"[RCA] Vectorstore built with {len(docs)} documents.")
    return _vectorstore


def get_vectorstore():
    """Return cached vectorstore or build it once."""
    global _vectorstore
    if _vectorstore is None:
        return build_vectorstore()
    return _vectorstore
