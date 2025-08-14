from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import PGVector
import chromadb
import os

def get_vector_store(chroma_path, collection_name, embeddings):
    """Setup Langchain vector store"""
    client = chromadb.PersistentClient(path=chroma_path)

    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    return vector_store

def get_vector_store_PG(embeddings, COLLECTION):
    conn = os.getenv("DATABASE_URL")

    if not conn:
        raise RuntimeError("DATABASE_URL not set")

    return PGVector(
        connection_string=conn,
        collection_name=COLLECTION,
        embedding_function=embeddings,
    )
