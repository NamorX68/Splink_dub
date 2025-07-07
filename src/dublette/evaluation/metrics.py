"""
Evaluation Module for Duplicate Detection POC

This module provides functions for evaluating the duplicate detection model and visualizing results.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import os

def evaluate_model(df_predictions, threshold=0.8):
    """
    Evaluate the model accuracy.

    Args:
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        dict: Dictionary with evaluation metrics
    """
    # For a real evaluation, we would need ground truth data
    # Here we'll just provide some basic statistics

    # Count predictions above threshold
    matches = df_predictions[df_predictions['match_probability'] >= threshold]
    non_matches = df_predictions[df_predictions['match_probability'] < threshold]

    # Calculate metrics
    metrics = {
        'total_comparisons': len(df_predictions),
        'predicted_matches': len(matches),
        'predicted_non_matches': len(non_matches),
        'match_rate': len(matches) / len(df_predictions) if len(df_predictions) > 0 else 0,
        'threshold': threshold
    }

    return metrics

def plot_match_probability_distribution(df_predictions):
    """
    Plot the distribution of match probabilities.

    Args:
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(df_predictions['match_probability'], bins=50, kde=True)
    plt.title('Distribution of Match Probabilities')
    plt.xlabel('Match Probability')
    plt.ylabel('Count')
    plt.axvline(x=0.8, color='r', linestyle='--', label='Threshold (0.8)')
    plt.legend()
    # Get the project root directory (3 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, 'output')
    plot_path = os.path.join(output_dir, 'match_probability_distribution.png')

    plt.savefig(plot_path)
    plt.close()
