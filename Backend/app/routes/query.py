import logging

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.schemas.models import QueryRequest, QueryResponse, SourceDocument
from app.utils.graph import (
    build_retrieval_question,
    is_public_cacheable_route,
    rag_graph,
    route_question,
)
from app.services.memory_service import MemoryService
from app.services.mental_health_service import MentalHealthService
from app.services.redis_service import RedisSemanticCacheService
from app.utils.authentication import get_token_payload, hash_token
from app.db.database import get_db, get_session_by_token_hash



router = APIRouter()
logger = logging.getLogger(__name__)
memory_service = MemoryService()
mental_health_service = MentalHealthService(memory_service=memory_service)
redis_cache_service = RedisSemanticCacheService()


def sources_to_dicts(sources: list[SourceDocument]) -> list[dict]:
    return [source.model_dump() for source in sources]


def evaluate_mental_health_if_needed(
    is_authenticated: bool,
    user_id: int | None,
    user_reg_id: str | None,
    db: Session,
    analysis: dict | None = None,
) -> None:
    if not is_authenticated or user_id is None:
        return

    mental_health_service.evaluate_user_risk(
        user_id=str(user_id),
        reg_id=user_reg_id,
        db=db,
        analysis=analysis,
    )

@router.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    user_token: str | None = Header(default=None, alias="X-User-Token"),
    db: Session = Depends(get_db),
):
    try:
        is_authenticated = False
        user_id = None
        user_reg_id = None

        if user_token:
            payload = get_token_payload(user_token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired user token",
                )
            session = get_session_by_token_hash(hash_token(user_token), db)
            if not session or session.user_id != payload.get("user_id"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session is invalid or expired",
                )
            is_authenticated = True
            user_id = payload.get("user_id")
            user_reg_id = payload.get("reg_id")

        interaction_user_id = str(user_id) if user_id is not None else request.user_id
        conversation_history = memory_service.get_user_memory(interaction_user_id)[-6:]
        mental_health_assessment = mental_health_service.assess_message(
            request.question,
            conversation_history,
        )

        route = route_question(
            request.question,
            is_authenticated=is_authenticated,
            conversation_history=conversation_history,
            mental_health_assessment=mental_health_assessment,
        )
        cache_question = build_retrieval_question(request.question, conversation_history)
        if is_public_cacheable_route(route):
            cached = redis_cache_service.get_similar_answer(cache_question)
            if cached:
                sources = [
                    SourceDocument(**source)
                    for source in cached.get("sources", [])
                ]
                answer = cached["answer"]
                memory_service.add_interaction(
                    user_id=interaction_user_id,
                    question=request.question,
                    answer=answer,
                )
                evaluate_mental_health_if_needed(
                    is_authenticated=is_authenticated,
                    user_id=user_id,
                    user_reg_id=user_reg_id,
                    db=db,
                    analysis=mental_health_assessment,
                )
                return QueryResponse(answer=answer, sources=sources)

        state = {
            "question": request.question,
            "context": None,
            "docs": None,
            "answer": None,
            "route": route,
            "is_authenticated": is_authenticated,
            "user_reg_id": user_reg_id,
            "top_k": request.top_k,
            "conversation_history": conversation_history,
            "mental_health_assessment": mental_health_assessment,
        }

        result = rag_graph.invoke(state)

        # Extract docs safely
        docs = result.get("docs") or []  # ← defaults to empty list if None

        sources = []
        for doc in docs:
            metadata = getattr(doc, "metadata", {}) or {}
            sources.append(SourceDocument(
                content=getattr(doc, "page_content", str(doc)),
                doc_id=metadata.get("doc_id", "unknown"),
                chunk_index=metadata.get("chunk_index", 0),
                source_name=metadata.get("source_name"),
            ))

        answer = result.get("answer", "")

        memory_service.add_interaction(
            user_id= interaction_user_id,
            question= request.question,
            answer= answer
        )

        evaluate_mental_health_if_needed(
            is_authenticated=is_authenticated,
            user_id=user_id,
            user_reg_id=user_reg_id,
            db=db,
            analysis=mental_health_assessment,
        )

        if is_public_cacheable_route(result.get("route")):
            redis_cache_service.set_answer(
                question=cache_question,
                answer=answer,
                sources=sources_to_dicts(sources),
                route=result.get("route", "rag"),
            )

        return QueryResponse(
            answer=answer,
            sources=sources
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Query processing failed")
        raise HTTPException(status_code=500, detail="Unable to process the query")
