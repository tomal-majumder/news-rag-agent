import time
from scripts.utils.get_device import get_device
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embedding_model():
    """Test 2: Initialize and test embedding model with auto device"""
    print("\n" + "="*60)
    print("EMBEDDING MODEL")
    print("="*60)

    # Simple device detection
    device = get_device()
    print(f" Using device: {device}")

    model_name = "all-MiniLM-L6-v2"
    print(f"Loading embedding model: {model_name}")

    try:
        start_time = time.time()
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},  # Use detected device
            encode_kwargs={'normalize_embeddings': True}
        )
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f} seconds")
        return embeddings

    except Exception as e:
        print(f"Embedding model failed: {e}")
        return None