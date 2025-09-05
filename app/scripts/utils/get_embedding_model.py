import time
# from langchain_community.embeddings import FastEmbedEmbeddings

# def get_embedding_model():
#     """Lightweight embeddings with FastEmbed (no torch, no sentence-transformers)."""
#     print("\n" + "="*60)
#     print("EMBEDDING MODEL")
#     print("="*60)

#     device = 'cpu'
#     print(f" Detected device: {device} (FastEmbed runs on CPU)")

#     # Good small models supported by FastEmbed
#     model_name = "BAAI/bge-small-en-v1.5"   # or "intfloat/e5-small-v2"
#     print(f"Loading FastEmbed model: {model_name}")

#     try:
#         start = time.time()
#         embeddings = FastEmbedEmbeddings(
#             model_name=model_name,
#             # Optional: put caches outside the image so containers stay small
#         )
#         print(f"Model loaded in {time.time() - start:.2f}s")
#         return embeddings
#     except Exception as e:
#         print(f"Embedding model failed: {e}")
#         return None
from fastembed import TextEmbedding

def get_embedding_model():
    """Lightweight embeddings with FastEmbed directly (no LangChain wrapper)."""
    print("\n" + "="*60)
    print("EMBEDDING MODEL")
    print("="*60)

    device = 'cpu'
    print(f" Detected device: {device} (FastEmbed runs on CPU)")

    # Good small models supported by FastEmbed
    model_name = "BAAI/bge-small-en-v1.5"   # or "intfloat/e5-small-v2"
    print(f"Loading FastEmbed model: {model_name}")

    try:
        start = time.time()
        # Use FastEmbed directly
        # embeddings = TextEmbedding(
        #     model_name=model_name,
        #     # cache_dir="./embeddings_cache"  # Optional: specify cache directory
        # )
        wrapper = FastEmbedWrapper()
        print(f"Model loaded in {time.time() - start:.2f}s")
        
        return wrapper
        
        
        
    except Exception as e:
        print(f"Embedding model failed: {e}")
        return None

# If you need LangChain compatibility, create a wrapper class
class FastEmbedWrapper:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model_name=model_name)
    
    def embed_documents(self, texts):
        """Embed a list of documents."""
        return list(self.model.embed(texts))
    
    def embed_query(self, text):
        """Embed a single query."""
        return list(self.model.embed([text]))[0]