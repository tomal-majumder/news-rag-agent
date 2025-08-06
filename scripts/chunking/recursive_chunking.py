import gc
import os
import time
import pandas as pd
from scripts.utils.get_memory_usage import get_memory_usage
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from scripts.utils.get_gpu_info import get_gpu_info
from scripts.utils.get_memory_usage import get_memory_usage
import chromadb.utils.embedding_functions as embedding_functions
import torch


def create_documents_batch(batch_df, text_splitter):
    """Create documents from a batch of articles"""
    documents = []

    for idx, row in batch_df.iterrows():
        # Create full text
        title = str(row['title']) if 'title' in row and str(row['title']) != 'nan' else "Untitled"
        content = str(row['article']) if 'article' in row and str(row['article']) != 'nan' else ""

        if not content.strip():
            continue

        full_text = f"Title: {title}\n\nContent: {content}"

        # Split into chunks
        chunks = text_splitter.split_text(full_text)

        # Create documents
        for i, chunk in enumerate(chunks):
            metadata = {
                'title': title,
                'publication': str(row.get('publication', 'Unknown')),
                'date': str(row.get('date', 'Unknown')),
                'url': str(row.get('url', '')),
                'article_id': str(idx),
            }

            documents.append({
                'content': chunk,
                'metadata': metadata,
                'id': f"doc_{idx}_{i}"
            })

    return documents

def create_chromadb_collection(embeddings, collection_name="news_articles_", sample_type='tiny'):
    """Create or load ChromaDB collection with your embedding model"""
    print(f"\nSetting up ChromaDB collection: {collection_name}")
    print(f"Using embedding model: {type(embeddings).__name__}")

    persist_directory= os.path.join('data', 'chromadb_storage', 'news_articles')
    persist_directory = f"{persist_directory}/{sample_type}"
    
    collection_name = f"{collection_name}{sample_type}"

    client = chromadb.PersistentClient(path=persist_directory)

    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"Found existing collection with {count:,} documents")
        return collection, client
    except:
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embeddings,  
            metadata={"description": "News articles with semantic search capability"}
        )
        print(f"Created new collection: {collection_name}")
        print(f"Embedding model: {type(embeddings).__name__}")
        return collection, client

def build_chromadb_from_articles(df, embeddings, batch_size=800, collection_name="news_articles_", sample_type='tiny'):
    """Build ChromaDB from articles DataFrame - GPU OPTIMIZED (minimal changes)"""
    print("\n" + "="*60)
    print("BUILDING CHROMADB FROM ARTICLES")
    print("="*60)
    print(f"Using embedding model: {type(embeddings).__name__}")

    use_gpu = get_gpu_info()

    if use_gpu:
        batch_size = min(batch_size * 1.5, 1000)  # More conservative increase
        print(f"GPU Mode: Increased batch_size to {batch_size}")
    else:
        batch_size = min(batch_size, 600)  # Conservative for CPU
        print(f"CPU Mode: Using batch_size {batch_size}")

    start_time = time.time()

    collection, client = create_chromadb_collection(embeddings, collection_name, sample_type)

    # Check if already populated
    existing_count = collection.count()
    # collection_name = f"{collection_name}{sample_type}"

    if existing_count > 0:
        print(f"Collection already has {existing_count:,} documents")
        rebuild = input("Rebuild collection? (y/n): ").lower()
        if rebuild != 'y':
            print("Using existing collection...")
            return collection, client
        else:
            # Delete and recreate
            client.delete_collection(collection_name + sample_type)
            collection, client = create_chromadb_collection(embeddings, collection_name, sample_type)


    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    # Process in batches
    total_articles = len(df)
    total_batches = (total_articles + batch_size - 1) // batch_size
    total_documents = 0

    print(f"Processing {total_articles:,} articles in {total_batches} batches")
    print(f"Batch size: {batch_size}")
    print(f"Initial memory: {get_memory_usage():.1f}MB")

    try:
        for batch_num in range(1, total_batches + 1):
            batch_start_time = time.time()

            # Get batch data
            start_idx = (batch_num - 1) * batch_size
            end_idx = min(start_idx + batch_size, total_articles)
            batch_df = df.iloc[start_idx:end_idx].copy()

            print(f"\n Processing batch {batch_num}/{total_batches}")
            print(f"   Articles: {len(batch_df)} (rows {start_idx}-{end_idx-1})")

            # Create documents for this batch
            documents = create_documents_batch(batch_df, text_splitter)
            batch_doc_count = len(documents)

            if not documents:
                print(f"No documents created from batch {batch_num}")
                continue

            print(f"Created {batch_doc_count} documents")

            # Prepare data for ChromaDB
            texts = [doc['content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            ids = [doc['id'] for doc in documents]

            # MINIMAL ADDITION: Handle ChromaDB batch size limit
            max_chroma_batch = 5000  # Safe limit for ChromaDB

            # MINIMAL ADDITION: Track embedding time
            embed_start = time.time()

            # Split into smaller chunks if needed
            if len(texts) > max_chroma_batch:
                print(f"Splitting {len(texts)} docs into chunks of {max_chroma_batch}")
                for i in range(0, len(texts), max_chroma_batch):
                    end_idx = min(i + max_chroma_batch, len(texts))
                    chunk_texts = texts[i:end_idx]
                    chunk_metadatas = metadatas[i:end_idx]
                    chunk_ids = ids[i:end_idx]

                    collection.add(
                        documents=chunk_texts,
                        metadatas=chunk_metadatas,
                        ids=chunk_ids
                    )
                    print(f"Added chunk {i//max_chroma_batch + 1}: {len(chunk_texts)} docs")
            else:
                # Add normally if under limit
                collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )

            # MINIMAL ADDITION: Show embedding speed
            embed_time = time.time() - embed_start
            docs_per_sec = batch_doc_count / embed_time if embed_time > 0 else 0

            total_documents += batch_doc_count

            # Cleanup - FREE MEMORY IMMEDIATELY
            del documents, texts, metadatas, ids, batch_df
            gc.collect()

            # MINIMAL ADDITION: Clear GPU cache if available
            if use_gpu:
                torch.cuda.empty_cache()

            batch_time = time.time() - batch_start_time
            memory_usage = get_memory_usage()

            print(f"Batch added to ChromaDB in {batch_time:.2f}s")
            print(f"Embedding speed: {docs_per_sec:.1f} docs/sec") 
            print(f"Memory usage: {memory_usage:.1f}MB (freed after batch)")
            print(f"Total documents: {total_documents:,}")

            # Memory warning
            if memory_usage > 12000:
                print(f"HIGH MEMORY WARNING: {memory_usage:.1f}MB")

        # Final statistics
        total_time = time.time() - start_time
        final_count = collection.count()

        print("\n" + "="*60)
        print("CHROMADB BUILD COMPLETED!")
        print("="*60)
        print(f"📊 Final Statistics:")
        print(f"   • Total articles processed: {total_articles:,}")
        print(f"   • Total documents in DB: {final_count:,}")
        print(f"   • Processing time: {total_time/60:.2f} minutes")
        print(f"   • Avg time per batch: {total_time/total_batches:.2f}s")
        print(f"   • Docs per article: {final_count/total_articles:.1f}")
        print(f"   • Final memory: {get_memory_usage():.1f}MB")
        print(f"   • Device used: {'GPU' if use_gpu else 'CPU'}")  # MINIMAL ADDITION
        print(f"   • Avg speed: {final_count/total_time:.1f} docs/sec")  # MINIMAL ADDITION
        print(f"   • Database location: ./chromadb_storage")

        return collection, client

    except Exception as e:
        print(f"\n Error in batch {batch_num}: {e}")
        raise e

# MINIMAL ADDITION: Create ChromaDB-compatible embedding function
def create_gpu_embeddings():
    """Create GPU-optimized embeddings (call this instead of your current embedding creation)"""

    device = "cuda" if torch.cuda.is_available() else "cpu"
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