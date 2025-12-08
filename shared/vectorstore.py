# shared/vectorstore.py

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from .shared_loader import load_capa_rca_docs

_vectorstore = None


def build_vectorstore():
    global _vectorstore

    print("🔧 Building global FAISS vectorstore using MiniLM embeddings...")

    docs = load_capa_rca_docs()

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    _vectorstore = FAISS.from_documents(docs, embeddings)
    return _vectorstore


def get_vectorstore():
    global _vectorstore

    if _vectorstore is None:
        _vectorstore = build_vectorstore()

    return _vectorstore
