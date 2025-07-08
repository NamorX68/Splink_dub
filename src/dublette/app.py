"""
Application Entry Point for Duplicate Detection POC

This is the main entry point for the duplicate detection proof of concept.
It orchestrates the workflow by calling functions from the other modules.
"""

import click
from dublette.data.generation import generate_test_data
from dublette.database.connection import setup_duckdb, create_target_table
from dublette.detection.splink_config import configure_splink, detect_duplicates
from dublette.evaluation.metrics import evaluate_model, plot_match_probability_distribution


@click.command()
@click.option(
    "--multi-table",
    is_flag=True,
    default=False,
    help="Use multi-table processing (link two tables). If False, uses single-table deduplication.",
)
@click.option(
    "--generate-test-data",
    "generate_data",
    is_flag=True,
    default=False,
    help="Generate new test data. If False, uses existing data from output directory.",
)
@click.option(
    "--table-name", default="company_data", help="Name of the table for single-table processing (default: company_data)"
)
def main(multi_table, generate_data, table_name):
    """
    Main function to run the duplicate detection POC.

    Args:
        multi_table (bool): If True, performs linking between two tables. If False, performs deduplication on single table.
        generate_data (bool): If True, generates new test data. If False, uses existing data.
        table_name (str): Name of the table for single-table processing.
    """
    click.echo("Starting Duplicate Detection POC...")
    click.echo(f"Mode: {'Multi-table linking' if multi_table else 'Single-table deduplication'}")
    click.echo(f"Generate test data: {generate_data}")

    if generate_data:
        click.echo("Generating test data...")
        df_company_a, df_company_b = generate_test_data(multi_table=multi_table)
        click.echo(f"Company A data: {len(df_company_a)} records")
        if multi_table:
            click.echo(f"Company B data: {len(df_company_b)} records")
        else:
            click.echo("Single-table mode: Company B data included in combined dataset")

    click.echo("\nSetting up DuckDB...")
    con = setup_duckdb(generate_test_data=generate_data, multi_table=multi_table)

    click.echo("\nConfiguring Splink...")
    linker = configure_splink(con, multi_table=multi_table, table_name=table_name)

    click.echo("\nDetecting duplicates...")
    df_predictions = detect_duplicates(linker)

    click.echo("\nCreating target table...")
    df_target = create_target_table(con, df_predictions)

    click.echo(f"\nTarget table created with {len(df_target)} records")

    click.echo("\nEvaluating model...")
    metrics = evaluate_model(df_predictions)

    click.echo("\nModel evaluation metrics:")
    for key, value in metrics.items():
        click.echo(f"  {key}: {value}")

    click.echo("\nPlotting match probability distribution...")
    plot_match_probability_distribution(df_predictions)

    click.echo("\nSaving results...")
    df_predictions.to_csv("output/predictions.csv", index=False)
    df_target.to_csv("output/target_table.csv", index=False)

    click.echo("\nDone!")


if __name__ == "__main__":
    main()
