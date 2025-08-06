from scripts.utils.get_device import get_device
from langchain_community.vectorstores import Chroma
import chromadb

def get_vector_store(chroma_path, collection_name, embeddings):
    """Setup Langchain vector store"""
    client = chromadb.PersistentClient(path=chroma_path)

    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    return vector_store