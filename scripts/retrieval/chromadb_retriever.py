import os
from scripts.utils.get_embedding_model import get_embedding_model
from scripts.utils.get_vector_store import get_vector_store

def chromadb_retriever():
    # Initialize embedding model
    embeddings = get_embedding_model()
    if not embeddings:
        print("Failed to initialize embedding model.")
        return None

    # Setup vector store
    sample_type = 'small'  # Example sample type

    chroma_path = os.path.join('data', 'vector_store', sample_type)
    collection_name = "news_articles_" + sample_type
    vector_store = get_vector_store(chroma_path, collection_name, embeddings)
    
    if not vector_store:
        print("Failed to setup vector store.")
        return None
    print(len(vector_store))
    print("ChromaDB retriever initialized successfully.")
    return vector_store

def retrieve_chunks(vector_store, question, k=5):
    """Retrieve top-k chunks and return with similarity scores"""
    results = vector_store.similarity_search_with_score(question, k=k)
    chunks, scores = zip(*results) if results else ([], [])
    return list(chunks), list(scores)

