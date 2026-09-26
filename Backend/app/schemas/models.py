from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class QueryRequest(BaseModel):
    user_id: str = Field(..., min_length=8, max_length=128)
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)

    @field_validator("user_id", "question")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value

class SourceDocument(BaseModel):
    content: str
    doc_id: str
    chunk_index: int
    source_name: Optional[str] = None
    title: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
