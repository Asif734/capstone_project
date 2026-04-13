from fastapi import APIRouter, HTTPException, Header
from app.schemas.models import QueryRequest, QueryResponse, SourceDocument
from app.utils.graph import rag_graph
from app.services.retriever_service import get_retriever
from app.services.memory_service import MemoryService
from app.utils.authentication import verify_user_token, get_token_payload
# from app.services.redis_service import RedisCacheService



router = APIRouter()
memory_service= MemoryService()
# redis_service= RedisCacheService()

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    user_token: str | None = Header(default=None, alias="X-User-Token"),
):
    try:
        # Invoke RAG graph
        # cached_answer= redis_service.get_answer(request.question)
        # if cached_answer:
        #     memory_service.add_interaction(
        #     user_id= request.user_id,
        #     question= request.question,
        #     answer= cached_answer
        # )
        #     return QueryResponse(answer= cached_answer, sources= [])

        is_authenticated= False
        user_reg_id = None

        if user_token:
            payload = get_token_payload(user_token)
            if payload:
                is_authenticated = True
                user_reg_id = payload.get("reg_id")

        state= {
            "question": request.question,
            "context": None,
            "docs": None,
            "answer": None,
            "route": None,
            "is_authenticated": is_authenticated,
            "user_reg_id": user_reg_id,
            "top_k": request.top_k
        }

        result = rag_graph.invoke(state)

        # Extract docs safely
        docs = result.get("docs") or []  # ← defaults to empty list if None

        sources = []
        for doc in docs:
            sources.append(SourceDocument(
                content=getattr(doc, "page_content", str(doc)),
                doc_id=getattr(doc.metadata, "doc_id", "unknown") if hasattr(doc, "metadata") else "unknown",
                chunk_index=getattr(doc.metadata, "chunk_index", 0) if hasattr(doc, "metadata") else 0
            ))

        answer= result.get("answer", "")
        memory_service.add_interaction(
            user_id= request.user_id,
            question= request.question,
            answer= answer
        )

        return QueryResponse(
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")



