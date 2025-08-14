from langchain import embedding_functions

# MINIMAL ADDITION: Create ChromaDB-compatible embedding function
def get_embedding_function():
    """Create GPU-optimized embeddings (call this instead of your current embedding creation)"""

    device = "cpu"
    print(f"Creating embeddings on: {device}")

    # For ChromaDB collection creation, use ChromaDB's embedding function
    if device == "cuda":
        # GPU optimized ChromaDB embedding function
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device=device
        )
        print("Created ChromaDB GPU embedding function")
    else:
        # CPU ChromaDB embedding function
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print("Created ChromaDB CPU embedding function")

    return embedding_function