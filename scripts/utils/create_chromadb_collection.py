import os
import chromadb
from langchain import embedding_functions
import torch

def create_chromadb_collection(embeddings, embedding_function, collection_name="news_articles_", sample_type='tiny'):
    """Create or load ChromaDB collection with your embedding model"""
    print(f"\nSetting up ChromaDB collection")
    print(f"Using embedding model: {type(embeddings).__name__}")

    persist_directory= os.path.join('data', 'chromadb_storage', 'news_articles')
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)

    persist_directory = f"{persist_directory}/{sample_type}"
    collection_name = f"{collection_name}{sample_type}"

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=persist_directory)

    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"Found existing collection with {count:,} documents")
        return collection, client
    except:
        # Create new collection with your embeddings
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"description": "News articles with semantic search capability"}
        )
        print(f"Created new collection: {collection_name}")
        return collection, client
