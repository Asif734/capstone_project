from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

_embeddings = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
    return _embeddings


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = LangchainPinecone.from_existing_index(
            index_name=settings.INDEX_NAME,
            embedding=get_embeddings(),
            text_key="text",
        )
    return _vectorstore

def get_retriever(k: int = 3):
    return get_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
