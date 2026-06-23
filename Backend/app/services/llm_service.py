from langchain_ollama import ChatOllama

from app.core.config import settings

_llm = None


def get_llm():
    """Return the configured local chat model."""
    global _llm
    if _llm is not None:
        return _llm

    if settings.LLM_PROVIDER != "ollama":
        raise ValueError("Only the local Ollama provider is enabled for this app")

    _llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
    )
    return _llm
