import logging
import uuid
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)
_pc = None
_index = None

def _get_client():
    global _pc
    if _pc is None:
        if not settings.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not configured")
        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise ImportError("pinecone package is required for Pinecone client") from exc
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    return _pc

def get_index():
    global _index
    if _index is not None:
        return _index

    pc = _get_client()
    index_name = settings.INDEX_NAME

    if index_name not in pc.list_indexes().names():
        from pinecone import ServerlessSpec

        pc.create_index(
            index_name,
            dimension=settings.PINECONE_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )

    _index = pc.Index(index_name)
    return _index

def store_embeddings(
    chunks,
    embeddings,
    doc_id=None,
    source_name=None,
    titles=None,
    max_metadata_length=3000,
):
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match")
    if titles is not None and len(chunks) != len(titles):
        raise ValueError("Chunk and title counts do not match")
    if not chunks:
        raise ValueError("No document chunks were generated")
    if not doc_id:
        doc_id = str(uuid.uuid4())

    index = get_index()
    vectors = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        values = emb.tolist()
        if len(values) != settings.PINECONE_DIMENSION:
            raise ValueError(
                f"Embedding dimension {len(values)} does not match configured dimension "
                f"{settings.PINECONE_DIMENSION}"
            )
        safe_text = chunk[:max_metadata_length]
        metadata = {
            "text": safe_text,
            "doc_id": doc_id,
            "chunk_index": i,
            "source_name": source_name or doc_id,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        if titles and titles[i]:
            metadata["title"] = titles[i]
        vectors.append({
            "id": f"{doc_id}_chunk_{i}",
            "values": values,
            "metadata": metadata,
        })

    batch_size = settings.PINECONE_UPSERT_BATCH_SIZE
    for start in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[start:start + batch_size])
    logger.info("Stored %s vectors in Pinecone for %s", len(vectors), doc_id)
    return len(vectors)
