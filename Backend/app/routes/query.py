from fastapi import APIRouter, HTTPException, Header
from app.schemas.models import QueryRequest, QueryResponse, SourceDocument
from app.utils.graph import is_public_cacheable_route, rag_graph, route_question
from app.services.memory_service import MemoryService
from app.services.mental_health_service import MentalHealthService
from app.services.redis_service import RedisSemanticCacheService
from app.utils.authentication import get_token_payload
from app.db.database import get_db



router = APIRouter()
memory_service = MemoryService()
mental_health_service = MentalHealthService(memory_service=memory_service)
redis_cache_service = RedisSemanticCacheService()


def sources_to_dicts(sources: list[SourceDocument]) -> list[dict]:
    return [source.model_dump() for source in sources]


def evaluate_mental_health_if_needed(
    is_authenticated: bool,
    user_id: int | None,
    user_reg_id: str | None,
) -> None:
    if not is_authenticated or user_id is None:
        return

    db = next(get_db())
    try:
        mental_health_service.evaluate_user_risk(
            user_id=str(user_id),
            reg_id=user_reg_id,
            db=db,
        )
    finally:
        db.close()

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    user_token: str | None = Header(default=None, alias="X-User-Token"),
):
    try:
        is_authenticated = False
        user_id = None
        user_reg_id = None

        if user_token:
            payload = get_token_payload(user_token)
            if payload:
                is_authenticated = True
                user_id = payload.get("user_id")
                user_reg_id = payload.get("reg_id")

        route = route_question(request.question, is_authenticated=is_authenticated)
        if is_public_cacheable_route(route):
            cached = redis_cache_service.get_similar_answer(request.question)
            if cached:
                sources = [
                    SourceDocument(**source)
                    for source in cached.get("sources", [])
                ]
                answer = cached["answer"]
                interaction_user_id = str(user_id) if user_id is not None else request.user_id
                memory_service.add_interaction(
                    user_id=interaction_user_id,
                    question=request.question,
                    answer=answer,
                )
                evaluate_mental_health_if_needed(
                    is_authenticated=is_authenticated,
                    user_id=user_id,
                    user_reg_id=user_reg_id,
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
            "top_k": request.top_k
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
            ))

        answer = result.get("answer", "")
        interaction_user_id = str(user_id) if user_id is not None else request.user_id

        memory_service.add_interaction(
            user_id= interaction_user_id,
            question= request.question,
            answer= answer
        )

        evaluate_mental_health_if_needed(
            is_authenticated=is_authenticated,
            user_id=user_id,
            user_reg_id=user_reg_id,
        )

        if is_public_cacheable_route(result.get("route")):
            redis_cache_service.set_answer(
                question=request.question,
                answer=answer,
                sources=sources_to_dicts(sources),
                route=result.get("route", "rag"),
            )

        return QueryResponse(
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

