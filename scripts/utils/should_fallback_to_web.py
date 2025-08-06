import os

def should_fallback_to_web(scores, threshold=0.78):
    """Fallback if majority of scores are weak"""
    if not scores:
        print("No scores available for fallback check")
        return True
    weak_count = sum(score > threshold for score in scores)
    return weak_count >= len(scores) * 0.8  # fallback if 80% or more scores are weak
