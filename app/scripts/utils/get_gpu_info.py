# ADD THESE IMPORTS AT THE TOP (minimal addition)
import torch

# ADD THIS SMALL FUNCTION (minimal addition)
def get_gpu_info():
    """Quick GPU check"""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"GPU Detected: {gpu_name}")
        return True
    else:
        print("Using CPU")
        return False