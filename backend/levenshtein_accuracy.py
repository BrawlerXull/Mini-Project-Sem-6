# levenshtein_accuracy.py
import Levenshtein

def calculate_levenshtein_accuracy(predicted: str, actual: str) -> float:
    """
    Function to calculate the Levenshtein distance-based accuracy between predicted and actual strings.
    
    Args:
    - predicted (str): The predicted string.
    - actual (str): The actual target string.

    Returns:
    - float: The accuracy as a percentage.
    """
    # Compute the Levenshtein distance between the strings
    distance = Levenshtein.distance(predicted, actual)
    
    # Calculate the maximum length of the two strings
    max_length = max(len(predicted), len(actual))
    
    # Calculate accuracy as the percentage of similarity (1 - normalized distance)
    accuracy = ((max_length - distance) / max_length) * 100 if max_length > 0 else 0

    return accuracy
