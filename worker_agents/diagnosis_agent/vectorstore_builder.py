# vectorstore_builder.py
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from shared.shared_loader import load_capa_rca_docs
import os

_vectorstore = None

def build_vectorstore(embeddings_model_name: str = "text-embedding-3-small"):
    """
    Build (or rebuild) the vectorstore from capa_rca_library.json using OpenAIEmbeddings.
    Ensure OPENAI_API_KEY is set in your environment.
    """
    global _vectorstore
    docs = load_capa_rca_docs(base_path=os.path.join("..", "data", "capa_rca_library.json"))
    # Instantiate OpenAI embeddings (requires OPENAI_API_KEY)
    embeddings = OpenAIEmbeddings(model=embeddings_model_name)
    # Build FAISS vectorstore
    _vectorstore = FAISS.from_documents(docs, embeddings)
    return _vectorstore

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = build_vectorstore()
    return _vectorstore
