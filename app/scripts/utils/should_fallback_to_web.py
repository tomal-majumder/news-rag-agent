import os

def should_fallback_to_web(scores, threshold=0.4):
    """Fallback if majority of scores are weak"""    

    if not scores:
        print("No scores available for fallback check")
        return True
    weak_count = sum(score > threshold for score in scores)
    return weak_count >= len(scores) * 0.55  # fallback if 55% or more scores are weak
