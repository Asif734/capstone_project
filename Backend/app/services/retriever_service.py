from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

_embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

_vectorstore = LangchainPinecone.from_existing_index(
    index_name=settings.INDEX_NAME,
    embedding=_embeddings,
    text_key="text",
)

def get_retriever(k: int = 3):
    return _vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
