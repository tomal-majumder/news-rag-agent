import argparse
from app.scripts.dataset_loading.load_data import load_sample_data
from app.scripts.utils.get_embedding_function import get_embedding_function
from app.scripts.utils.get_embedding_model import get_embedding_model
from app.scripts.utils.build_chromadb_from_articles import build_chromadb_from_articles

from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_article_text(text: str, chunk_size=2500, overlap=600):
    """
    Spaces, punctuation, and newlines are counted toward chunk_size/overlap.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    return splitter.split_text(text)


def main():
    parser = argparse.ArgumentParser(description="Build ChromaDB from news articles")
    parser.add_argument('--sample_type', type=str, default='tiny', help="Sample size: tiny, small, medium, large")
    parser.add_argument('--splitter', type=str, default='recursive', choices=['recursive', 'semantic'], help="Chunking method")
    parser.add_argument('--batch_size', type=int, default=400, help="Batch size for ingestion")

    args = parser.parse_args()

    print(f"\n Running ChromaDB Build with:")
    print(f"Sample: {args.sample_type}")
    print(f"Splitter: {args.splitter}")
    print(f"Batch Size: {args.batch_size}")


    # Load data
    sample_df = load_sample_data(sample_type=args.sample_type)
    collection_name = "news_articles_" 
    # Load embedding function/model
    embeddings = get_embedding_function()
    embedding_function = get_embedding_model()

    # Build ChromaDB
    build_chromadb_from_articles(
        sample_df,
        embeddings,
        embedding_function,
        batch_size=args.batch_size,
        splitter=args.splitter,
        collection_name=collection_name,
        sample_type=args.sample_type
    )

if __name__ == "__main__":
    main()
