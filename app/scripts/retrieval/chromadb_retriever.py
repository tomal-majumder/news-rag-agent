def retrieve_chunks(vector_store, question, k=10):
    """Retrieve top-k chunks and return with similarity scores"""
    results = vector_store.similarity_search_with_score(question, k=k)
    chunks, scores = zip(*results) if results else ([], [])
    return list(chunks), list(scores)

