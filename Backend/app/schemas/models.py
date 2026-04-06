from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    user_id: str
    question: str
    top_k: Optional[int] = 3

class SourceDocument(BaseModel):
    content: str
    doc_id: str
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
