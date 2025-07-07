"""
Application Entry Point for Duplicate Detection POC

This is the main entry point for the duplicate detection proof of concept.
It orchestrates the workflow by calling functions from the other modules.
"""

from src.dublette.data.generation import generate_test_data
from src.dublette.database.connection import setup_duckdb, create_target_table
from src.dublette.detection.splink_config import configure_splink, detect_duplicates
from src.dublette.evaluation.metrics import evaluate_model, plot_match_probability_distribution

def main():
    """
    Main function to run the duplicate detection POC.
    """
    print("Generating test data...")
    df_company_a, df_company_b = generate_test_data()

    print(f"Company A data: {len(df_company_a)} records")
    print(f"Company B data: {len(df_company_b)} records")

    print("\nSetting up DuckDB...")
    con = setup_duckdb()

    print("\nConfiguring Splink...")
    linker = configure_splink(con)

    print("\nDetecting duplicates...")
    df_predictions = detect_duplicates(linker)

    print("\nCreating target table...")
    df_target = create_target_table(con, df_predictions)

    print(f"\nTarget table created with {len(df_target)} records")

    print("\nEvaluating model...")
    metrics = evaluate_model(df_predictions)

    print("\nModel evaluation metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\nPlotting match probability distribution...")
    plot_match_probability_distribution(df_predictions)

    print("\nSaving results...")
    df_predictions.to_csv('output/predictions.csv', index=False)
    df_target.to_csv('output/target_table.csv', index=False)

    print("\nDone!")

if __name__ == "__main__":
    main()
