import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import torch
import faiss
import numpy as np
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[FAISS] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu", "local_files_only": True},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception:
            _embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
    return _embeddings


def _relevance_score_fn(score: float) -> float:
    # Embeddings are L2-normalized; inner product is cosine similarity [-1, 1].
    # Clamp to [0, 1] for LangChain relevance score filtering.
    return max(0.0, min(1.0, float(score)))


def get_index_path() -> Path:
    raw_path = getattr(settings, "FAISS_INDEX_PATH", "faiss_index")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / raw_path
    return path


def _create_empty_vectorstore() -> FAISS:
    dim = getattr(settings, "VECTOR_DIMENSION", getattr(settings, "PINECONE_DIMENSION", 384))
    index = faiss.IndexFlatIP(dim)
    return FAISS(
        embedding_function=get_embeddings(),
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
        distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
        relevance_score_fn=_relevance_score_fn,
    )


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    with _lock:
        if _vectorstore is not None:
            return _vectorstore

        index_dir = get_index_path()
        index_file = index_dir / "index.faiss"
        pkl_file = index_dir / "index.pkl"

        if index_file.exists() and pkl_file.exists():
            try:
                logger.info("Loading FAISS index from %s", index_dir)
                _vectorstore = FAISS.load_local(
                    folder_path=str(index_dir),
                    embeddings=get_embeddings(),
                    allow_dangerous_deserialization=True,
                    distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
                    relevance_score_fn=_relevance_score_fn,
                )
                return _vectorstore
            except Exception:
                logger.exception("Failed to load existing FAISS index from %s; creating empty index", index_dir)

        logger.info("Initializing new in-memory FAISS index")
        _vectorstore = _create_empty_vectorstore()
        return _vectorstore


def save_vectorstore() -> None:
    index_dir = get_index_path()
    index_dir.mkdir(parents=True, exist_ok=True)
    vs = get_vectorstore()
    vs.save_local(folder_path=str(index_dir))
    logger.info("Persisted FAISS index to %s", index_dir)


def store_embeddings(
    chunks: List[str],
    embeddings,
    doc_id: Optional[str] = None,
    source_name: Optional[str] = None,
    titles: Optional[List[str]] = None,
    max_metadata_length: int = 3000,
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match")
    if titles is not None and len(chunks) != len(titles):
        raise ValueError("Chunk and title counts do not match")
    if not chunks:
        raise ValueError("No document chunks were generated")
    if not doc_id:
        doc_id = str(uuid.uuid4())

    dim = getattr(settings, "VECTOR_DIMENSION", getattr(settings, "PINECONE_DIMENSION", 384))
    now_iso = datetime.now(timezone.utc).isoformat()

    text_embeddings = []
    metadatas = []
    ids = []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        values = emb.tolist() if hasattr(emb, "tolist") else list(emb)
        if len(values) != dim:
            raise ValueError(
                f"Embedding dimension {len(values)} does not match configured dimension {dim}"
            )

        safe_text = chunk[:max_metadata_length]
        meta = {
            "text": safe_text,
            "doc_id": doc_id,
            "chunk_index": i,
            "source_name": source_name or doc_id,
            "ingested_at": now_iso,
        }
        if titles and titles[i]:
            meta["title"] = titles[i]

        chunk_id = f"{doc_id}_chunk_{i}"
        text_embeddings.append((safe_text, values))
        metadatas.append(meta)
        ids.append(chunk_id)

    with _lock:
        vs = get_vectorstore()
        vs.add_embeddings(
            text_embeddings=text_embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        save_vectorstore()

    logger.info("Stored %s vectors in FAISS for %s", len(chunks), doc_id)
    return len(chunks)


def get_retriever(k: int = 3):
    return get_vectorstore().as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": settings.RAG_SCORE_THRESHOLD},
    )


def get_documents_metadata() -> List[dict]:
    """Return summary metadata for all unique documents currently stored in FAISS."""
    with _lock:
        vs = get_vectorstore()
        doc_map = {}
        for chunk_id, doc in vs.docstore._dict.items():
            meta = getattr(doc, "metadata", {}) or {}
            doc_id = meta.get("doc_id") or "default"
            source_name = meta.get("source_name") or doc_id

            key = (doc_id, source_name)
            if key not in doc_map:
                doc_map[key] = {
                    "document_id": doc_id,
                    "document_name": source_name,
                    "source_name": source_name,
                    "chunks_count": 0,
                    "ingested_at": meta.get("ingested_at"),
                }
            doc_map[key]["chunks_count"] += 1
            if not doc_map[key]["ingested_at"] and meta.get("ingested_at"):
                doc_map[key]["ingested_at"] = meta.get("ingested_at")

        return list(doc_map.values())


def get_document_names() -> List[str]:
    """Return a unique list of all document names/sources currently indexed in FAISS."""
    docs = get_documents_metadata()
    names = []
    for d in docs:
        name = d.get("document_name") or d.get("source_name") or d.get("document_id")
        if name and name not in names:
            names.append(name)
    return names


def delete_document_by_name(document_name: str) -> Optional[dict]:
    """
    Delete all chunks and vectors belonging to a document matching document_name.
    Matches against source_name, doc_id, filename stem, or case-insensitive variants.
    Returns deletion details dict, or None if no matching document was found.
    """
    if not document_name or not document_name.strip():
        raise ValueError("Document name is required")

    target = document_name.strip()
    target_lower = target.lower()
    target_stem = Path(target).stem.lower()

    with _lock:
        vs = get_vectorstore()
        matching_ids = []
        matched_doc_id = None
        matched_source_name = None

        for chunk_id, doc in vs.docstore._dict.items():
            meta = getattr(doc, "metadata", {}) or {}
            doc_id = str(meta.get("doc_id") or "")
            source_name = str(meta.get("source_name") or "")
            source_stem = Path(source_name).stem.lower()

            matches = (
                doc_id == target
                or source_name == target
                or doc_id.lower() == target_lower
                or source_name.lower() == target_lower
                or (source_stem and source_stem == target_stem)
                or (source_name.lower() in (f"{target_lower}.docx", f"{target_lower}.pdf", f"{target_lower}.txt"))
            )

            if matches:
                matching_ids.append(chunk_id)
                if not matched_doc_id:
                    matched_doc_id = doc_id
                if not matched_source_name:
                    matched_source_name = source_name

        if not matching_ids:
            return None

        # Delete all matching chunk vectors from FAISS index and docstore
        vs.delete(ids=matching_ids)
        save_vectorstore()

        from app.services.redis_service import redis_cache_service
        try:
            redis_cache_service.clear_cache()
        except Exception:
            logger.warning("Failed to clear redis cache after deleting document %s", target)

        logger.info(
            "Deleted %d chunks for document '%s' (doc_id: %s)",
            len(matching_ids),
            matched_source_name or target,
            matched_doc_id,
        )

        return {
            "document_name": matched_source_name or target,
            "document_id": matched_doc_id or target,
            "chunks_deleted": len(matching_ids),
            "remaining_total_chunks": len(vs.docstore._dict),
        }
