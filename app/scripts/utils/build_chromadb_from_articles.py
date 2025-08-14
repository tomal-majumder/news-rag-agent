from app.scripts.utils.create_chromadb_collection import create_chromadb_collection
from app.scripts.utils.create_documents_batch import create_documents_batch
from app.scripts.utils.get_memory_usage import get_memory_usage
from app.scripts.utils.get_gpu_info import get_gpu_info
from langchain.text_splitter import RecursiveCharacterTextSplitter
import gc
import time
from langchain_experimental.text_splitter import SemanticChunker

def build_chromadb_from_articles(df, embeddings, embedding_function, batch_size=400, splitter='recursive', collection_name="news_articles_", sample_type='tiny'):
    """Build ChromaDB from articles DataFrame - PERFORMANCE OPTIMIZED"""
    print("\n" + "="*60)
    print("BUILDING CHROMADB FROM ARTICLES (OPTIMIZED)")
    print("="*60)
    print(f"Using embedding model: {type(embeddings).__name__}")

    # Check GPU and optimize settings
    use_gpu = get_gpu_info()
    if use_gpu:
        # Smaller batches work better for GPU memory management
        batch_size = min(batch_size, 300)  # Conservative for stability
        print(f"🚀 GPU Mode: Using batch_size {batch_size}")
    else:
        batch_size = min(batch_size, 200)  # Even smaller for CPU
        print(f"💻 CPU Mode: Using batch_size {batch_size}")

    start_time = time.time()

    # Setup collection
    collection, client = create_chromadb_collection(embeddings, embedding_function, collection_name, sample_type)

    # Check if already populated
    existing_count = collection.count()
    collection_name = f"{collection_name}{sample_type}"

    if existing_count > 0:
        print(f"⚠️ Collection already has {existing_count:,} documents")
        rebuild = input("Rebuild collection? (y/n): ").lower()
        if rebuild != 'y':
            print("Using existing collection...")
            return collection, client
        else:
            client.delete_collection(collection_name)
            collection, client = create_chromadb_collection(embeddings, embedding_function, collection_name, sample_type)

    # Initialize text splitter
    if splitter == 'recursive':
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    elif splitter == 'semantic':
        # Use SemanticChunker if available
        print("Using SemanticChunker for text splitting")
        if not hasattr(embeddings, 'embed_query'):
            raise ValueError("Embeddings must have 'embed_query' method for SemanticChunker")

        text_splitter = SemanticChunker(embeddings)

    # Process in smaller batches for better memory management
    total_articles = len(df)
    total_batches = (total_articles + batch_size - 1) // batch_size
    total_documents = 0

    print(f"Processing {total_articles:,} articles in {total_batches} batches")
    print(f"Optimized batch size: {batch_size}")
    print(f"Initial memory: {get_memory_usage():.1f}MB")

    try:
        for batch_num in range(1, total_batches + 1):
            batch_start_time = time.time()

            # Get batch data
            start_idx = (batch_num - 1) * batch_size
            end_idx = min(start_idx + batch_size, total_articles)
            batch_df = df.iloc[start_idx:end_idx].copy()

            print(f"\nProcessing batch {batch_num}/{total_batches}")
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

            # OPTIMIZATION: Use smaller ChromaDB batches
            chroma_batch_size = 100  # Much smaller batches for ChromaDB insertion ***
            # this mico-batch insertion saves time
            embed_start = time.time()

            # Process in micro-batches
            for i in range(0, len(texts), chroma_batch_size):
                end_idx = min(i + chroma_batch_size, len(texts))
                chunk_texts = texts[i:end_idx]
                chunk_metadatas = metadatas[i:end_idx]
                chunk_ids = ids[i:end_idx]

                collection.add(
                    documents=chunk_texts,
                    metadatas=chunk_metadatas,
                    ids=chunk_ids
                )

                # Progress indicator
                if len(texts) > chroma_batch_size:
                    print(f"Added micro-batch: {len(chunk_texts)} docs")

            embed_time = time.time() - embed_start
            docs_per_sec = batch_doc_count / embed_time if embed_time > 0 else 0

            total_documents += batch_doc_count

            # Aggressive cleanup
            del documents, texts, metadatas, ids, batch_df
            gc.collect()

            batch_time = time.time() - batch_start_time
            memory_usage = get_memory_usage()

            print(f"   ✅ Batch completed in {batch_time:.2f}s")
            print(f"   📈 Embedding speed: {docs_per_sec:.1f} docs/sec")
            print(f"   💾 Memory: {memory_usage:.1f}MB")
            print(f"   📊 Total documents: {total_documents:,}")

        # Final statistics
        total_time = time.time() - start_time
        final_count = collection.count()

        print("\n" + "="*60)
        print("✅ CHROMADB BUILD COMPLETED!")
        print("="*60)
        print(f" Performance Summary:")
        print(f"   • Articles processed: {total_articles:,}")
        print(f"   • Documents created: {final_count:,}")
        print(f"   • Total time: {total_time/60:.2f} minutes")
        print(f"   • Speed: {final_count/total_time:.1f} docs/sec")
        print(f"   • Chunks per article: {final_count/total_articles:.1f}")
        print(f"   • Device: {'GPU' if use_gpu else 'CPU'}")
        print(f"   • Final memory: {get_memory_usage():.1f}MB")

        return collection, client

    except Exception as e:
        print(f"\n❌ Error in batch {batch_num}: {e}")
        raise e
