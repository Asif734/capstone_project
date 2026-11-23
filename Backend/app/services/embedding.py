from sentence_transformers import SentenceTransformer
from app.core.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def get_embedding(chunks):
    model = get_model()
    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=32,
        normalize_embeddings=True,
        )
    return embeddings
