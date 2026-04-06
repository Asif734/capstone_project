from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def get_embedding(chunks):
    embeddings = model.encode(
        chunks,
        convert_to_numpy= True,
        show_progress_bar= True,
        batch_size =32
        )
    print(f" Generated {len(embeddings)} embeddings for {len(chunks)} chunks")
    return embeddings