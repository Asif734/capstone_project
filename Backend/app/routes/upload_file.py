import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.routes.admin import require_admin
from app.services.embedding import get_embedding
from app.services.faiss_service import (
    store_embeddings,
    get_documents_metadata,
    get_document_names,
    delete_document_by_name,
)
from app.services.redis_service import redis_cache_service
from app.utils.preprocess_text import chunk_sections, clean_text, extract_sections

router = APIRouter()
logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
DOC_ID_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


def normalize_doc_id(value: str | None) -> str:
    if not value:
        return str(uuid.uuid4())
    normalized = DOC_ID_PATTERN.sub("-", value.strip()).strip("-._")
    if not normalized:
        raise HTTPException(status_code=422, detail="Document name is invalid")
    return normalized[:128]


def ingest_document(file_bytes: bytes, filename: str, doc_id: str) -> int:
    sections = extract_sections(
        file_bytes, filename, max_pages=settings.MAX_DOCUMENT_PAGES
    )
    if not any(clean_text(text) for _, text in sections):
        raise ValueError("The document contains no extractable text")
    section_chunks = chunk_sections(sections)
    chunks = [chunk for chunk, _ in section_chunks]
    titles = [title for _, title in section_chunks]
    embeddings = get_embedding(chunks)
    stored_count = store_embeddings(
        chunks=chunks,
        embeddings=embeddings,
        doc_id=doc_id,
        source_name=filename,
        titles=titles,
    )
    redis_cache_service.clear_cache()
    return stored_count


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@router.post("/Upload", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def upload_file(
    file: UploadFile = File(...),
    doc_name: str | None = Form(default=None),
    _: None = Depends(require_admin),
):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()
    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported")

    file_bytes = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(file_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    doc_id = normalize_doc_id(doc_name)
    try:
        stored_count = await run_in_threadpool(
            ingest_document, file_bytes, filename, doc_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document ingestion failed for %s", filename)
        raise HTTPException(status_code=502, detail="Document ingestion failed") from exc

    return {
        "filename": filename,
        "document_id": doc_id,
        "chunks_stored": stored_count,
        "message": "Document uploaded and indexed successfully",
    }


@router.get("/documents", status_code=status.HTTP_200_OK)
@router.get("/Documents", status_code=status.HTTP_200_OK, include_in_schema=False)
@router.get("/document-names", status_code=status.HTTP_200_OK, include_in_schema=False)
@router.get("/documents/names", status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_documents():
    """
    Retrieve all document names and metadata currently stored in the knowledge base.
    """
    docs = await run_in_threadpool(get_documents_metadata)
    names = await run_in_threadpool(get_document_names)
    return {
        "documents": docs,
        "document_names": names,
        "total_documents": len(docs),
    }


@router.get("/documents/{document_name:path}", status_code=status.HTTP_200_OK)
async def get_document(document_name: str):
    """
    Retrieve details for a single document by its document name or document ID.
    """
    docs = await run_in_threadpool(get_documents_metadata)
    target = document_name.strip().lower()
    target_stem = Path(target).stem.lower()

    for d in docs:
        d_name = str(d.get("document_name") or "").lower()
        d_id = str(d.get("document_id") or "").lower()
        d_stem = Path(d_name).stem.lower()
        if (
            target in (d_name, d_id, d_stem)
            or d_name in (f"{target}.docx", f"{target}.pdf", f"{target}.txt")
        ):
            return {"document": d}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{document_name}' not found in knowledge base",
    )


@router.delete("/documents", status_code=status.HTTP_200_OK)
async def delete_document_by_query(
    document_name: str = Query(..., description="Name or ID of the document to delete"),
):
    """
    Delete a document and all its indexed chunks via query parameter.
    """
    return await delete_document(document_name)


@router.delete("/documents/{document_name:path}", status_code=status.HTTP_200_OK)
@router.delete("/document/{document_name:path}", status_code=status.HTTP_200_OK, include_in_schema=False)
async def delete_document(document_name: str):
    """
    Delete a document and all its indexed chunks using the document name or document ID.
    """
    if not document_name or not document_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document name is required",
        )

    result = await run_in_threadpool(delete_document_by_name, document_name.strip())
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' not found in knowledge base",
        )

    return {
        "message": f"Document '{result['document_name']}' deleted successfully",
        "document_name": result["document_name"],
        "document_id": result["document_id"],
        "chunks_deleted": result["chunks_deleted"],
        "remaining_total_chunks": result["remaining_total_chunks"],
    }

