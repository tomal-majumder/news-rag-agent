def get_device():
    """Detect and return the best available device for model inference."""
    try:
        import torch
        if torch.cuda.is_available():
            return 'cuda'
        else:
            return 'cpu'
    except ImportError:
        print("PyTorch is not installed. Defaulting to CPU.")
        return 'cpu'