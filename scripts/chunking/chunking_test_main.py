# test recursive_chunking.py
from scripts.chunking.recursive_chunking import build_chromadb_from_articles
from scripts.utils.get_memory_usage import get_memory_usage
from scripts.utils.get_gpu_info import get_gpu_info
import pandas as pd
import os
from scripts.dataset_loading.load_data import load_sample_data

def __main__():
    """Main function to run tests"""
    # Load sample data
    sample_type = 'tiny'
    sample_df = load_sample_data(sample_type=sample_type)

    # Run the build_chromadb_from_articles function
    embeddings = None  # Replace with actual embeddings if needed
    build_chromadb_from_articles(sample_df, embeddings, sample_type='tiny')

    # Check final memory usage
    final_memory = get_memory_usage()
    