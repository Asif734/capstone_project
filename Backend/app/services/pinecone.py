"""
Backward compatibility layer for pinecone service.
Vector storage has been migrated to FAISS (app.services.faiss_service).
"""
import logging
from app.services.faiss_service import (
    store_embeddings,
    get_vectorstore,
    get_retriever,
    get_documents_metadata,
    get_document_names,
    delete_document_by_name,
)

logger = logging.getLogger(__name__)


def get_index():
    return get_vectorstore()


__all__ = [
    "store_embeddings",
    "get_vectorstore",
    "get_retriever",
    "get_index",
    "get_documents_metadata",
    "get_document_names",
    "delete_document_by_name",
]
