# vectorstore_builder.py

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from shared.shared_loader import load_capa_rca_docs

_vectorstore = None

def build_vectorstore():
    global _vectorstore

    docs = load_capa_rca_docs()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    _vectorstore = FAISS.from_documents(docs, embeddings)
    return _vectorstore


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = build_vectorstore()
    return _vectorstore
