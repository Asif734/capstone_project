from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return _model

def get_embedding(chunks):
    model = get_model()
    embeddings = model.encode(
        chunks,
        convert_to_numpy= True,
        show_progress_bar= True,
        batch_size =32
        )
    print(f" Generated {len(embeddings)} embeddings for {len(chunks)} chunks")
    return embeddings
