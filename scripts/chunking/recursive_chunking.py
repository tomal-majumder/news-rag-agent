import gc
import time
from scripts.utils.get_memory_usage import get_memory_usage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from scripts.utils.get_gpu_info import get_gpu_info
from scripts.utils.get_memory_usage import get_memory_usage
import torch
from scripts.utils.create_chromadb_collection import create_chromadb_collection
from scripts.utils.create_documents_batch import create_documents_batch
from scripts.utils.build_chromadb_from_articles import build_chromadb_from_articles
from scripts.dataset_loading.load_data import load_sample_data
from scripts.utils.get_embedding_function import get_embedding_function
from scripts.utils.get_embedding_model import get_embedding_model

# call build_chromadb_from_articles with the correct parameters for recursive_chunking
def main():
    # Load sample data
    sample_type = 'tiny'
    sample_df = load_sample_data(sample_type=sample_type)
    # Define embeddings and embedding function (replace with actual implementations)
    embeddings = get_embedding_function()  # Replace with actual embeddings if needed
    embedding_function = get_embedding_model()  # Replace with actual embedding function if needed

    # Run the build_chromadb_from_articles function
    build_chromadb_from_articles(sample_df, embeddings, embedding_function, sample_type=sample_type)