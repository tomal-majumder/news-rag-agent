import os
from app.scripts.utils.get_embedding_model import get_embedding_model
from app.scripts.utils.get_vector_store import get_vector_store
from app.core.settings import CHROMA_DIR, SAMPLE_TYPE

embeddings = get_embedding_model()
chroma_path = str(CHROMA_DIR)
collection_name = f"news_articles_{SAMPLE_TYPE}"

vector_store = get_vector_store(chroma_path, collection_name, embeddings)

def chromadb_retriever():    
    if not vector_store:
        print("Failed to setup vector store.")
        return None
    return vector_store

def retrieve_chunks(vector_store, question, k=5):
    """Retrieve top-k chunks and return with similarity scores"""
    results = vector_store.similarity_search_with_score(question, k=k)
    chunks, scores = zip(*results) if results else ([], [])
    return list(chunks), list(scores)

