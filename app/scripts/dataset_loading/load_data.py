import pandas as pd
import os
def load_sample_data(sample_type='tiny'):
    """
    Load sample data for testing purposes.
    
    Args:
        sample_type (str): Type of sample to load ('tiny', 'small', 'medium', 'large').
    
    Returns:
        pd.DataFrame: Loaded sample data as a DataFrame.
    """
    print(f"Loading {sample_type} sample data...")

    # Define the path to the sample data
    sample_path = os.path.join('data', 'samples', f'{sample_type}_sample.parquet')

    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"Sample file not found: {sample_path}")

    # Load the sample data
    df = pd.read_parquet(sample_path)
    
    print(f"Loaded {len(df)} rows from {sample_type} sample")
    
    return df